# Docker: frontend + backend + MySQL

Con Docker y Docker Compose el **frontend** (Vue), el **backend** (Laravel) y **MySQL** quedan desplegados sin instalar Node, PHP, Composer ni MySQL en la máquina.

## Qué hace Docker aquí

- **Frontend**: imagen que construye la app Vue con Vite y la sirve con nginx. Escucha en el puerto 8080 y consume la API del backend (URL configurable con `VITE_API_URL`).
- **Backend**: imagen con PHP 8.4, Python 3 y el modelo AI (chatbot). Al arrancar:
  - Crea directorios de storage y bootstrap/cache.
  - Crea `.env` desde `.env.example` si no existe y rellena `DB_*` y `APP_URL` con los valores del compose.
  - Espera a que MySQL esté listo (healthcheck).
  - Genera `APP_KEY`, ejecuta migraciones y opcionalmente seeders (variable `ARTISAN_SEED=0` para no ejecutar seed en cada arranque). El seed incluye sincronizar hasta 300 cartas desde TCGdex (igual que en local); la primera ejecución puede tardar 1–2 minutos. Si falla por SSL, define `TCGDEX_SSL_VERIFY=false` en el entorno del backend.
  - Deja la API en el puerto 8000. Healthcheck con `php artisan route:list`.
  - El endpoint `/api/ai/chat` ejecuta el chatbot Python dentro del contenedor (`AI_PYTHON_PATH` apunta al venv de `ai model/`).
- **MySQL**: contenedor con la base de datos y credenciales fijas en el compose. Healthcheck con mysqladmin ping.

Los servicios usan `restart: unless-stopped` y el frontend espera a que el backend esté healthy antes de arrancar.

## Cómo desplegar (descargar y usar)

Requisitos: **Docker** y **Docker Compose** (o `docker compose` integrado).

1. **Clonar el repositorio del backend**
   ```bash
   git clone https://github.com/jose22uwu/BackEnd-TCG-center.git
   cd BackEnd-TCG-center
   ```

2. **Levantar frontend + backend + MySQL**
   ```bash
   docker compose up -d --build
   ```
   O desde el script de deploy:
   - **PowerShell (Windows):** `.\scripts\deploy-docker.ps1`
   - **Bash (Linux/Mac/Git Bash):** `./scripts/deploy-docker.sh`

   La primera vez, si la carpeta `FrontPKMNTCG` no tiene el código fuente del front (carpeta `src/`), el script clona el repositorio del frontend e incluye `nginx.conf` para el build. Luego construye las imágenes y descarga MySQL; puede tardar unos minutos. En cada arranque del backend se ejecutan migraciones y, por defecto, seeders (pon `ARTISAN_SEED=0` en el compose para no ejecutar seed tras el primer deploy).

3. **Comprobar**
   - **Frontend (app):** http://localhost:8080  
   - **Backend API:** http://localhost:8000  
   - Usuarios de prueba (contraseña `password`): `seller`, `buyer`, `admin`, `coleccion75` (75 cartas), etc. Ver [SEEDERS.md](SEEDERS.md). La base de datos queda con hasta 300 cartas sincronizadas desde TCGdex.
   - **Prueba del modelo AI en Docker:** desde la raíz del proyecto, `.\scripts\test-ai-docker.ps1` (PowerShell) o `./scripts/test-ai-docker.sh` (Bash). Hacen login con `seller`/`password`, llaman a `POST /api/ai/chat` y comprueban que la respuesta es correcta.

4. **Parar**
   ```bash
   docker compose down
   ```
   Para borrar también los datos de la BD: `docker compose down -v`.

**Tras cambiar código** del backend o del frontend, reconstruye y levanta de nuevo:
```bash
docker compose up -d --build
```

## Variables de entorno (opcional)

Por defecto el `docker-compose.yml` usa:

- Base de datos: `subasta_pokemon`
- Usuario MySQL: `laravel` / contraseña: `secret`
- Puerto API: 8000
- Puerto frontend: 8080
- Puerto MySQL: 3306

**URL del backend para el frontend:** el front se construye con `VITE_API_URL` (por defecto `http://localhost:8000/api`). Si despliegas con dominios distintos (p. ej. API en `https://api.ejemplo.com`), en la raíz del proyecto:

```env
VITE_API_URL=https://api.ejemplo.com/api
```

y reconstruye el frontend: `docker compose build frontend && docker compose up -d`.

Para cambiar contraseña de BD u otras variables, edita `docker-compose.yml` o el `.env` en la raíz.

## Resumen

| Sin Docker | Con Docker |
|------------|------------|
| Instalar Node, PHP, Composer, MySQL | Solo Docker + Docker Compose |
| `npm run dev` + `composer run setup-backend` | `docker compose up -d --build` o `./scripts/deploy-docker.sh` |
| Configurar `.env` y BD a mano | BD y `.env` listos; front apunta al backend por defecto |

Con Docker, quien clone el repo y ejecute `docker compose up -d --build` (o el script de deploy) tiene el frontend, el backend y la base de datos funcionando sin setup adicional.

## Paridad con el entorno local

Si levantas todo desde cero (`docker compose up -d --build` con BD nueva, p. ej. primer clone o `docker compose down -v` y volver a subir), se ejecuta **exactamente el mismo seed** que en local al hacer `php artisan migrate --seed`:

| Qué | Local | Docker desde cero |
|-----|--------|--------------------|
| Migraciones | `php artisan migrate` | Entrypoint ejecuta `migrate --force` |
| Tipos de usuario | UserTypeSeeder | Igual (DatabaseSeeder) |
| Usuarios (seller, buyer, admin, seller2, buyer2, **coleccion75**) | UserSeeder + UserWith75CardsSeeder | Igual |
| Cartas demo (10) | CardSeeder | Igual |
| **300 cartas TCGdex** | Sync300TcgdexCardsSeeder | Igual (se ejecuta en el seed; puede tardar 1–2 min) |
| Cartas asignadas a usuarios, anuncios, pujas | UserCardSeeder, ListingSeeder, BidSeeder | Igual |
| API + frontend + AI chat | Tus servicios | mysql + backend (PHP + Python/AI) + frontend |

**Contraseña de todos los usuarios de prueba:** `password`. Ver [SEEDERS.md](SEEDERS.md).

**Único matiz:** la sincronización de las 300 cartas llama a la API TCGdex desde dentro del contenedor. Si en ese entorno falla la verificación SSL, el seeder no lanza error pero solo quedarán las 10 cartas del CardSeeder. En ese caso, en la raíz del proyecto (o en el compose) define `TCGDEX_SSL_VERIFY=false` y vuelve a sembrar:

```bash
docker compose exec backend php artisan db:seed --class=Sync300TcgdexCardsSeeder --force
docker compose exec backend php artisan db:seed --class=UserWith75CardsSeeder --force
```

O pon en `docker-compose.yml` en el servicio `backend` `TCGDEX_SSL_VERIFY: "false"` (o en un `.env` en la raíz `TCGDEX_SSL_VERIFY=false`) y vuelve a crear los contenedores con BD nueva para que el seed completo use ya esa opción.
