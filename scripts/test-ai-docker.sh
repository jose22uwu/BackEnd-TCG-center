#!/usr/bin/env bash
# Prueba de funcionamiento del modelo AI en Docker.
# Requiere: backend + MySQL levantados (docker compose up -d). Usuario seller/password debe existir (seed).
# Ejecutar desde la raiz: ./scripts/test-ai-docker.sh

set -e
API_URL="${API_URL:-http://localhost:8000}"
API="$API_URL/api"

echo "API base: $API"

# Login
LOGIN_RESP=$(curl -s -w "\n%{http_code}" -X POST "$API/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"seller","password":"password"}')
HTTP_LOGIN=$(echo "$LOGIN_RESP" | tail -n1)
BODY_LOGIN=$(echo "$LOGIN_RESP" | sed '$d')
if [ "$HTTP_LOGIN" != "200" ]; then
  echo "Login fallido (HTTP $HTTP_LOGIN): $BODY_LOGIN"
  exit 1
fi
TOKEN=$(echo "$BODY_LOGIN" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
if [ -z "$TOKEN" ]; then
  echo "Login no devolvio token. Respuesta: $BODY_LOGIN"
  exit 1
fi
echo "Login OK, token obtenido."

# AI Chat
CHAT_RESP=$(curl -s -w "\n%{http_code}" -X POST "$API/ai/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question":"Que reglas aplican?"}')
HTTP_CHAT=$(echo "$CHAT_RESP" | tail -n1)
BODY_CHAT=$(echo "$CHAT_RESP" | sed '$d')
if [ "$HTTP_CHAT" != "200" ]; then
  echo "AI chat fallo (HTTP $HTTP_CHAT): $BODY_CHAT"
  exit 1
fi

# Verificar que hay .data (y opcionalmente rules/collectionSummary)
if ! echo "$BODY_CHAT" | grep -q '"data"'; then
  echo "Respuesta sin .data: $BODY_CHAT"
  exit 1
fi
echo "AI chat OK."
if echo "$BODY_CHAT" | grep -q '"rules"'; then
  echo "rules presente."
fi
if echo "$BODY_CHAT" | grep -q 'collectionSummary'; then
  echo "collectionSummary presente."
fi
echo "Prueba de AI en Docker completada."
