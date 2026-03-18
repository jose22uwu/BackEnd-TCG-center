# BackEnd TCG Center

API REST para una plataforma de compraventa y subasta de cartas **Pokemon TCG**. Incluye autenticación, catálogo de cartas (sincronizado con [TCGdex](https://tcgdex.dev)), anuncios de venta, contraofertas (bids) y facturación.

## Características

- **Autenticación**: Registro, login y logout con [Laravel Sanctum](https://laravel.com/docs/sanctum) (tokens Bearer).
- **Catálogo de cartas**: Datos e imágenes desde TCGdex; historial de precios por carta.
- **Colección de usuario**: CRUD de cartas del usuario (cantidad por carta).
- **Anuncios de venta (listings)**: Crear ofertas con precio inicial; filtrar por estado (activas, cerradas, canceladas) y por anuncios con contraofertas pendientes.
- **Contraofertas (bids)**: Ofertar en un anuncio; el vendedor puede aceptar o declinar; aceptar al precio de compra directa cierra la venta.
- **Facturación**: Facturas e ítems generados al completar una venta; transferencia de cartas de vendedor a comprador.

## Stack

- **PHP 8.2+**
- **Laravel 12**
- **Laravel Sanctum** (API tokens)
- **MySQL** (por defecto; configurable)
- **TCGdex SDK** ([tcgdex/sdk](https://github.com/tcgdex/sdk-php)) para datos de cartas
- **Colas** (database driver) para tareas asíncronas

## Requisitos

- PHP 8.2+
- Composer
- MySQL 8 (o MariaDB compatible)
- Node.js 18+ y npm (solo si usas los scripts que incluyen Vite/frontend)

## Instalación

### Opción rápida (recomendada en clon nuevo)

Con PHP 8.2+ y Composer instalados:

```bash
git clone https://github.com/jose22uwu/BackEnd-TCG-center.git
cd BackEnd-TCG-center
composer run setup-backend
```

Eso instala dependencias, crea `.env`, genera la clave, ejecuta migraciones y seeders. Luego edita `.env` con tu BD si hace falta y arranca con `php artisan serve`. Detalle en [docs/SETUP.md](docs/SETUP.md).

### Instalación paso a paso

1. **Clonar el repositorio**

   ```bash
   git clone https://github.com/jose22uwu/BackEnd-TCG-center.git
   cd BackEnd-TCG-center
   ```

2. **Dependencias PHP**

   ```bash
   composer install
   ```

3. **Variables de entorno**

   ```bash
   cp .env.example .env
   php artisan key:generate
   ```

   Editar `.env` y configurar al menos:

   - `APP_NAME`, `APP_URL`
   - `DB_CONNECTION`, `DB_HOST`, `DB_PORT`, `DB_DATABASE`, `DB_USERNAME`, `DB_PASSWORD`

   Opcional (TCGdex):

   - `TCGDEX_LANGUAGE` (por defecto `en`): idioma para nombres e imágenes de cartas (`en`, `es`, `fr`, etc.).
   - `TCGDEX_SSL_VERIFY=false` solo si falla la verificación SSL en local.

4. **Base de datos**

   ```bash
   php artisan migrate
   ```

   Datos de prueba y usuarios con contraseña conocida (ver [docs/SEEDERS.md](docs/SEEDERS.md)):

   ```bash
   php artisan db:seed
   ```

   O migrar y sembrar de una vez: `php artisan migrate:fresh --seed` (borra la BD).

5. **Colas y cache**

   El proyecto usa `QUEUE_CONNECTION=database` y `CACHE_STORE=database`. Las migraciones crean las tablas necesarias. En desarrollo, levanta el worker de colas:

   ```bash
   php artisan queue:work
   ```

## Docker (recomendado para quien solo quiera usarlo)

Con Docker y Docker Compose no hace falta instalar PHP ni MySQL ni ejecutar scripts:

```bash
docker compose up -d
```

La API queda en http://localhost:8000; la BD se crea y se ejecutan migraciones y seeders al arrancar. Ver [docs/DOCKER.md](docs/DOCKER.md).

## Ejecución en local (sin Docker)

- **Servidor API**

  ```bash
  php artisan serve
  ```

  La API queda en `http://localhost:8000` (o la URL configurada en `APP_URL`).

- **Entorno de desarrollo** (si usas el script que incluye frontend y colas):

  ```bash
  composer run dev
  ```

  Arranca servidor, cola, logs y (opcional) Vite.

## API – Resumen

Todas las respuestas JSON tienen la forma `{ "success": true|false, "message": "...", "data": ... }`.

### Público

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Info de la API |
| POST | `/register` | Registro (username, name, email?, password, password_confirmation) |
| POST | `/login` | Login (username, password) → token |
| GET | `/cards` | Listado de cartas (paginado) |
| GET | `/cards/{id}` | Detalle de una carta |
| GET | `/cards/{id}/price-history` | Historial de precios de la carta |
| GET | `/listings` | Listado de anuncios (query: `status`, `seller_id`, `per_page`) |
| GET | `/listings/{id}` | Detalle de un anuncio |
| GET | `/listings/{id}/bids` | Pujas del anuncio |

### Protegidas (Header: `Authorization: Bearer {token}`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/logout` | Invalidar token |
| GET | `/user` | Usuario autenticado |
| GET | `/user/cards` | Cartas del usuario |
| POST | `/user/cards` | Añadir carta a la colección |
| PATCH | `/user/cards/{card}` | Actualizar cantidad |
| DELETE | `/user/cards/{card}` | Quitar carta |
| POST | `/listings` | Crear anuncio (starting_price, cards[]) |
| GET | `/user/listings` | Mis anuncios (query: `status`, `has_pending_bids`, `per_page`) |
| POST | `/listings/{id}/accept` | Aceptar al precio de compra (comprador) |
| PATCH | `/listings/{id}` | Actualizar anuncio (solo activos) |
| DELETE | `/listings/{id}` | Cancelar/eliminar anuncio |
| POST | `/listings/{id}/bids` | Crear contraoferta (amount) |
| PATCH | `/listings/{id}/bids/{bid}` | Aceptar/declinar contraoferta (action: accept|decline) |
| GET | `/user/invoices` | Mis facturas |
| GET | `/invoices/{id}` | Detalle de factura |

| POST | `/ai/chat` | Chat con asistente (question) – reglas TCG, resumen de colección, cartas similares, recomendaciones de catálogo |

## Modelo de embeddings (AI)

El asistente de chat (`POST /ai/chat`) puede devolver **cartas similares** y **recomendaciones de catálogo** basadas en un modelo de embeddings entrenado sobre el catálogo de cartas.

### Qué es el modelo

- **Pipeline**: En la carpeta `ai model/` está el código Python que entrena un modelo (TensorFlow/Keras) con dos ramas de entrada:
  - **Texto**: nombre, categoría, rareza, set, tipos, nombres de ataques y habilidades, debilidades y resistencias (concatenados y vectorizados).
  - **Numéricos**: HP, número de ataques/abilities/debilidades/resistencias/tipos, y flags de variante (holo, reverse, first edition).
- Una capa compartida **cardEmbedding** (64 dimensiones) se entrena con cabezas auxiliares de clasificación de **categoría** y **rareza**. Tras el entrenamiento se extraen los vectores L2-normalizados de todas las cartas y se guardan en un índice.
- **Artifacts generados** (en `ai model/artifacts/`):
  - `card_embedding_model.keras`: modelo entrenado.
  - `card_embedding_index.npz`: vectores por carta (`cardIds`, `embeddings`).
  - `embedding_metadata.json`: vocabularios y metadatos.

### Cómo se usan los embeddings en el chatbot

1. **Cartas similares**  
   Cuando el usuario pregunta por una carta concreta (p. ej. “cartas similares a Lapras V”), el chatbot busca el vector de esa carta en el índice y calcula la **similitud por producto escalar** con el resto de vectores. Las cartas con mayor puntuación se devuelven en `similarCards`. Así se ofrecen sugerencias por **similitud semántica** (nombre, tipo, rareza, ataques/habilidades).

2. **Recomendaciones de catálogo**  
   Para preguntas del tipo “qué cartas del catálogo encajan con mi colección”, se construye un **perfil de colección**: promedio ponderado de los vectores de las cartas del usuario (por cantidad). Ese vector se compara con los vectores del catálogo; las cartas con mayor puntuación se devuelven en `recommendedCatalogCards`. Sirve para recomendar cartas que “encajan” con lo que ya tiene el usuario.

3. **Sin índice de embeddings**  
   Si no existe `card_embedding_index.npz`, el chatbot sigue funcionando (reglas TCG, resumen de colección, etc.) pero no devuelve `similarCards` ni `recommendedCatalogCards`, y en la respuesta `embeddingsAvailable` es `false`. El mensaje de ayuda indica cómo generar el índice.

### Cómo generar el índice (entrenar el modelo)

Desde la raíz del backend, con Python 3 y dependencias instaladas en `ai model/` (p. ej. `pip install -r "ai model/requirements.txt"` en un venv):

```bash
cd "ai model"
python train_embedding_model.py
```

Dentro de `ai model/` también puedes ejecutar directamente `python embedding_pipeline.py` (mismo efecto).

Se requiere tener **al menos 100 cartas** en la BD (p. ej. tras `Sync300TcgdexCardsSeeder`). El script lee las cartas desde MySQL (usando `DB_*` del `.env`), entrena el modelo y escribe los artifacts en `ai model/artifacts/`. En Docker el chatbot usa un venv con dependencias mínimas (`requirements-docker.txt`, sin TensorFlow); el entrenamiento se hace en un entorno con TensorFlow instalado y luego se puede copiar solo `card_embedding_index.npz` (y opcionalmente el modelo) al contenedor o al host donde corre el chatbot.

Documentación detallada del alcance del chatbot y limitaciones: [docs/AI-CHATBOT-SCOPE.md](docs/AI-CHATBOT-SCOPE.md).

## Estructura relevante

```
app/
├── Http/Controllers/Api/   # Controladores de la API (incl. AiChatController)
├── Models/                 # User, Card, Listing, Bid, Invoice, etc.
├── Services/               # Lógica de negocio (ej. sincronización TCGdex)
ai model/                   # Modelo de embeddings y chatbot Python
├── chatbot.py              # Asistente: reglas, colección, similares, recomendaciones
├── embedding_pipeline.py   # Entrenamiento del modelo y generación del índice
├── train_embedding_model.py
├── rule_engine.py          # Reglas TCG y resumen de colección
├── db.py, config.py        # Conexión MySQL y configuración
├── artifacts/              # card_embedding_index.npz, modelo, metadata (generados)
database/
├── migrations/             # Esquema de BD
routes/
└── api.php                # Rutas de la API
```

## Tests

```bash
composer test
# o
php artisan test
```

## Licencia

MIT.
