from __future__ import annotations

from dataclasses import dataclass
from typing import Any


TCG_CORE_RULES = [
    "Deck de 60 cartas exactas.",
    "Maximo 4 copias por nombre de carta (excepto energias basicas).",
    "Premios: 6 cartas; KO normal=1 premio, EX/V=2, VMAX/VSTAR=3.",
    "Solo 1 energia unida por turno.",
    "Solo 1 Supporter por turno.",
    "Ataque: maximo 1 por turno.",
    "Banca: maximo 5 Pokemon.",
    "Si no puedes robar al inicio del turno, pierdes la partida.",
]


@dataclass
class CollectionSummary:
    totalDistinctCards: int
    totalCardCopies: int
    pokemonCopies: int
    trainerCopies: int
    energyCopies: int
    rareCopies: int
    highHpCopies: int


def summarizeCollection(userCards: list[dict[str, Any]]) -> CollectionSummary:
    totalDistinctCards = len(userCards)
    totalCardCopies = 0
    pokemonCopies = 0
    trainerCopies = 0
    energyCopies = 0
    rareCopies = 0
    highHpCopies = 0

    for card in userCards:
        quantity = int(card.get("quantity") or 0)
        totalCardCopies += quantity
        category = str(card.get("category") or "").lower()
        rarity = str(card.get("rarity") or "").lower()
        apiData = card.get("api_data") or {}
        hp = _safeInt(apiData.get("hp"))

        if "pokemon" in category:
            pokemonCopies += quantity
        elif "trainer" in category:
            trainerCopies += quantity
        elif "energy" in category:
            energyCopies += quantity

        if "rare" in rarity or "ultra" in rarity:
            rareCopies += quantity

        if hp >= 130:
            highHpCopies += quantity

    return CollectionSummary(
        totalDistinctCards=totalDistinctCards,
        totalCardCopies=totalCardCopies,
        pokemonCopies=pokemonCopies,
        trainerCopies=trainerCopies,
        energyCopies=energyCopies,
        rareCopies=rareCopies,
        highHpCopies=highHpCopies,
    )


def _safeInt(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return 0


def buildStrategicAdvice(summary: CollectionSummary) -> list[str]:
    advice: list[str] = []

    if summary.totalCardCopies < 60:
        advice.append(
            f"Tu coleccion visible tiene {summary.totalCardCopies} copias. Necesitas llegar a 60 para un deck legal."
        )
    elif summary.totalCardCopies > 60:
        advice.append(
            f"Tu coleccion visible tiene {summary.totalCardCopies} copias. Filtra hasta 60 para mantener legalidad."
        )
    else:
        advice.append("Ya estas en 60 copias, listo para un deck legal.")

    if summary.energyCopies < 10:
        advice.append("Baja cantidad de energias: considera subir a 10-14 para estabilidad.")
    if summary.trainerCopies < 12:
        advice.append("Pocos Trainers: subir Items/Supporters mejora consistencia de robo y busqueda.")
    if summary.pokemonCopies < 15:
        advice.append("Pocos Pokemon: riesgo de mulligan alto. Eleva bases para apertura estable.")
    if summary.highHpCopies >= 8:
        advice.append("Tienes buen volumen de Pokemon de alto HP: puedes jugar plan mid/late game.")
    if summary.rareCopies >= 6:
        advice.append("Tu pool incluye varias Rare: prioriza sinergias alrededor de atacantes principales.")

    if not advice:
        advice.append("Coleccion balanceada. Ajusta por metajuego y curva de energia.")

    return advice


def evaluateScenario(scenarioText: str) -> list[str]:
    scenarioLower = scenarioText.lower()
    conclusions: list[str] = []

    # Mulligan y robo inicial
    if "sin pokemon basico" in scenarioLower or "mulligan" in scenarioLower or "sin basico" in scenarioLower:
        conclusions.append(
            "Escenario mulligan: debes barajar y robar 7 nuevas; el rival roba 1 carta extra por cada mulligan."
        )
    if "robo inicial" in scenarioLower or "cuantas cartas robo" in scenarioLower or "cartas robo" in scenarioLower:
        conclusions.append(
            "Al inicio de la partida cada jugador roba 7 cartas. Si no tienes Pokemon basico, declaras mulligan y repites."
        )
    if "jugador inicial" in scenarioLower or "quien empieza" in scenarioLower or "empieza primero" in scenarioLower:
        conclusions.append(
            "El jugador que sale primero se decide por moneda o acuerdo; quien empieza no puede atacar ni usar carta de Entrenador en su primer turno."
        )

    # Premios y KO
    if "vmax" in scenarioLower or "vstar" in scenarioLower:
        conclusions.append(
            "Si das KO a un Pokemon VMAX o VSTAR del rival, tomas 3 cartas de premio."
        )
    if "premio" in scenarioLower and ("1 " in scenarioLower or "un premio" in scenarioLower or "un ko" in scenarioLower):
        conclusions.append(
            "KO a Pokemon normal (no EX/V/GX): tomas 1 carta de premio. KO a EX/V: 2 premios. KO a VMAX/VSTAR: 3 premios."
        )
    if "empate" in scenarioLower or "ultimo premio" in scenarioLower:
        conclusions.append(
            "Si ambos toman el ultimo premio en el mismo turno o hay empate por premios, se desempata por cartas restantes en el mazo (quien tenga mas gana)."
        )

    # Supporters y energias por turno
    if "supporter" in scenarioLower and ("dos" in scenarioLower or "2 " in scenarioLower or "dos " in scenarioLower):
        conclusions.append(
            "Solo puedes jugar 1 carta Supporter por turno. Jugar 2 en el mismo turno no es legal."
        )
    if ("energia" in scenarioLower or "energias" in scenarioLower) and ("dos" in scenarioLower or "2 " in scenarioLower or "dos " in scenarioLower):
        conclusions.append(
            "Solo puedes unir 1 energia de mano a un Pokemon por turno (salvo efectos de cartas que digan lo contrario)."
        )
    if "ataque" in scenarioLower and ("dos" in scenarioLower or "2 " in scenarioLower or "dos veces" in scenarioLower):
        conclusions.append(
            "Solo puedes usar 1 ataque por turno. No puedes atacar dos veces en el mismo turno."
        )

    # Deck vacio, robar, perder
    if "sin robar" in scenarioLower or "deck vacio" in scenarioLower or "mazo vacio" in scenarioLower:
        conclusions.append(
            "Si al inicio de tu turno no puedes robar porque tu mazo esta vacio, pierdes la partida."
        )
    if "retirar" in scenarioLower or "me rindo" in scenarioLower or "conceder" in scenarioLower:
        conclusions.append(
            "Puedes retirarte (conceder) en cualquier momento; el rival gana la partida."
        )

    # Banca y Pokemon activo
    if "banca" in scenarioLower and ("llena" in scenarioLower or "maximo" in scenarioLower or "5" in scenarioLower or "cinco" in scenarioLower):
        conclusions.append(
            "Puedes tener maximo 5 Pokemon en la banca. No puedes poner un sexto hasta que uno salga (KO, retirada, efecto)."
        )
    if "retreat" in scenarioLower or "retirada" in scenarioLower or "cambio de pokemon" in scenarioLower or "sustituir pokemon" in scenarioLower:
        conclusions.append(
            "Retreat: puedes cambiar el Pokemon activo por uno de la banca pagando su costo de retirada en energias (descartadas). Solo el activo puede atacar y ser atacado."
        )
    if "activo" in scenarioLower or "benched" in scenarioLower:
        conclusions.append(
            "Solo hay 1 Pokemon activo por jugador. El resto esta en banca; el activo es el que ataca y recibe ataques."
        )

    # Primer turno y evolucion
    if "turno 1" in scenarioLower or "primer turno" in scenarioLower:
        conclusions.append(
            "En el primer turno del jugador que empieza no se puede atacar ni usar cartas de Entrenador (Items/Supporters/Stadium)."
        )
    if "evolucionar" in scenarioLower or "evolucion" in scenarioLower:
        conclusions.append(
            "Puedes evolucionar Pokemon en la banca o activo si tienes la carta de evolucion encima del Pokemon base (o Etapa 1) correspondiente; normalmente solo una evolucion por turno."
        )

    # Copias y legalidad del mazo
    if "4 copias" in scenarioLower or "copias en el mazo" in scenarioLower or "limite de copias" in scenarioLower:
        conclusions.append(
            "Maximo 4 copias de una misma carta por nombre en el mazo (excepto energias basicas, que no tienen limite)."
        )
    if "carta ilegal" in scenarioLower or "deck invalido" in scenarioLower or "mazo invalido" in scenarioLower:
        conclusions.append(
            "Un mazo es ilegal si no tiene 60 cartas, tiene mas de 4 copias de alguna carta (salvo energia basica), o incluye cartas no permitidas en el formato."
        )

    # Ganar partida
    if "gana" in scenarioLower or "ganar" in scenarioLower or "ganar partida" in scenarioLower or "como se gana" in scenarioLower:
        conclusions.append(
            "Ganas la partida si: tomas tus 6 cartas de premio, o el rival se queda sin Pokemon en el campo (activo + banca), o el rival no puede robar al inicio de su turno."
        )
    # Pokemon basico
    if "pokemon basico" in scenarioLower or "basico" in scenarioLower and "pokemon" in scenarioLower and "que es" in scenarioLower:
        conclusions.append(
            "Pokemon Basico es el que se pone en juego desde la mano (no es evolucion). Necesitas al menos uno en la mano inicial para no hacer mulligan."
        )
    # Premios (como funcionan)
    if "premio" in scenarioLower and ("funcionan" in scenarioLower or "como" in scenarioLower or "cartas de premio" in scenarioLower):
        conclusions.append(
            "Al inicio pones 6 cartas boca abajo como premios. Cada vez que das KO a un Pokemon rival, tomas 1, 2 o 3 premios segun el tipo (normal 1, EX/V 2, VMAX/VSTAR 3). Quien tome sus 6 premios gana."
        )
    # Activo vs Banca
    if "activo" in scenarioLower and "banca" in scenarioLower:
        conclusions.append(
            "El Pokemon Activo es el que esta en el centro y puede atacar/recibir ataques. Los demas estan en la Banca (max 5); solo el activo cuenta para combate. Puedes retirar (retreat) al activo pagando su costo."
        )
    # Entrenador
    if "entrenador" in scenarioLower and ("carta" in scenarioLower or "cartas" in scenarioLower):
        conclusions.append(
            "Cartas de Entrenador: Items (ilimitados por turno), Supporters (1 por turno), Stadiums (1 en juego entre ambos). Se juegan en tu turno y tienen efectos inmediatos segun el texto."
        )
    # Calcular daño
    if "daño" in scenarioLower or "danio" in scenarioLower or "damage" in scenarioLower or "calcula" in scenarioLower and "ataque" in scenarioLower:
        conclusions.append(
            "El daño del ataque es el numero base del ataque. Se aplica debilidad (x2 u otro) y resistencia (-20, -30, etc.). Luego se restan defensas si las hay. Si el daño final >= HP del rival, el Pokemon queda K.O."
        )
    # KO
    if "k.o" in scenarioLower or "ko" in scenarioLower or "queda ko" in scenarioLower or "derrotar" in scenarioLower:
        conclusions.append(
            "Cuando un Pokemon recibe daño >= su HP, queda K.O.: va al descarte del rival y este toma premios (1, 2 o 3 segun el tipo). Si no tiene Pokemon en banca para reemplazar, pierde la partida."
        )
    # Confundido
    if "confundido" in scenarioLower or "confusion" in scenarioLower:
        conclusions.append(
            "Confundido: al atacar, lanzas moneda. Cruz = el ataque falla y el Pokemon se hace 30 de daño a si mismo. Cara = el ataque se ejecuta normal."
        )
    # Envenenamiento
    if "envenenamiento" in scenarioLower or "envenenado" in scenarioLower or "poison" in scenarioLower:
        conclusions.append(
            "Envenenado: entre turnos, el Pokemon recibe daño (suele ser 10 o 20 por contador). Los contadores se ponen segun el ataque o efecto que lo cause."
        )
    # Debilidad y resistencia
    if "resistencia" in scenarioLower or "debilidad" in scenarioLower:
        conclusions.append(
            "Debilidad y resistencia se aplican al calcular el daño del ataque: debilidad suele x2, resistencia resta (p. ej. -30)."
        )
    # Coste de retirada
    if "coste de retirada" in scenarioLower or "costo de retirada" in scenarioLower or "retreat" in scenarioLower and "cost" in scenarioLower:
        conclusions.append(
            "El coste de retirada es el numero de energias que debes descartar del Pokemon para retirarlo a la banca y poner otro como activo. Si no puedes pagar, no puedes retirar."
        )
    # Atacar primer turno
    if "primer turno" in scenarioLower and "atacar" in scenarioLower or "atacar" in scenarioLower and "primero" in scenarioLower:
        conclusions.append(
            "El jugador que empieza no puede atacar ni usar cartas de Entrenador en su primer turno. El segundo jugador si puede."
        )
    # Atacar sin energia
    if "atacar" in scenarioLower and ("sin energia" in scenarioLower or "sin energias" in scenarioLower):
        conclusions.append(
            "Normalmente los ataques tienen un coste en energias unidas al Pokemon. Si no tienes las energias necesarias, no puedes usar ese ataque. Algunas cartas tienen ataques de 0 coste o efectos que reducen coste."
        )
    # Efectos adicionales ataque
    if "efectos adicionales" in scenarioLower or "efecto del ataque" in scenarioLower:
        conclusions.append(
            "Muchos ataques tienen texto adicional (ej. robar cartas, poner daño, paralisis). Se resuelven en el orden que indique la carta despues de aplicar el daño."
        )
    # Lanzar moneda
    if "moneda" in scenarioLower or "lanzar" in scenarioLower and "ataque" in scenarioLower or "cara o cruz" in scenarioLower:
        conclusions.append(
            "Algunos ataques o efectos piden lanzar 1 o mas monedas. Cara/Cara = suele doble daño o efecto; Cruz = fallo o sin efecto. El numero de caras necesarias lo indica la carta."
        )
    if "tool" in scenarioLower or "herramienta" in scenarioLower:
        conclusions.append(
            "Las cartas Tool (herramienta) se unen a un Pokemon y permanecen; cada Pokemon puede tener solo 1 Tool a la vez (salvo que la carta diga lo contrario)."
        )
    if "stadium" in scenarioLower or "estadio" in scenarioLower:
        conclusions.append(
            "Solo puede haber 1 Stadium en juego (entre ambos jugadores). Si se juega otro Stadium, el anterior se descarta."
        )
    if "item" in scenarioLower and ("varios" in scenarioLower or "cuantos" in scenarioLower or "muchos" in scenarioLower):
        conclusions.append(
            "Puedes jugar tantas cartas Item como quieras en tu turno (a diferencia del Supporter, que es 1 por turno)."
        )

    # Descarte y buscar
    if "descarte" in scenarioLower or "descartar" in scenarioLower:
        conclusions.append(
            "Muchos efectos obligan a descartar cartas; van al monton de descartes. Si un efecto pide descartar y no tienes, no puedes cumplirlo (salvo que la carta diga otra cosa)."
        )
    if "buscar en el mazo" in scenarioLower or "buscar carta" in scenarioLower:
        conclusions.append(
            "Efectos que buscan en el mazo te permiten revelar y tomar cartas; barajas el mazo despues. El orden del mazo no puede verse por el rival."
        )

    if not conclusions:
        conclusions.append(
            "Valida el escenario con reglas base: 1 energia/turno, 1 Supporter/turno, banca max 5, 1 ataque/turno. Si concretas mas (mulligan, premios, primer turno, etc.), te doy la regla exacta."
        )
    return conclusions


def getRulesRelevantToQuestion(question: str, rules: list[str], topK: int = 3) -> list[str]:
    """Devuelve las reglas con mayor solapamiento de palabras con la pregunta (sin APIs externas)."""
    qTokens = _tokenizeForRelevance(question)
    if not qTokens:
        return rules[:topK]
    scored: list[tuple[int, str]] = []
    for rule in rules:
        rTokens = _tokenizeForRelevance(rule)
        overlap = len(qTokens & rTokens)
        scored.append((overlap, rule))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [rule for _, rule in scored[:topK] if rule]


def _tokenizeForRelevance(text: str) -> set[str]:
    """Tokens para relevancia: palabras de 2+ caracteres, sin acentos normalizados."""
    import unicodedata
    normalized = unicodedata.normalize("NFD", (text or "").lower())
    without_accents = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return {w.strip(" ,.!?;:()[]{}") for w in without_accents.split() if len(w.strip(" ,.!?;:()[]{}")) >= 2}
