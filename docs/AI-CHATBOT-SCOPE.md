# Alcance del chatbot TCG y huecos realizables

Resumen de **situaciones que el modelo aún no resuelve** pero que están **dentro de su alcance** (datos o reglas ya disponibles, o lógica fácil de extender).

---

## 1. Reglas y escenarios TCG (rule_engine)

**Datos/reglas ya documentados en el proyecto** que no están codificados:

| Situación | Dato disponible | Estado actual |
|-----------|-----------------|---------------|
| Estados especiales (Dormido, Confundido, Quemado, Envenenado, Paralizado) | Reglas descritas por el usuario | No hay ramas en `evaluateScenario()` |
| Retirada: coste, una vez por turno, descartar energías | Mencionado en reglas TCG | No está en `TCG_CORE_RULES` ni en escenarios |
| Evolución: Básico → Fase 1 → Fase 2, no evolucionar el mismo turno que bajas | Reglas TCG | No hay escenarios "qué pasa si evoluciono el mismo turno" |
| Objetos (Items): ilimitados por turno | Reglas TCG | No explicitado en reglas devueltas |
| Estadio: solo uno en juego, reemplaza al anterior | Reglas TCG | No está en reglas ni escenarios |
| Herramienta Pokémon: una por Pokémon | Reglas TCG | No está |
| Barajar obligatorio tras buscar en el deck | Reglas TCG | No hay escenario "buscar en el deck" |
| Victoria: tomar todos los premios / rival sin Pokémon activo | Reglas TCG | Solo "rival no puede robar" (deck vacío) está en escenarios |
| Orden de efectos cuando varias cosas pasan a la vez | Reglas TCG | No modelado |
| EX vs V: premios (2); VMAX/VSTAR: 3 premios | Sí en reglas | Solo texto genérico en escenario VMAX/VSTAR |

**Ejemplos de preguntas que hoy no tienen respuesta específica:**

- "¿Qué pasa si mi Pokémon está quemado?"
- "¿Cuántas veces me puedo retirar por turno?"
- "¿Puedo evolucionar el mismo turno que juego un básico?"
- "¿Qué pasa si juego un segundo Estadio?"
- "¿Cuándo gano la partida?"

---

## 2. Colección y estrategia (rule_engine + chatbot)

**Datos en BD/cartas (`api_data`)** que el pipeline ya usa para embeddings pero **no** para recomendaciones:

| Dato | Dónde está | Uso actual en chatbot |
|------|------------|------------------------|
| Tipos de Pokémon (Fuego, Agua, etc.) | `api_data.types` | No; solo conteo genérico Pokemon/Trainer/Energy |
| Debilidades / resistencias | `api_data.weaknesses`, `api_data.resistances` | No |
| Coste de ataques (energías) | `api_data.attacks[].cost` | No |
| Daño de ataques | `api_data.attacks` | No |
| Habilidades (abilities) | `api_data.abilities` | No (sí en embeddings para texto) |
| Subtipos de Trainer (Item, Supporter, Stadium, Tool) | `category` podría refinarse | Solo "trainerCopies" global |

**Situaciones realizables sin nuevo dato:**

- "Dame mis cartas de tipo Fuego" → filtrar por `api_data.types`.
- "Qué cartas mías tienen debilidad a Rayo" → filtrar por `weaknesses`.
- "Recomiéndame cartas que combinen con Lapras V" → usar **embeddings** (similitud por vector); el índice existe pero el chatbot **no** hace búsqueda por similitud.
- "Tengo pocas energías en el mazo" → ya se recomienda subir energías; se podría cruzar con tipos de ataques de las cartas del usuario para sugerir tipos de energía.
- Desglose Trainer: "¿Cuántos Items vs Supporters tengo?" → requeriría etiquetar subtipo en `api_data` o en category.

---

## 3. Búsqueda de cartas relevantes (chatbot)

| Situación | Alcance | Estado actual |
|-----------|---------|----------------|
| "Cartas similares a X" o "que combinen con X" | Embeddings; índice por `card_id` | **Implementado:** intent `similar_to_card`; respuesta en `similarCards` (hasta 10 del catálogo). Palabras clave: "similares a", "parecidas a", "combinan con", "recomienda como", "cartas como". |
| Recomendar cartas del **catálogo** (300) que encajen con la colección | Centroid de embeddings de la colección | **Implementado:** intent `catalog_recommend`; respuesta en `recommendedCatalogCards` (hasta 10). Palabras clave: "catalogo", "encajen con mi coleccion", "complementen", "cartas me faltan", "recomienda del catalogo". |
| "Mis cartas con más de 100 HP" | `api_data.hp` en colección | No hay filtro por HP en respuestas |
| "Cartas que puedan atacar por 2 energías" | `api_data.attacks` con coste | No hay filtro por coste de ataque |

---

## 4. Intents y preguntas genéricas (chatbot)

**Palabras clave que podrían mapear a intents ya existentes** pero no están en la lista:

- Victoria / perder / empate → podrían reforzar **rules** o un bloque "condiciones de victoria".
- Evolución / evolucionar → **rules** o **scenario**.
- Retirada / retreat → **rules**.
- Objeto / Item / Supporter / Estadio / Herramienta → **rules** (límites por turno).

Preguntas que hoy caen en **general** y reciben solo resumen + recomendaciones genéricas:

- "¿Cómo gano la partida?"
- "¿Qué es la retirada?"
- "¿Puedo usar dos objetos en el mismo turno?"

---

## 5. Resumen prioritario

| Prioridad | Qué hacer | Dificultad |
|-----------|-----------|------------|
| ~~Alta~~ Hecho | ~~Usar **embeddings** en el chatbot~~ | **Implementado:** `similarCards` (similares a una carta) y `recommendedCatalogCards` (catálogo que encaja con la colección). |
| Alta | Añadir más **reglas TCG** al texto (retirada, evolución, Items/Supporter/Estadio/Herramienta, condiciones de victoria) | Baja |
| Media | Ampliar **evaluateScenario** con estados especiales, retirada, evolución mismo turno, segundo Estadio, barajar tras buscar | Media |
| Media | Filtros por **tipo, debilidad, HP, coste de ataque** sobre la colección del usuario y exponer en respuesta (o nuevo intent "filtro") | Baja–media |
| Baja | Desglose Trainer (Item vs Supporter vs Stadium vs Tool) si el dato existe en TCGdex | Depende del API |

Este documento se puede actualizar cuando se implemente alguna de estas mejoras.
