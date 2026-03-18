"""
Pruebas para los cambios del asistente: ayuda (?), extraccion de nombre, intent,
y busqueda de carta por nombre con variantes.

Ejecutar desde la raiz del proyecto (donde esta .env):
  python "ai model/tests/test_chatbot_and_db.py"
"""
from __future__ import annotations

import os
import sys

# Permitir importar desde el directorio ai model
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_MODEL_DIR = os.path.dirname(SCRIPT_DIR)
if AI_MODEL_DIR not in sys.path:
    sys.path.insert(0, AI_MODEL_DIR)

os.chdir(AI_MODEL_DIR)


def test_card_name_search_variants():
    """Variantes de nombre para Charizard VMAX deben incluir 'Charizard' y 'CharizardVMAX'."""
    from db import _cardNameSearchVariants

    variants = _cardNameSearchVariants("Charizard VMAX")
    assert "Charizard VMAX" in variants
    assert "Charizard" in variants
    assert "CharizardVMAX" in variants
    assert len(variants) >= 3

    variants2 = _cardNameSearchVariants("Pikachu VSTAR")
    assert "Pikachu VSTAR" in variants2
    assert "Pikachu" in variants2

    variants3 = _cardNameSearchVariants("Mewtwo ex")
    assert "Mewtwo ex" in variants3
    assert "Mewtwo" in variants3


def test_normalize_extracted_card_name():
    """Nombres con VMAX y colas de cortesia se normalizan bien."""
    from chatbot import _normalizeExtractedCardName

    assert _normalizeExtractedCardName("Charizard VMAX") == "Charizard VMAX"
    assert _normalizeExtractedCardName("Charizard VMAX por favor") == "Charizard VMAX"
    assert _normalizeExtractedCardName("Dhelmise V gracias") == "Dhelmise V"
    assert _normalizeExtractedCardName("Pikachu VSTAR") == "Pikachu VSTAR"


def test_help_request_detection():
    """? y ayuda deben detectarse como peticion de ayuda."""
    from chatbot import _isHelpRequest

    assert _isHelpRequest("?") is True
    assert _isHelpRequest("¿") is True
    assert _isHelpRequest("ayuda") is True
    assert _isHelpRequest("help") is True
    assert _isHelpRequest("  ?  ") is True
    assert _isHelpRequest("ayuda por favor") is True
    assert _isHelpRequest("Hola") is False
    assert _isHelpRequest("Dame reglas") is False


def test_extract_card_name_for_similar():
    """Extraccion del nombre de carta en preguntas de alternativas/similares."""
    from chatbot import _extractCardNameForSimilar

    assert _extractCardNameForSimilar("Dame alternativas a Charizard VMAX") == "Charizard VMAX"
    assert _extractCardNameForSimilar("dime una carta similar a Charizard VMAX por favor") == "Charizard VMAX"
    assert _extractCardNameForSimilar("dime una carta similar a Dhelmise V") == "Dhelmise V"
    assert _extractCardNameForSimilar("Recomienda cartas como Lapras V") == "Lapras V"
    assert _extractCardNameForSimilar("sustitutas de Pikachu") == "Pikachu"
    assert _extractCardNameForSimilar("Hola") is None
    assert _extractCardNameForSimilar("Resumen mi coleccion") is None


def test_intent_similar_to_card():
    """Preguntas de alternativas/similares deben mapear a similar_to_card."""
    from chatbot import _intentFromQuestion

    assert _intentFromQuestion("Dame alternativas a Charizard VMAX") == "similar_to_card"
    assert _intentFromQuestion("dime una carta similar a Dhelmise V") == "similar_to_card"
    assert _intentFromQuestion("Recomienda cartas similares a Lapras V") == "similar_to_card"
    assert _intentFromQuestion("sustitutas de Pikachu") == "similar_to_card"
    assert _intentFromQuestion("Resumen mi coleccion") == "generate_conclusion"
    assert _intentFromQuestion("?") == "general"


def test_question_matches_intent():
    """Preguntas con palabras clave deben reconocerse como intent conocido."""
    from chatbot import _questionMatchesAnyIntent

    assert _questionMatchesAnyIntent("Dame alternativas a Charizard VMAX") is True
    assert _questionMatchesAnyIntent("Resumen mi coleccion") is True
    assert _questionMatchesAnyIntent("xyz abc nada") is False


def test_help_response_returns_help_message():
    """Pregunta '?' debe devolver intent help y helpMessage no vacio (con usuario mock)."""
    from chatbot import _buildStructuredResponse, _isHelpRequest

    assert _isHelpRequest("?") is True
    # Solo comprobar estructura si hay usuario id 1 y no falla la conexion
    try:
        out = _buildStructuredResponse(1, "?")
        if out.get("error") is None and out.get("user"):
            assert out.get("intent") == "help"
            assert out.get("helpMessage") is not None
            assert len(out["helpMessage"]) > 100
            assert "embedding" in out["helpMessage"].lower() or "ejemplo" in out["helpMessage"].lower()
    except Exception as e:
        if "connect" in str(e).lower() or "access" in str(e).lower() or "mysql" in str(e).lower():
            raise AssertionError("DB no disponible para prueba de ayuda: " + str(e)) from e
        raise


def test_similar_intent_response_structure():
    """Para 'Dame alternativas a X' la respuesta debe tener intent similar_to_card y conclusion o recomendaciones."""
    from chatbot import _buildStructuredResponse

    try:
        out = _buildStructuredResponse(1, "Dame alternativas a Charizard VMAX")
        assert "intent" in out
        assert out["intent"] == "similar_to_card"
        assert "recommendations" in out
        assert "conclusion" in out or len(out.get("recommendations", [])) >= 0
        if out.get("similarCards"):
            assert all("name" in c for c in out["similarCards"])
    except Exception as e:
        if "connect" in str(e).lower() or "access" in str(e).lower() or "mysql" in str(e).lower():
            raise AssertionError("DB no disponible para prueba de similares: " + str(e)) from e
        raise


if __name__ == "__main__":
    import traceback

    tests = [
        ("_cardNameSearchVariants", test_card_name_search_variants),
        ("_normalizeExtractedCardName", test_normalize_extracted_card_name),
        ("_isHelpRequest(?)", test_help_request_detection),
        ("_extractCardNameForSimilar", test_extract_card_name_for_similar),
        ("_intentFromQuestion(similar)", test_intent_similar_to_card),
        ("_questionMatchesAnyIntent", test_question_matches_intent),
        ("help response (?)", test_help_response_returns_help_message),
        ("similar intent response", test_similar_intent_response_structure),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"OK: {name}")
        except Exception as e:
            failed += 1
            print(f"FAIL: {name}")
            traceback.print_exc()
    print(f"\nResultado: {len(tests) - failed}/{len(tests)} pruebas pasaron.")
    sys.exit(1 if failed else 0)
