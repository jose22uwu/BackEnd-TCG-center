# Scripts de setup del backend

Scripts para dejar el backend listo desde cero (dependencias, `.env`, migraciones y seeders).

## Requisitos

- PHP 8.2+
- Composer
- Base de datos MySQL (o MariaDB) creada y accesible

## Inicializar el sistema

Desde la **raíz del proyecto** (carpeta donde está `composer.json`):

```bash
composer run setup-backend
```

Ese comando:

1. Instala dependencias (`composer install`)
2. Crea `.env` desde `.env.example` si no existe
3. Genera la clave de aplicación
4. Ejecuta migraciones y seeders (usuarios y datos de prueba)
5. Limpia config y caché

Si la base de datos falla, configura en `.env` las variables `DB_DATABASE`, `DB_USERNAME` y `DB_PASSWORD` y vuelve a ejecutar:

```bash
php artisan migrate --seed --force
```

## Otras formas de ejecutar el setup

**PHP directo** (desde la raíz del proyecto):

```bash
php scripts/setup-backend.php
```

**Bash** (Linux, Mac o Git Bash en Windows):

```bash
./scripts/setup-backend.sh
```

**PowerShell** (Windows):

```powershell
.\scripts\setup-backend.ps1
```

## Después del setup

1. Arrancar la API:
   ```bash
   php artisan serve
   ```
2. (Opcional) Worker de colas:
   ```bash
   php artisan queue:work
   ```

Usuarios de prueba (contraseña `password`): `seller`, `buyer`, `admin`, `seller2`, `buyer2`. Detalle en `docs/SEEDERS.md`.
