# Setup rápido del backend

Script para instalar el backend desde cero en un clon nuevo (otro PC, nuevo entorno).

## Requisitos previos

- **PHP 8.2+**
- **Composer**
- **MySQL** (o MariaDB) creado y accesible
- Variables de entorno de BD en `.env` (o editar `.env` después del primer paso)

## Un solo comando

Desde la raíz del proyecto:

```bash
composer run setup-backend
```

Eso hace:

1. `composer install`
2. Crea `.env` desde `.env.example` si no existe
3. `php artisan key:generate`
4. `php artisan migrate --seed --force` (migraciones + seeders con usuarios y datos de prueba)
5. `php artisan config:clear` y `cache:clear`
6. (Opcional) `php artisan storage:link` si aplica

Si algo falla (por ejemplo la base de datos), el script se detiene y muestra en qué paso. Corrige (p. ej. `.env`) y vuelve a ejecutar:

```bash
php artisan migrate --seed --force
```

## Alternativas al comando

**PHP directo:**

```bash
php scripts/setup-backend.php
```

**Bash (Linux / Mac / Git Bash en Windows):**

```bash
./scripts/setup-backend.sh
# o
bash scripts/setup-backend.sh
```

**PowerShell (Windows):**

```powershell
.\scripts\setup-backend.ps1
```

## Después del setup

1. Revisa `.env`: `DB_DATABASE`, `DB_USERNAME`, `DB_PASSWORD` (y `APP_URL` si cambias de puerto).
2. Arranca la API:
   ```bash
   php artisan serve
   ```
3. (Opcional) Worker de colas:
   ```bash
   php artisan queue:work
   ```

Usuarios de prueba: ver [SEEDERS.md](SEEDERS.md) (seller, buyer, admin, etc. con contraseña `password`).
