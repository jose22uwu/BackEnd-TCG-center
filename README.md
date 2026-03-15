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

## Estructura relevante

```
app/
├── Http/Controllers/Api/   # Controladores de la API
├── Models/                 # User, Card, Listing, Bid, Invoice, etc.
├── Services/               # Lógica de negocio (ej. sincronización TCGdex)
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
