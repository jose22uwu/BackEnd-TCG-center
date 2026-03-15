# Docker: frontend + backend listos sin scripts

Con Docker y Docker Compose el **frontend** (Vue), el **backend** (Laravel) y **MySQL** quedan montados sin instalar Node, PHP, Composer ni MySQL en la máquina.

## Qué hace Docker aquí

- **Frontend**: imagen que construye la app Vue con Vite y la sirve con nginx. Escucha en el puerto 8080 y consume la API del backend (URL configurable con `VITE_API_URL`).
- **Backend**: imagen con PHP 8.2, dependencias y Laravel. Al arrancar:
  - Espera a que MySQL esté listo.
  - Crea `.env` desde `.env.example` si no existe y rellena `DB_*` con los valores del compose.
  - Genera `APP_KEY`, ejecuta migraciones y seeders (usuarios de prueba, cartas de demo).
  - Deja la API en el puerto 8000.
- **MySQL**: contenedor con la base de datos y credenciales fijas en el compose.

Una vez levantado, la app (front + API) y la BD están listas para usar.

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

   La primera vez, si la carpeta `FrontPKMNTCG` no tiene el código fuente del front (carpeta `src/`), el script clona el repositorio del frontend por ti (por defecto `https://github.com/jose22uwu/FrontEnd-TCG-Center.git`; puedes cambiar la URL con la variable de entorno `FRONTEND_REPO`). Luego construye las imágenes y descarga MySQL; puede tardar unos minutos. En cada arranque del backend se ejecutan migraciones y seeders.

3. **Comprobar**
   - **Frontend (app):** http://localhost:8080  
   - **Backend API:** http://localhost:8000  
   - Usuarios de prueba (contraseña `password`): `seller`, `buyer`, `admin`, etc. Ver [SEEDERS.md](SEEDERS.md).

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

**URL del backend para el frontend:** el front se construye con `VITE_API_URL` para saber dónde llamar a la API. Por defecto es `http://localhost:8000/api` (válido cuando front y backend se usan en el mismo equipo). Si despliegas en un servidor con dominios distintos (p. ej. front en `https://app.ejemplo.com` y API en `https://api.ejemplo.com`), define en la raíz del proyecto un `.env` con:

```env
VITE_API_URL=https://api.ejemplo.com/api
```

y vuelve a construir: `docker compose build frontend && docker compose up -d`.

Para cambiar contraseña de BD u otras variables, edita `docker-compose.yml` o el `.env` en la raíz.

## Resumen

| Sin Docker | Con Docker |
|------------|------------|
| Instalar Node, PHP, Composer, MySQL | Solo Docker + Docker Compose |
| `npm run dev` + `composer run setup-backend` | `docker compose up -d --build` o `./scripts/deploy-docker.sh` |
| Configurar `.env` y BD a mano | BD y `.env` listos; front apunta al backend por defecto |

Con Docker, quien clone el repo y ejecute `docker compose up -d --build` (o el script de deploy) tiene el frontend, el backend y la base de datos funcionando sin setup adicional.
