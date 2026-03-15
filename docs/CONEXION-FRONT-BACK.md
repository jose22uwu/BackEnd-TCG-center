# Conectar frontend (FrontPKMNTCG) con el backend

## Desarrollo local (recomendado)

1. **Backend** en un terminal (raíz del proyecto Laravel):
   ```bash
   php artisan serve
   ```
   O con Docker: `docker compose up -d`. La API debe quedar en http://localhost:8000.

2. **Frontend** en otro terminal (carpeta FrontPKMNTCG):
   ```bash
   cd FrontPKMNTCG
   npm install
   npm run dev
   ```
   Abre http://localhost:5173.

El frontend usa un **proxy de Vite**: las peticiones a `/api` se reenvían al backend en el puerto 8000. No hace falta crear `.env` en el frontend ni configurar CORS para desarrollo.

## Si el backend está en otro host o puerto

Crea `FrontPKMNTCG/.env` con la URL completa del backend:

```env
VITE_API_URL=http://localhost:8000/api
```

Cambia el host/puerto si tu backend no está en 8000 (por ejemplo si usas otro puerto en Docker).

## Comprobar que conectan

1. Backend: abre http://localhost:8000 en el navegador (debe responder la API o un mensaje de Laravel).
2. Frontend: en http://localhost:5173 haz login con `seller` / `password` (tras haber ejecutado los seeders). Si carga el perfil o la lista de anuncios, la conexión funciona.

## Errores frecuentes

- **CORS o “blocked by CORS”**: en desarrollo no debería aparecer si usas el proxy (front en 5173, backend en 8000). Si usas build de producción, configura `allowed_origins` en el backend (`config/cors.php`) con la URL del frontend.
- **Network Error / conexión rechazada**: el backend no está corriendo o no está en el puerto 8000. Comprueba con `php artisan serve` o `docker compose ps`.
- **401 en /user o tras login**: token inválido o expirado. Cierra sesión y vuelve a entrar con `seller` / `password`.
