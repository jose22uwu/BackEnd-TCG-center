from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

from config import getArtifactsDir
from db import findCardIdByName, loadCardsByIds, loadUserById, loadUserCollection
from rule_engine import (
    TCG_CORE_RULES,
    CollectionSummary,
    buildStrategicAdvice,
    evaluateScenario,
    getRulesRelevantToQuestion,
    summarizeCollection,
)


def _tokenize(text: str) -> set[str]:
    return {token.strip(" ,.!?;:()[]{}").lower() for token in text.split() if token.strip()}


def _cardSearchScore(questionTokens: set[str], card: dict[str, Any]) -> float:
    name = str(card.get("name") or "").lower()
    rarity = str(card.get("rarity") or "").lower()
    category = str(card.get("category") or "").lower()
    text = f"{name} {rarity} {category}"
    score = 0.0
    for token in questionTokens:
        if token and token in text:
            score += 1.0
    return score


def _loadEmbeddingIndex() -> tuple[np.ndarray, np.ndarray] | None:
    indexPath = getArtifactsDir() / "card_embedding_index.npz"
    if not indexPath.exists():
        return None
    data = np.load(indexPath)
    return data["cardIds"], data["embeddings"]


def _getSimilarCardIds(
    cardId: int,
    excludeIds: set[int],
    topK: int = 10,
) -> list[tuple[int, float]]:
    indexData = _loadEmbeddingIndex()
    if indexData is None:
        return []
    cardIds, embeddings = indexData
    cardIds = np.asarray(cardIds)
    embeddings = np.asarray(embeddings, dtype=np.float32)
    if embeddings.ndim != 2 or cardIds.shape[0] != embeddings.shape[0]:
        return []
    idx = np.where(cardIds == cardId)[0]
    if len(idx) == 0:
        return []
    vec = embeddings[idx[0]]
    scores = np.dot(embeddings, vec)
    order = np.argsort(-scores)
    out: list[tuple[int, float]] = []
    for i in order:
        cid = int(cardIds[i])
        if cid == cardId or cid in excludeIds:
            continue
        out.append((cid, float(scores[i])))
        if len(out) >= topK:
            break
    return out


def _getCatalogRecommendationIds(
    userCardIds: list[int],
    quantities: list[int],
    topK: int = 10,
) -> list[tuple[int, float]]:
    indexData = _loadEmbeddingIndex()
    if indexData is None or not userCardIds:
        return []
    cardIds, embeddings = indexData
    cardIds = np.asarray(cardIds)
    embeddings = np.asarray(embeddings, dtype=np.float32)
    if embeddings.ndim != 2 or cardIds.shape[0] != embeddings.shape[0]:
        return []
    excludeSet = set(userCardIds)
    pairs = [(cid, quantities[i] if i < len(quantities) else 1) for i, cid in enumerate(userCardIds) if np.any(cardIds == cid)]
    if not pairs:
        return []
    indices = [np.where(cardIds == cid)[0][0] for cid, _ in pairs]
    weights = [q for _, q in pairs]
    vec = np.average(embeddings[indices], axis=0, weights=weights)
    norm = np.linalg.norm(vec)
    if norm > 1e-9:
        vec = vec / norm
    scores = np.dot(embeddings, vec)
    order = np.argsort(-scores)
    out: list[tuple[int, float]] = []
    for i in order:
        cid = int(cardIds[i])
        if cid in excludeSet:
            continue
        out.append((cid, float(scores[i])))
        if len(out) >= topK:
            break
    return out


def _normalizeExtractedCardName(segment: str) -> str:
    """Quita colas de cortesia y recorta al nombre de carta (conserva V, VMAX, VSTAR, GX, ex)."""
    segment = segment.strip()
    for tail in (" por favor", " gracias", " please", " pls", " gracias.", " por favor."):
        low = segment.lower()
        if low.endswith(tail):
            segment = segment[: -len(tail)].strip()
        elif tail in low:
            segment = segment[: low.find(tail)].strip()
    if len(segment) > 80:
        segment = segment[:80].strip()
    lower = segment.lower()
    for suffix in (" vmax", " vstar", " gx", " ex"):
        if suffix in lower:
            end = lower.rfind(suffix) + len(suffix)
            segment = segment[:end].strip()
            break
    if " v " in lower and " vmax" not in lower and " vstar" not in lower:
        end = lower.rfind(" v ") + len(" v ")
        segment = segment[:end].strip()
    return segment.strip()


def _extractCardNameForSimilar(question: str) -> str | None:
    q = question.strip()
    if not q:
        return None
    lower = q.lower()
    prefixes = [
        "dime una carta similar a ", "dame una carta similar a ", "carta similar a ", "similar a ",
        "similares a ", "parecidas a ", "parecidos a ", "parecido a ", "como ", "combinan con ",
        "recomienda como ", "recomienda cartas como ", "cartas como ", "sustitutas de ", "sustitutos de ",
        "alternativas a ", "reemplazo de ", "en lugar de ", "algo como ", "cartas tipo ",
        "recomiendame como ", "recomiendame cartas como ", "sustituto de ", "sustituta de ",
        "reemplazos de ", "al estilo de ", "cartas que reemplacen a ", "equivalente a ", "equivalentes a ",
        "otras cartas como ", "mas cartas como ", "variantes de ", "opciones como ", "alternativas para ",
    ]
    for prefix in prefixes:
        if prefix in lower:
            start = lower.index(prefix) + len(prefix)
            segment = q[start:].strip()
            if segment:
                segment = segment[:80].strip() if len(segment) > 80 else segment
                return _normalizeExtractedCardName(segment)
    return None


def _findCardForSimilarIntent(cardName: str | None, userCards: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not cardName:
        return None
    nameLower = cardName.lower()
    for c in userCards:
        if nameLower in (str(c.get("name") or "").lower()):
            return c
    cardId = findCardIdByName(cardName)
    if cardId is None:
        return None
    cards = loadCardsByIds([cardId])
    return cards[0] if cards else None


def _findRelevantCards(
    question: str, userCards: list[dict[str, Any]], topK: int = 5
) -> tuple[list[dict[str, Any]], bool]:
    """Devuelve (cartas relevantes, True si hubo coincidencia con la pregunta, False si es fallback)."""
    tokens = _tokenize(question)
    scored = []
    for card in userCards:
        score = _cardSearchScore(tokens, card)
        scored.append((score, int(card.get("quantity") or 0), card))
    scored.sort(key=lambda row: (row[0], row[1]), reverse=True)

    selected = [entry[2] for entry in scored if entry[0] > 0][:topK]
    if selected:
        return (selected, True)

    fallback = sorted(userCards, key=lambda c: int(c.get("quantity") or 0), reverse=True)
    return (fallback[:topK], False)


def _intentFromQuestion(question: str) -> str:
    questionLower = question.lower()
    # Escenarios: variantes de "que pasa si", situaciones de partida, mulligan, premios, turno, etc.
    if any(term in questionLower for term in [
        "escenario", "que pasa si", "que pasaria", "que pasaria si", "y si ", "si pasa", "simular",
        "en el caso de que", "cuando ", "puedo jugar dos", "dos supporters", "dos energias", "dos energia ",
        "sin pokemon basico", "sin basico", "mulligan", "deck vacio", "mazo vacio", "no puedo robar",
        "robo inicial", "cuantas cartas robo", "premios", "tomo premios", "ko a vmax", "pierdo si ",
        "puedo poner ", "puedo usar ", "puedo jugar ", "puedo atacar ", "ataque dos veces", "dos ataques",
        "cuantas energias", "cuantos supporters", "retirar", "me rindo", "conceder", "empate",
        "ganar", "perder", "robar de mas", "descarte", "descartar", "evolucionar", "turno 1", "primer turno",
        "banca llena", "sustituir pokemon", "retirar pokemon", "carta anulada", "anular",
        "resistencia", "debilidad", "habilidad", "item", "tool", "stadium", "estadio",
        "energia basica", "energia especial", "unir energia", "attach", "robar carta",
        "buscar en el mazo", "jugador inicial", "quien empieza", "orden del turno",
        "copias en el mazo", "4 copias", "limite de copias", "carta ilegal", "deck invalido",
        "cambio de pokemon", "retreat", "retirada", "costo de retirada", "benched", "activo ",
        "que hago si", "que hacer si", "como reacciono si", "supongamos que", "imaginemos que",
        "dos items", "tres energias", "segundo supporter", "otro supporter", "robo 7", "mano inicial",
        "no tengo basico", "tengo 6 premios", "tome todos los premios", "derrotar vmax", "ko vstar",
        "paralisis", "dormido", "quemado", "envenenado", "confusion", "estado especial",
        "carta bloqueada", "habilidad anulada", "no puedo atacar", "no puedo retirar", "banca completa",
    ]):
        return "scenario"
    # Similares a una carta: sustitutas, alternativas, tipo de carta (V, VMAX, etc.).
    if any(term in questionLower for term in [
        "carta similar a ", "similar a ", "similares a ", "parecidas a ", "parecidos a ", "combinan con ",
        "recomienda como ", "cartas como ", "sustitutas de ", "sustitutos de ", "alternativas a ",
        "alternativas para ", "reemplazo de ", "en lugar de ", "parecido a ", "algo como ", "cartas tipo ",
        "recomiendame como ", "recomiendame cartas como ", "sustituto de ", "sustituta de ", "reemplazos de ",
        "al estilo de ", "cartas que reemplacen", "equivalente a ", "equivalentes a ",
        "otras cartas como", "mas cartas como", "variantes de ", "opciones como ",
    ]):
        return "similar_to_card"
    # Catalogo: que comprar, que me falta, complementar coleccion.
    if any(term in questionLower for term in [
        "catalogo", "catálogo", "encajen con mi coleccion", "complementen", "cartas me faltan",
        "recomienda del catalogo", "del catalogo", "que comprar", "que deberia comprar", "comprar ",
        "añadir a mi", "agregar a mi", "sumar a mi", "que me faltan", "sugiere del catalogo",
        "recomendaciones de compra", "para completar", "encajan con mi", "que cartas añadir",
        "que cartas agregar", "que deberia añadir", "cartas que encajen", "completar mi mazo",
        "que expansion comprar", "que set comprar", "donde comprar cartas", "que me recomiendas comprar",
        "sugerencias de compra", "invertir en", "proximas cartas", "siguientes cartas a conseguir",
    ]):
        return "catalog_recommend"
    # Conclusion / resumen generado.
    if any(term in questionLower for term in [
        "conclusion", "conclusiones", "resumen", "resumir", "resume mi mazo", "dame una conclusion",
        "que conclusion sacas", "resume mi coleccion", "resumeme", "dame un resumen", "analiza mi mazo",
        "valoracion de mi", "diagnostico de mi mazo", "que conclusiones", "sintetiza mi coleccion",
        "analiza mi coleccion", "valora mi mazo", "diagnostico mi deck", "resumen de mi mazo",
        "que opinas de mi mazo", "opinion sobre mi coleccion", "valorar mi deck", "analisis de mi coleccion",
        "dame tu opinion", "que te parece mi mazo", "revisa mi mazo", "revisa mi coleccion",
    ]):
        return "generate_conclusion"
    # Reglas y mecanicas basicas: ganar, mazo, basico, premios, activo/banca, evolucionar, entrenador, supporters.
    if any(term in questionLower for term in [
        "regla", "reglas", "legal", "turno", "premio", "mulligan", "como se juega", "normas del juego",
        "limites ", "cuantas cartas ", "60 cartas", "supporter por turno", "ataque por turno",
        "banca ", "maximo 5", "robo inicial", "estructura del mazo", "deck legal",
        "como se gana", "ganar partida", "cuantas cartas debe", "pokemon basico", "que es un basico",
        "cuantas energias puedo", "que pasa si no tengo pokemon inicial", "como funcionan las cartas de premio",
        "diferencia entre activo y banca", "cuando puedo evolucionar", "cartas de entrenador", "cuantos supporters",
        "normas ", "reglamento", "como funciona el turno", "fases del turno", "estructura de partida",
        "cuantas energias unir", "cuantos ataques", "cuantos items", "limite de supporters",
        "que es premio", "como funcionan premios", "cuando tomo premios", "cartas de premio",
        "inicio de partida", "como empieza", "quien va primero", "orden de juego", "setup inicial",
        "cuantas copias maximo", "limite 4 copias", "deck invalido", "mazo ilegal", "formato standard",
    ]):
        return "rules"
    # Combate y efectos: daño, KO, confundido, envenenamiento, debilidad, retirada, primer turno, moneda.
    if any(term in questionLower for term in [
        "calcula el daño", "daño de un ataque", "danio", "cuando queda ko", "k.o", "estado confundido",
        "envenenamiento", "debilidad y resistencia", "coste de retirada", "atacar en el primer turno",
        "atacar sin energia", "efectos adicionales", "lanzar moneda", "cara o cruz",
        "calcular daño", "como se calcula el daño", "daño total", "aplicar debilidad",
        "ko", "derribar", "derrotar pokemon", "cuando va al descarte", "moneda en ataque",
        "efecto de ataque", "texto del ataque", "condiciones de victoria", "como gano",
    ]):
        return "scenario"
    # Estrategia y construccion: armar mazo, proporcion, meta, agresivo, control, contrarrestar, esenciales, brickear.
    if any(term in questionLower for term in [
        "recomienda", "recomendacion", "recomendaciones", "mejorar", "estrategia", "consejos",
        "tips ", "como mejorar", "optimizar mi mazo", "armar mazo", "construir deck", "que cambiar",
        "ajustar mi mazo", "mejoras para mi", "sugerencias para mi deck",
        "mazo competitivo", "proporcion ideal", "carta meta", "mazo agresivo", "deck control",
        "contrarrestar", "esenciales", "consistencia", "brickear", "elegir pokemon principal",
        "mejor jugada", "simula partida", "deck contra meta", "evalua este mazo", "mejoras con bajo presupuesto",
        "que poner en el mazo", "que incluir en el deck", "cuantas energias poner", "cuantos pokemon",
        "como armar un deck", "construccion de mazo", "mejorar mi deck", "optimizar deck",
        "consejos para mi mazo", "que quitar del mazo", "que añadir al mazo", "cambios en mi mazo",
        "deck viable", "mazo jugable", "arquetipo", "tipo de mazo", "estrategia agresiva",
        "mejor deck con lo que tengo", "armar deck con mi coleccion", "sacar partido a mi coleccion",
    ]):
        return "strategy"
    # Busqueda semantica / catalogo: cartas que, pokemon que, mejor relacion, sinergia, counter, curacion.
    if any(term in questionLower for term in [
        "cartas que", "pokemon que", "dame cartas", "que cartas tienen", "mejor relacion dano energia",
        "sinergia", "acelerar energias", "counter", "efectos similares", "curacion", "clasificar por utilidad",
        "robar mas", "atacar primer turno", "curar", "multiples pokemon", "habilidades pasivas",
        "descartar energias", "bajo coste", "cambiar pokemon", "sinergia electrico", "tipo electrico",
        "cartas de robo", "cartas de busqueda", "aceleracion", "draw", "search", "fetch",
        "mejor relacion costo daño", "ataques baratos", "pokemon de apoyo", "support pokemon",
        "curar pokemon", "quitar daño", "recuperar hp", "cartas de curacion", "heal",
    ]):
        return "catalog_recommend"
    # Coleccion: que tengo, inventario, cuantas cartas.
    if any(term in questionLower for term in [
        "coleccion", "tengo", "mis cartas", "que tengo", "mi inventario", "cuantas cartas tengo",
        "contenido de mi coleccion", "que hay en mi", "listado de mi", "resumen de mi coleccion",
        "listar mi coleccion", "ver mi coleccion", "mostrar mis cartas", "que cartas tengo",
        "inventario de cartas", "mi lista de cartas", "cuantas tengo", "conteo de mi coleccion",
    ]):
        return "collection"
    return "general"


def _questionMatchesAnyIntent(question: str) -> bool:
    """True if the question contains at least one keyword from any intent."""
    lower = question.lower()
    keywords = [
        "escenario", "que pasa si", "que pasaria", "si pasa", "simular", "y si ", "dos supporters", "dos energias", "mulligan", "deck vacio", "premios", "robo inicial",
        "puedo poner", "puedo usar", "retirar", "empate", "evolucionar", "turno 1", "banca llena", "resistencia", "debilidad", "tool", "stadium", "robar carta", "4 copias",
        "daño", "danio", "ko", "confundido", "envenenamiento", "coste retirada", "primer turno atacar", "moneda",
        "que hago si", "que hacer si", "paralisis", "dormido", "quemado", "envenenado", "robo 7", "mano inicial",
        "carta similar a", "similar a", "similares a", "parecidas a", "combinan con", "recomienda como", "cartas como", "sustitutas", "sustituto de", "alternativas a", "reemplazo de", "en lugar de", "cartas tipo ",
        "recomiendame como", "equivalente a", "variantes de", "opciones como",
        "catalogo", "catálogo", "encajen", "complementen", "cartas me faltan", "del catalogo", "que comprar", "comprar", "añadir a mi", "que me faltan",
        "que expansion comprar", "que set comprar", "completar mi mazo", "encajan con mi",
        "cartas que", "pokemon que", "mejor relacion", "sinergia", "counter", "curacion", "esenciales", "brickear",
        "conclusion", "conclusiones", "resumen", "resumir", "resume mi mazo", "resume mi coleccion", "resumeme", "analiza mi mazo", "valoracion", "diagnostico",
        "analiza mi coleccion", "valora mi mazo", "que opinas", "revisa mi mazo", "revisa mi coleccion",
        "regla", "reglas", "legal", "turno", "premio", "mulligan", "como se juega", "normas", "60 cartas", "supporter", "banca", "deck legal",
        "ganar partida", "pokemon basico", "activo", "entrenador", "evolucionar", "reglamento", "fases del turno",
        "cuantas energias unir", "cuantos supporters", "inicio de partida", "quien va primero", "formato standard",
        "recomienda", "recomendacion", "mejorar", "estrategia", "consejos", "tips", "optimizar", "armar mazo", "construir deck", "competitivo", "meta", "control",
        "que poner en el mazo", "que incluir", "cuantas energias poner", "como armar", "mejorar mi deck", "arquetipo",
        "coleccion", "tengo", "mis cartas", "inventario", "cuantas cartas tengo", "que tengo", "evalua mazo", "mejoras presupuesto",
        "listar mi coleccion", "ver mi coleccion", "mostrar mis cartas", "listado de mi",
    ]
    return any(kw in lower for kw in keywords)


def _isHelpRequest(question: str) -> bool:
    q = question.strip().lower()
    exact = {
        "?", "¿", "help", "ayuda", "que puedes hacer", "qué puedes hacer",
        "que sabes hacer", "qué sabes hacer", "como te uso", "cómo te uso",
        "instrucciones", "ejemplos", "que preguntas puedo hacer", "qué preguntas puedo hacer",
        "ayuda por favor", "help me", "socorro", "no se que preguntar", "no sé qué preguntar",
        "dime opciones", "que preguntas aceptas", "qué preguntas aceptas", "lista de comandos",
        "que comandos", "qué comandos", "como empezar", "cómo empezar", "por donde empiezo",
        "por dónde empiezo", "que puedo preguntar", "qué puedo preguntar", "opciones", "menu", "menú",
        "como funciona esto", "cómo funciona esto", "que hace el asistente", "qué hace el asistente",
    }
    if q in exact:
        return True
    if q.rstrip(".!?¿¡") in exact:
        return True
    if q.startswith("ayuda ") or q.startswith("help "):
        return True
    return False


def _normalizeForSocial(q: str) -> str:
    return " ".join(q.strip().lower().split())


def _isGreetingOnly(question: str) -> bool:
    """True if the question is only a greeting (no TCG intent)."""
    q = _normalizeForSocial(question)
    if not q:
        return False
    # Exact or near-exact greetings (with optional punctuation)
    exact = q.rstrip(".!?¿¡,")
    greeting_exact = {
        "hola", "holaa", "holaaa", "buenos dias", "buenos días", "buenas tardes", "buenas noches",
        "buenas", "buen dia", "buen día", "hey", "hi", "hello", "qué tal", "que tal", "quetal",
        "holi", "saludos", "qué hay", "que hay", "como estas", "cómo estás", "ey", "oye", "ola",
        "good morning", "good afternoon", "good evening", "wena", "ql tal", "ke tal", "k tal",
    }
    if exact in greeting_exact:
        return True
    tokens = _tokenize(question)
    greeting_words = {
        "hola", "holi", "hey", "hi", "hello", "buenos", "buenas", "dias", "día", "días", "dia",
        "tardes", "noches", "tal", "qué", "que", "saludos", "hay", "como", "cómo", "estas", "estás",
        "ey", "oye", "ola", "buen",
    }
    if len(tokens) <= 4 and tokens and all(t in greeting_words for t in tokens):
        return True
    return False


def _isMetaQuestion(question: str) -> bool:
    """True if the user is asking what the assistant is / what it's for (no TCG content)."""
    lower = question.strip().lower()
    phrases = [
        "para qué sirves", "para que sirves", "para que sirve", "para qué sirve",
        "qué eres", "que eres", "quién eres", "quien eres", "qué haces", "que haces",
        "para qué te uso", "para que te uso", "qué hago contigo", "que hago contigo",
        "dime qué eres", "cuéntame qué eres", "cuentame que eres", "qué tipo de asistente",
        "que tipo de asistente", "eres un bot", "eres una ia", "eres una inteligencia",
        "que puedes hacer por mi", "qué puedes hacer por mí", "qué puedes hacer por mi",
        "en qué me ayudas", "en que me ayudas", "como me ayudas", "cómo me ayudas",
        "para qué estás", "para que estas", "qué asistente eres", "que asistente eres",
        "que hace este chat", "qué hace este chat", "para que es este bot", "para qué es este bot",
        "funcion de este asistente", "función de este asistente", "que es esto", "qué es esto",
        "como funciona el asistente", "cómo funciona el asistente", "que es este chat",
        "explicame para que sirve", "explícame para qué sirves",
    ]
    return any(p in lower for p in phrases)


def _getSocialResponse(question: str, isGreeting: bool) -> str:
    """Friendly reply for greetings or meta questions (analysis layer only)."""
    if isGreeting:
        return (
            "Hola. Soy el asistente de Pokemon TCG de esta app: te ayudo con reglas, escenarios de partida, "
            "recomendaciones sobre tu mazo y cartas que encajan con tu coleccion. Escribe ? o ayuda para ver "
            "todo lo que puedes preguntar."
        )
    return (
        "Soy un asistente centrado en Pokemon TCG. Sirvo para explicarte reglas del juego, resolver dudas de partida "
        "(por ejemplo que pasa si haces mulligan o juegas dos supporters), darte recomendaciones segun las cartas "
        "que tienes en tu coleccion, sugerirte cartas similares a una que nombres y recomendar cartas del catalogo "
        "que encajen con lo que ya tienes. Escribe ? o ayuda para ver ejemplos de preguntas."
    )


def _getHelpMessage() -> str:
    return """Este asistente usa tu coleccion de cartas Pokemon TCG para darte respuestas personalizadas. Puede:

- Explicar reglas del juego (turno, premios, mulligan, deck de 60 cartas, etc.).
- Resolver escenarios (que pasa si no tienes basico, si juegas dos supporters, etc.).
- Dar recomendaciones estrategicas segun las cartas que tienes.
- Sugerir cartas similares a una que nombres (usa embeddings: similitud semantica).
- Recomendar cartas del catalogo que encajan con tu coleccion (usa embeddings: perfil de tu coleccion).
- Generar una conclusion o resumen sobre tu mazo o coleccion.

Preguntas de ejemplo para probar:

Sin embeddings (siempre disponibles):
• Dame una conclusion sobre mi mazo
• Resumen mi coleccion
• Cuales son las reglas clave del turno y los premios?
• Que pasa si no tengo Pokemon basico y hago mulligan?
• Dame recomendaciones para mejorar mi mazo

Con embeddings (requieren indice de cartas generado):

Similares a una carta (similitud semantica):
• Recomienda cartas similares a Lapras V
• Dame alternativas a Celebi V
• Dime una carta similar a Pikachu V
• Sustitutas de Mewtwo ex
• Cartas como Lapras V

Catalogo que encaja con tu coleccion (perfil de embeddings):
• Que cartas del catalogo encajan con mi coleccion?
• Que me recomiendas comprar para completar mi mazo?
• Sugiere cartas que pueda añadir a mi coleccion
• Que cartas me faltan que encajen con lo que tengo?"""


# FAQ interno: preguntas frecuentes que el modelo puede contestar por coincidencia de palabras (sin APIs).
_FAQ_ENTRIES: list[tuple[list[str], str]] = [
    # Reglas basicas
    (["gana", "partida", "ganar", "como se gana"], "Ganas si tomas tus 6 premios, o el rival se queda sin Pokemon en campo, o no puede robar al inicio de su turno."),
    (["cuantas", "cartas", "mazo", "deck", "60", "debe tener"], "El mazo debe tener exactamente 60 cartas para ser legal."),
    (["pokemon", "basico", "que es", "que es un"], "Pokemon Basico es el que se juega desde la mano sin evolucionar. Necesitas al menos uno en la mano inicial para no hacer mulligan."),
    (["cuantas", "energias", "unir", "turno", "puedo"], "Solo puedes unir 1 energia de mano a un Pokemon por turno (salvo efectos de cartas)."),
    (["pokemon", "inicial", "no tengo", "que pasa"], "Si no tienes Pokemon basico en mano inicial, declaras mulligan: barajas, robas 7 de nuevo; el rival roba 1 carta extra. Repites hasta tener al menos un basico."),
    (["premio", "premios", "funcionan", "cartas"], "Pones 6 cartas boca abajo como premios. Por cada KO al rival tomas 1, 2 o 3 segun el tipo (normal 1, EX/V 2, VMAX/VSTAR 3). Quien tome sus 6 gana."),
    (["activo", "banca", "diferencia", "entre"], "El activo es el Pokemon en el centro que ataca y recibe ataques. La banca son hasta 5 Pokemon de respaldo; solo el activo participa en combate."),
    (["evolucionar", "cuando", "puedo"], "Puedes evolucionar en tu turno poniendo la carta de evolucion encima del Pokemon base o Etapa 1 correspondiente. Normalmente una evolucion por turno."),
    (["entrenador", "cartas", "que son"], "Entrenador: Items (ilimitados por turno), Supporters (1 por turno), Stadiums (1 en juego entre ambos). Tienen efectos segun el texto."),
    (["supporter", "cuantos", "turno", "usar"], "Solo 1 Supporter por turno."),
    (["cuatro", "4", "copias", "carta", "limite"], "Puedes llevar maximo 4 copias de la misma carta por nombre, excepto energias basicas."),
    (["turno", "energia", "una", "por"], "Solo puedes unir 1 energia de mano a un Pokemon por turno (salvo efectos de cartas)."),
    (["ataque", "veces", "turno"], "Solo 1 ataque por turno."),
    (["banca", "cuantos", "pokemon", "maximo", "5"], "Maximo 5 Pokemon en la banca."),
    (["pierdo", "pierdes", "cuando", "deck", "vacio"], "Si al inicio de tu turno no puedes robar porque el mazo esta vacio, pierdes."),
    (["mulligan", "robar", "7", "basico"], "Si no tienes Pokemon basico, muestras la mano, barajas y robas 7; el rival roba 1 carta por cada mulligan."),
    (["primero", "empieza", "atacar", "turno"], "Quien empieza no puede atacar ni usar Entrenador en su primer turno."),
    (["retreat", "retirada", "cambiar", "activo", "coste", "costo"], "Retirar al activo cuesta el numero de energias indicado en su esquina (se descartan). Pones otro de la banca como activo."),
    (["formato", "legal", "expansion"], "Cada formato (Standard, Expanded, etc.) tiene una lista de sets legales; las cartas de sets rotados no se pueden usar."),
    (["energia", "basica", "especial", "diferencia"], "Energia basica se une desde la mano (1 por turno salvo efectos). La especial se juega segun el texto de la carta."),
    (["tool", "herramienta", "pokemon"], "Cada Pokemon puede tener 1 Tool unida; si juegas otra, la anterior se descarta."),
    (["stadium", "estadio", "uno"], "Solo puede haber 1 Stadium en juego entre ambos; un nuevo Stadium reemplaza al anterior."),
    # Combate y efectos
    (["calcula", "daño", "ataque", "danio", "damage"], "El daño es el numero base del ataque; se aplica debilidad (x2) y resistencia (-20/-30); si daño >= HP del rival, queda K.O."),
    (["queda", "ko", "k.o", "cuando"], "Cuando un Pokemon recibe daño >= su HP, queda K.O.: va al descarte y el rival toma premios (1, 2 o 3 segun tipo)."),
    (["confundido", "confusion", "hace", "estado"], "Confundido: al atacar, lanzas moneda. Cruz = ataque falla y 30 de daño a si mismo. Cara = ataque normal."),
    (["envenenamiento", "envenenado", "poison", "funciona"], "Envenenado: entre turnos recibe daño (ej. 10 o 20 por contador). Los contadores los pone el ataque o efecto."),
    (["debilidad", "resistencia", "significa"], "Debilidad multiplica el daño (suele x2). Resistencia resta (ej. -20 o -30). Se aplican al calcular el daño final."),
    (["coste", "retirada", "retreat", "afecta"], "El coste de retirada son las energias que debes descartar del Pokemon para retirarlo a la banca. Sin pagar no puedes retirar."),
    (["atacar", "primer", "turno", "puedo"], "El jugador que empieza no puede atacar ni usar Entrenador en su primer turno. El segundo jugador si puede."),
    (["atacar", "sin", "energia", "se puede"], "Los ataques tienen coste en energias unidas al Pokemon. Sin las energias necesarias no puedes usar ese ataque. Hay cartas con ataque 0 coste."),
    (["efectos", "adicionales", "ataque", "que pasa"], "Los efectos del ataque (robar, paralisis, etc.) se resuelven segun el texto de la carta, normalmente despues del daño."),
    (["moneda", "lanzar", "ataque", "requieren"], "Algunos ataques piden lanzar moneda(s). Cara = efecto o daño extra; Cruz = fallo. El numero de caras lo indica la carta."),
    # Estrategia y mazos
    (["armar", "mazo", "competitivo", "desde cero"], "Mazo competitivo: 60 cartas, 15-20 Pokemon (varios basicos), 30-35 Entrenadores (robo, busqueda, draw), 10-14 energias. Ajusta segun el arquetipo."),
    (["proporcion", "ideal", "energias", "deck"], "Suele recomendarse 10-14 energias en un mazo de 60 para consistencia. Los mazos que aceleran mucho pueden bajar a 8-10."),
    (["meta", "carta", "que hace"], "Una carta 'meta' es la que domina el formato actual: alta eficiencia, sinergia con el resto del mazo y buena contra los decks mas jugados."),
    (["mazo", "agresivo", "construir"], "Mazo agresivo: muchos Pokemon basicos, ataques de bajo coste, Items de busqueda y robo para tener recursos rapidos y presionar desde el turno 1."),
    (["deck", "control", "que es"], "Deck control intenta dominar el ritmo con cartas que cancelen ataques, descarten mano rival, o controlen el tablero. Suele ser mas lento y reactivo."),
    (["contrarrestar", "agua", "mazos", "tipo"], "Contra mazos Agua: Pokemon y energias de tipo Planta o Electrico si el formato lo permite; cartas que anulen debilidad o reduzcan daño."),
    (["esenciales", "cartas", "todos", "decks"], "En casi todos los decks suelen ir: cartas de robo (Profesor, Cynthia), busqueda (Ultra Ball, Quick Ball), y energias base. El resto depende del arquetipo."),
    (["consistencia", "optimizar", "mazo"], "Consistencia: mas cartas de robo y busqueda (Supporters, Items), suficientes basicos para no mulliganear, y curva de energias que permita jugar desde turno 1."),
    (["brickear", "brick", "significa"], "Brickear es quedarte sin jugadas utiles: mano mala, pocas cartas jugables. Se reduce con mas robo, busqueda y menos cartas de alto coste."),
    (["elegir", "pokemon", "principal", "deck"], "Elige un Pokemon principal que sea el nucleo del mazo: buen ataque, sinergia con tus Trainers y energias, y que puedas poner en juego de forma fiable."),
    # Analisis tipo AI
    (["mejor", "relacion", "daño", "energia", "carta"], "La mejor relacion daño/energia depende del formato. Revisa tu coleccion y las cartas recomendadas; prioriza ataques que hagan mucho daño con 1-2 energias."),
    (["hp", "promedio", "pokemon", "set"], "El HP promedio varia por set y rareza. Las cartas V/VMAX suelen tener mas HP. Puedes filtrar en el catalogo por set para comparar."),
    (["sinergia", "combinaciones", "cartas"], "La sinergia surge cuando las cartas se potencian entre si: aceleradores de energia + atacantes caros, robo + cartas que descarten, etc. Revisa recomendaciones del catalogo segun tu coleccion."),
    (["acelerar", "energias", "rapido", "cartas"], "Cartas que aceleran energia: aquellas que unen energias desde el mazo o la mano a tus Pokemon (habilidades, Items, Supporters). Busca en el catalogo por efectos de 'attach' o 'energia'."),
    (["counter", "fuego", "mazo", "mejor"], "Contra mazos Fuego: tipo Agua o Pokemon con resistencia a Fuego; cartas que reduzcan daño o anulen debilidad. Revisa el catalogo por tipo y efectos."),
    (["efectos", "similares", "robar", "cartas"], "Cartas que permiten robar: muchos Supporters e Items tienen 'dibuja cartas' o 'roba'. Puedes pedir recomendaciones del catalogo o cartas similares a una que nombre."),
    (["ataques", "daño", "menos", "coste"], "Los ataques eficientes suelen costar 1-2 energias y hacer 30-60 de daño base, o tener efectos utiles. Revisa las cartas recomendadas para tu coleccion."),
    (["curacion", "curen", "eficientes", "cartas"], "Cartas de curacion: buscan efectos 'cura', 'HP', 'heal' en el texto. Suelen ser Items, Supporters o ataques. Pide cartas similares o del catalogo que encajen con tu mazo."),
    (["clasificar", "utilidad", "estrategica", "cartas"], "Por utilidad: robo/busqueda, aceleracion de energia, daño, curacion, control. Revisa tu coleccion y las recomendaciones; el asistente puede resumir y sugerir mejoras."),
    # Bonus
    (["mejor", "jugada", "cartas", "mano"], "La mejor jugada depende de tu mano, el tablero y el mazo. Prioriza poner basico, unir energia, robar o buscar lo que te falte. Pide una conclusion sobre tu mazo para consejos generales."),
    (["simula", "partida", "decks", "especificos"], "No puedo simular partidas completas entre dos mazos. Puedo darte reglas, escenarios concretos y recomendaciones para construir o mejorar tu deck."),
    (["deck", "meta", "recomendar", "contra"], "Contra el meta actual: incluye cartas que contrarresten los tipos y estrategias mas usados; mantén consistencia y velocidad. Revisa recomendaciones del catalogo segun tu coleccion."),
    (["evalua", "mazo", "debilidades"], "Pide 'dame una conclusion sobre mi mazo' o 'resumeme mi coleccion'; te dare recomendaciones y puntos debiles (energias, Trainers, Pokemon). Puedes pedir mejoras concretas despues."),
    (["mejoras", "deck", "presupuesto", "bajo"], "Con bajo presupuesto: prioriza cartas comunes y no promos caras; usa sustitutos de cartas meta que encajen en la estrategia. Pide cartas del catalogo que encajen con tu coleccion."),
    # Mas reglas y partida
    (["cuantas", "cartas", "robo", "inicio", "mano"], "Al inicio de la partida cada jugador roba 7 cartas. Si no tienes Pokemon basico, declaras mulligan y robas 7 de nuevo; el rival roba 1 por cada mulligan."),
    (["quien", "empieza", "primero", "partida", "elige"], "Se suele decidir por moneda o Piedra-Papel-Tijera. Quien empieza no puede atacar ni usar cartas de Entrenador en su primer turno."),
    (["que", "es", "supporter", "supporter"], "Un Supporter es un tipo de carta de Entrenador. Solo puedes jugar 1 Supporter por turno. Tienen efectos potentes como robar cartas o buscar en el mazo."),
    (["item", "carta", "que es", "entrenador"], "Los Items son cartas de Entrenador que puedes usar en cantidad ilimitada por turno (salvo que el texto diga lo contrario). Ejemplos: Pokedex, Potion, Ultra Ball."),
    (["cuantas", "energias", "mazo", "deck", "poner"], "En un mazo de 60 cartas suele recomendarse 10-14 energias para consistencia. Los decks que aceleran mucho pueden bajar a 8-10."),
    (["que", "cartas", "llevar", "mazo", "basicas"], "Basico: 60 cartas exactas; varios Pokemon basicos para no mulliganear; 30-35 Entrenadores (robo y busqueda); 10-14 energias. Ajusta segun el arquetipo."),
    (["standard", "expanded", "formato", "diferencia"], "Standard usa solo sets recientes (rotacion anual). Expanded permite mas sets antiguos. Cada formato tiene su lista de sets legales."),
    (["vmax", "vstar", "gx", "premios", "tomo"], "Por KO: Pokemon normal = 1 premio; Pokemon EX/GX/V = 2 premios; VMAX/VSTAR = 3 premios. Quien tome sus 6 premios gana."),
    # Catalogo y compra
    (["donde", "comprar", "cartas", "conseguir"], "Las cartas se compran en tiendas oficiales, eventos o sitios de coleccionismo. En esta app puedes ver el catalogo y que cartas encajan con tu coleccion; para comprar busca tiendas de TCG en tu zona."),
    (["que", "expansion", "set", "comprar", "primero"], "Depende de si juegas Standard o Expanded. Para Standard prioriza los sets mas recientes. Pide 'que cartas del catalogo encajan con mi coleccion' para sugerencias personalizadas."),
    (["completar", "coleccion", "que", "falta"], "Pide 'que cartas del catalogo encajan con mi coleccion' o 'que me recomiendas comprar' para ver sugerencias basadas en lo que ya tienes."),
    # Coleccion e inventario
    (["cuantas", "cartas", "tengo", "total"], "Pregunta 'resumen mi coleccion' o 'que tengo en mi coleccion' y el asistente te mostrara un resumen con total de cartas, Pokemon, Trainers y energias."),
    (["listar", "coleccion", "ver", "mis", "cartas"], "El asistente usa tu coleccion para recomendaciones y conclusiones. Para ver el listado completo usa la seccion de coleccion o inventario de la app si esta disponible."),
    # Escenarios rapidos
    (["dos", "supporters", "mismo", "turno", "puedo"], "No. Solo puedes jugar 1 Supporter por turno. Jugar un segundo seria ilegal."),
    (["dos", "energias", "unir", "turno", "puedo"], "Normalmente solo 1 energia de mano por turno. Algunas cartas (habilidades, Items, Supporters) permiten unir mas; el texto de la carta lo indica."),
    (["evolucion", "turno", "cuantas", "veces"], "Normalmente 1 evolucion por turno: pones la carta de evolucion encima del Pokemon correspondiente. Efectos de cartas pueden permitir mas."),
    (["retirar", "activo", "costo", "pagar"], "El coste de retirada esta en la esquina del Pokemon (ej. 2 = descartar 2 energias de ese Pokemon). Sin pagar no puedes retirar al activo."),
]


def _getFaqAnswer(question: str) -> str | None:
    """Si la pregunta coincide con un FAQ por palabras clave, devuelve la respuesta; si no, None."""
    qTokens = _tokenize(question)
    if not qTokens:
        return None
    bestScore = 0
    bestAnswer: str | None = None
    for keywords, answer in _FAQ_ENTRIES:
        score = sum(1 for kw in keywords if kw in qTokens or any(kw in t for t in qTokens))
        if score >= 2 and score > bestScore:
            bestScore = score
            bestAnswer = answer
    return bestAnswer


def _buildGeneratedConclusion(summary: CollectionSummary, recommendations: list[str]) -> str:
    """Genera un parrafo de conclusion que resume la coleccion y las recomendaciones principales."""
    parts: list[str] = []
    parts.append(
        f"Tu coleccion tiene {summary.totalDistinctCards} cartas distintas y {summary.totalCardCopies} copias en total: "
        f"{summary.pokemonCopies} Pokemon, {summary.trainerCopies} Trainers y {summary.energyCopies} energias."
    )
    if summary.rareCopies >= 6:
        parts.append(f"Cuentas con {summary.rareCopies} copias de rareza Rare o superior.")
    if summary.highHpCopies >= 8:
        parts.append(f"Tienes {summary.highHpCopies} copias de Pokemon con 130+ HP, lo que apoya un plan de juego mid o late.")
    if not recommendations:
        parts.append("Ajusta el mazo segun el metajuego y la curva de energia que busques.")
    else:
        firstTwo = recommendations[:2]
        for rec in firstTwo:
            parts.append(rec.rstrip(".") + ".")
    parts.append(
        "En conjunto, te conviene priorizar llegar a un mazo legal de 60 cartas, "
        "equilibrar Pokemon base, Trainers de consistencia y energias, y luego afinar por sinergias."
    )
    return " ".join(parts)


def _buildStructuredResponse(
    userId: int,
    question: str,
) -> dict[str, Any]:
    user = loadUserById(userId)
    if user is None:
        return {
            "error": f"No existe usuario con id={userId}.",
            "user": None,
            "question": question,
            "intent": None,
            "rules": [],
            "scenarioConclusions": [],
            "collectionSummary": None,
            "recommendations": [],
            "relevantCards": [],
            "similarCards": [],
            "recommendedCatalogCards": [],
            "unrecognizedHint": None,
            "helpMessage": None,
            "conclusion": None,
            "embeddingsAvailable": False,
        }

    if _isHelpRequest(question):
        return {
            "error": None,
            "user": {"id": user["id"], "username": user["username"], "name": user["name"]},
            "question": question,
            "intent": "help",
            "rules": [],
            "scenarioConclusions": [],
            "collectionSummary": None,
            "recommendations": [],
            "relevantCards": [],
            "similarCards": [],
            "recommendedCatalogCards": [],
            "unrecognizedHint": None,
            "helpMessage": _getHelpMessage(),
            "conclusion": (
                "Puedes usar este asistente para consultar reglas, resolver escenarios de partida, obtener recomendaciones "
                "estrategicas segun tu coleccion, pedir cartas similares a una que nombres o que te sugiera cartas del catalogo "
                "que encajen con lo que ya tienes. Abajo tienes ejemplos de preguntas para probar cada tipo de consulta."
            ),
            "embeddingsAvailable": _loadEmbeddingIndex() is not None,
        }

    if _isGreetingOnly(question):
        return {
            "error": None,
            "user": {"id": user["id"], "username": user["username"], "name": user["name"]},
            "question": question,
            "intent": "social",
            "rules": [],
            "scenarioConclusions": [],
            "collectionSummary": None,
            "recommendations": [],
            "relevantCards": [],
            "similarCards": [],
            "recommendedCatalogCards": [],
            "unrecognizedHint": None,
            "helpMessage": None,
            "conclusion": _getSocialResponse(question, isGreeting=True),
            "embeddingsAvailable": _loadEmbeddingIndex() is not None,
        }

    if _isMetaQuestion(question):
        return {
            "error": None,
            "user": {"id": user["id"], "username": user["username"], "name": user["name"]},
            "question": question,
            "intent": "social",
            "rules": [],
            "scenarioConclusions": [],
            "collectionSummary": None,
            "recommendations": [],
            "relevantCards": [],
            "similarCards": [],
            "recommendedCatalogCards": [],
            "unrecognizedHint": None,
            "helpMessage": None,
            "conclusion": _getSocialResponse(question, isGreeting=False),
            "embeddingsAvailable": _loadEmbeddingIndex() is not None,
        }

    userCards = loadUserCollection(userId)
    if not userCards:
        return {
            "error": "Usuario sin cartas en coleccion. No puedo personalizar recomendaciones.",
            "user": {"id": user["id"], "username": user["username"], "name": user["name"]},
            "question": question,
            "intent": None,
            "rules": [],
            "scenarioConclusions": [],
            "collectionSummary": None,
            "recommendations": [],
            "relevantCards": [],
            "similarCards": [],
            "recommendedCatalogCards": [],
            "unrecognizedHint": None,
            "helpMessage": None,
            "conclusion": None,
            "embeddingsAvailable": False,
        }

    summary = summarizeCollection(userCards)
    relevantCards, hadRelevantMatch = _findRelevantCards(question, userCards, topK=5)
    intent = _intentFromQuestion(question)

    rules: list[str] = []
    scenarioConclusions: list[str] = []
    recommendations: list[str] = []
    unrecognizedHint: str | None = None

    if intent == "general" and not _questionMatchesAnyIntent(question):
        unrecognizedHint = (
            "No detecte una pregunta concreta. Puedes preguntar por ejemplo: reglas o como se juega, "
            "que pasa si hago mulligan o juego dos supporters, recomendaciones o consejos para mi mazo, "
            "dame una conclusion o resumeme mi coleccion, cartas similares o sustitutas de [nombre], "
            "que cartas del catalogo encajan o que deberia comprar, o que tengo en mi coleccion."
        )
        recommendations = buildStrategicAdvice(summary)
    elif intent == "rules":
        rules = list(TCG_CORE_RULES)
        recommendations = buildStrategicAdvice(summary)
    elif intent == "scenario":
        scenarioConclusions = evaluateScenario(question)
        # Si solo obtuvimos la conclusion generica, anadir reglas mas relacionadas con la pregunta.
        if len(scenarioConclusions) == 1 and "Valida el escenario con reglas base" in scenarioConclusions[0]:
            relevantRules = getRulesRelevantToQuestion(question, TCG_CORE_RULES, 3)
            if relevantRules:
                scenarioConclusions = list(scenarioConclusions)
                scenarioConclusions.append("Reglas que pueden aplicar: " + "; ".join(relevantRules))
    elif intent == "generate_conclusion":
        recommendations = buildStrategicAdvice(summary)
    elif intent in {"strategy", "collection", "general"}:
        recommendations = buildStrategicAdvice(summary)

    # Cuando no reconocemos la pregunta, intentar responder con el FAQ interno.
    if unrecognizedHint:
        faq = _getFaqAnswer(question)
        if faq:
            unrecognizedHint = unrecognizedHint + " Por si te ayuda: " + faq

    collectionSummary = {
        "totalDistinctCards": summary.totalDistinctCards,
        "totalCardCopies": summary.totalCardCopies,
        "pokemonCopies": summary.pokemonCopies,
        "trainerCopies": summary.trainerCopies,
        "energyCopies": summary.energyCopies,
        "rareCopies": summary.rareCopies,
        "highHpCopies": summary.highHpCopies,
    }

    cardsPayload = (
        [
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "rarity": c.get("rarity") or "Unknown",
                "quantity": int(c.get("quantity") or 0),
                "setIdentifier": c.get("set_identifier") or None,
            }
            for c in relevantCards
        ]
        if hadRelevantMatch
        else []
    )

    embeddingsAvailable = _loadEmbeddingIndex() is not None
    similarCardsPayload: list[dict[str, Any]] = []
    recommendedCatalogPayload: list[dict[str, Any]] = []
    seedCardNameForConclusion: str | None = None

    if intent == "similar_to_card":
        cardName = _extractCardNameForSimilar(question)
        seedCard = _findCardForSimilarIntent(cardName, userCards)
        if seedCard:
            seedCardNameForConclusion = str(seedCard.get("name") or cardName or "")
            if embeddingsAvailable:
                userCardIdsSet = {int(c.get("id")) for c in userCards}
                similarIds = _getSimilarCardIds(int(seedCard["id"]), userCardIdsSet, topK=10)
                if similarIds:
                    ids = [sid for sid, _ in similarIds]
                    similarCardsList = loadCardsByIds(ids)
                    similarCardsPayload = [
                        {
                            "id": c.get("id"),
                            "name": c.get("name"),
                            "rarity": c.get("rarity") or "Unknown",
                            "setIdentifier": c.get("set_identifier") or None,
                        }
                        for c in similarCardsList
                    ]
            else:
                recommendations = recommendations or []
                recommendations = list(recommendations)
                recommendations.append(
                    f"Carta encontrada: {seedCardNameForConclusion}. "
                    "Para ver cartas similares necesitas generar el indice de embeddings (ejecuta embedding_pipeline.py en la carpeta 'ai model')."
                )
        elif cardName and not seedCard:
            recommendations = recommendations or []
            recommendations = list(recommendations)
            recommendations.append(
                f"No se encontro la carta '{cardName}' en tu coleccion ni en el catalogo de la app. "
                "Para que 'cartas similares a X' funcione, esa carta tiene que existir en el catalogo (tabla de cartas). "
                "Comprueba que la carta esté dada de alta en la app o prueba con una que sepas que tienes en tu coleccion."
            )

    if intent == "catalog_recommend" and embeddingsAvailable:
        userIds = [int(c.get("id")) for c in userCards]
        quantities = [int(c.get("quantity") or 0) for c in userCards]
        recIds = _getCatalogRecommendationIds(userIds, quantities, topK=10)
        if recIds:
            ids = [cid for cid, _ in recIds]
            recCardsList = loadCardsByIds(ids)
            recommendedCatalogPayload = [
                {
                    "id": c.get("id"),
                    "name": c.get("name"),
                    "rarity": c.get("rarity") or "Unknown",
                    "setIdentifier": c.get("set_identifier") or None,
                }
                for c in recCardsList
            ]

    if intent == "rules":
        conclusion = (
            "Las reglas que ves abajo son las oficiales y fundamentales del Pokemon TCG: estructura del mazo, premios, "
            "limites por turno (energia, Supporter, ataque) y condiciones de derrota. Te las resumo para que tengas una base "
            "clara antes de armar o ajustar un mazo. Ademas, he revisado tu coleccion actual y las recomendaciones que siguen "
            "tienen en cuenta cuantas cartas tienes, cuantas son Pokemon, Trainers o energias, para que puedas acercarte a un "
            "deck legal y equilibrado."
        )
    elif intent == "scenario":
        conclusion = (
            "Para responder a tu escenario he aplicado las reglas oficiales del juego paso a paso: que se puede y no se puede "
            "hacer por turno, que pasa con los premios, con el mulligan o con el deck vacio. Las conclusiones que ves abajo "
            "son la consecuencia logica de esas reglas aplicadas al caso que planteas, para que puedas resolver dudas de partida "
            "o de torneo con criterio."
        )
    elif intent == "similar_to_card" and seedCardNameForConclusion:
        if similarCardsPayload:
            conclusion = (
                f"Has pedido cartas parecidas o que encajen con {seedCardNameForConclusion}. La lista que sigue se ha obtenido "
                "comparando esa carta con el resto del catalogo en tipo, rareza, rol en el mazo y contexto de uso. Asi, las sugerencias "
                "pueden servirte como sustitutas si no tienes mas copias, como alternativas para variar el mazo, o como cartas que "
                "complementan la misma estrategia. Prioriza las que mejor encajen con el resto de tu lista."
            )
        else:
            conclusion = (
                f"Has pedido cartas similares a {seedCardNameForConclusion}. "
                "La carta esta en el catalogo; si no ves sugerencias arriba, genera el indice de embeddings (embedding_pipeline.py) para obtener cartas similares por similitud semantica."
            )
    elif intent == "catalog_recommend" and recommendedCatalogPayload:
        conclusion = (
            "Para recomendar cartas del catalogo que encajen con tu coleccion he usado un perfil promedio de tus cartas (tipo, "
            "rol y sinergia). Las que aparecen abajo son las que mas se acercan a ese perfil y que aun no tienes, de modo que "
            "pueden reforzar tu mazo sin repetir lo que ya usas. Tiene sentido valorarlas sobre todo en funcion de los huecos "
            "que notes en energias, Pokemon base, Trainers de robo o de busqueda, o en cartas de remate."
        )
    elif intent == "generate_conclusion":
        conclusion = _buildGeneratedConclusion(summary, recommendations)
    elif recommendations or unrecognizedHint:
        conclusion = (
            "Las recomendaciones que ves estan basadas en un analisis de tu coleccion: cuantas copias tienes en total, cuantas "
            "son Pokemon, cuantas Trainers y cuantas energias, y como se comparan con lo que suele llevar un mazo legal y equilibrado "
            "(por ejemplo 60 cartas, suficiente base de Pokemon para evitar mulligans, suficientes Trainers para consistencia y "
            "una curva de energia estable). No son reglas fijas, pero te dan un criterio para ajustar tu mazo y priorizar que añadir "
            "o quitar."
        )
    elif rules or scenarioConclusions or cardsPayload or similarCardsPayload or recommendedCatalogPayload:
        conclusion = (
            "La respuesta anterior se basa en tu pregunta y en los datos de tu coleccion. "
            "Si quieres una conclusion mas detallada, pregunta por ejemplo: dame una conclusion sobre mi mazo, o resumen mi coleccion."
        )
    else:
        conclusion = None

    return {
        "error": None,
        "user": {"id": user["id"], "username": user["username"], "name": user["name"]},
        "question": question,
        "intent": intent,
        "rules": rules,
        "scenarioConclusions": scenarioConclusions,
        "collectionSummary": collectionSummary,
        "recommendations": recommendations,
        "relevantCards": cardsPayload,
        "similarCards": similarCardsPayload,
        "recommendedCatalogCards": recommendedCatalogPayload,
        "unrecognizedHint": unrecognizedHint,
        "helpMessage": None,
        "conclusion": conclusion,
        "embeddingsAvailable": embeddingsAvailable,
    }


def answerQuestion(userId: int, question: str, formatJson: bool = False) -> str | dict[str, Any]:
    if formatJson:
        return _buildStructuredResponse(userId, question)

    user = loadUserById(userId)
    if user is None:
        return f"No existe usuario con id={userId}."

    userCards = loadUserCollection(userId)
    if not userCards:
        return (
            f"Usuario {user['username']} no tiene cartas en `user_cards`."
            " No puedo personalizar recomendaciones sin coleccion."
        )

    summary = summarizeCollection(userCards)
    relevantCards, hadRelevantMatch = _findRelevantCards(question, userCards, topK=5)
    intent = _intentFromQuestion(question)

    lines = []
    lines.append(f"Usuario: {user['username']} ({user['name']})")
    lines.append(f"Pregunta: {question}")
    lines.append("")

    if intent == "rules":
        lines.append("Reglas TCG clave:")
        lines.extend([f"- {rule}" for rule in TCG_CORE_RULES])
    elif intent == "scenario":
        lines.append("Conclusiones del escenario:")
        lines.extend([f"- {item}" for item in evaluateScenario(question)])
    elif intent in {"strategy", "general", "collection"}:
        lines.append("Analitica de coleccion:")
        lines.append(f"- Cartas distintas: {summary.totalDistinctCards}")
        lines.append(f"- Copias totales: {summary.totalCardCopies}")
        lines.append(f"- Pokemon: {summary.pokemonCopies}")
        lines.append(f"- Trainer: {summary.trainerCopies}")
        lines.append(f"- Energia: {summary.energyCopies}")
        lines.append("")
        lines.append("Recomendaciones:")
        lines.extend([f"- {item}" for item in buildStrategicAdvice(summary)])

    if hadRelevantMatch:
        lines.append("")
        lines.append("Cartas relevantes de tu coleccion:")
        for card in relevantCards:
            lines.append(
                "- "
                + f"{card.get('name')} | {card.get('rarity') or 'Unknown'} | "
                + f"qty={card.get('quantity')} | set={card.get('set_identifier') or 'N/A'}"
            )

    indexLoaded = _loadEmbeddingIndex()
    if indexLoaded is not None:
        lines.append("")
        lines.append("Embeddings: indice cargado correctamente para recomendaciones semanticas.")
    else:
        lines.append("")
        lines.append(
            "Embeddings: aun no hay indice. Ejecuta `python embedding_pipeline.py` para generarlo."
        )

    return "\n".join(lines)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Chatbot TCG personalizado por perfil de usuario.")
    parser.add_argument("--user-id", type=int, required=True, help="ID del usuario autenticado")
    parser.add_argument("--question", type=str, required=True, help="Pregunta del usuario")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json",
    )
    args = parser.parse_args()

    response = answerQuestion(
        userId=args.user_id,
        question=args.question,
        formatJson=(args.format == "json"),
    )
    if isinstance(response, dict):
        json.dump(response, sys.stdout, ensure_ascii=True, indent=2)
        sys.stdout.flush()
    else:
        print(response, flush=True)


if __name__ == "__main__":
    main()
