# Seeders y credenciales de prueba

Tras ejecutar `php artisan db:seed` (o `php artisan migrate --seed`) tendrás datos de prueba y estos usuarios con **contraseña común: `password`**.

## Usuarios

| Usuario   | Contraseña | Rol          | Uso típico                          |
|-----------|------------|--------------|-------------------------------------|
| **seller**  | `password` | Usuario      | Vendedor: tiene cartas, anuncios activos y cerrados, contraofertas pendientes |
| **buyer**   | `password` | Usuario      | Comprador: tiene cartas (de una venta cerrada) y hace contraofertas |
| **admin**   | `password` | Administrador| Perfil administrador                |
| **seller2** | `password` | Usuario      | Segundo vendedor (anuncios extra)   |
| **buyer2**  | `password` | Usuario      | Segundo comprador (contraofertas)   |

## Qué genera el seed

1. **UserTypeSeeder**: Tipos de usuario (user, administrator).
2. **UserSeeder**: Los 5 usuarios de la tabla anterior.
3. **CardSeeder**: 8 cartas de ejemplo (solo si la tabla `cards` está vacía). Si ya tienes cartas (p. ej. por sincronización TCGdex), no se insertan más.
4. **UserCardSeeder**: Asigna cartas a seller, buyer y seller2 con cantidades para poder crear anuncios y completar una venta.
5. **ListingSeeder**:  
   - Un anuncio **cerrado** (venta completada a buyer; se crea factura y se mueven cartas).  
   - Varios anuncios **activos** (seller y seller2).  
   - Un anuncio **cancelado**.
6. **BidSeeder**: Contraofertas en un anuncio activo: pendientes, aceptadas y declinadas (solo registros; no ejecuta la lógica de aceptar/declinar).

## Cómo ejecutar

En un clon nuevo del proyecto (otro PC), usa siempre migrar y luego sembrar:

```bash
# Recomendado en proyecto recién clonado: migrar y sembrar de una vez
php artisan migrate --seed

# O en dos pasos (útil si quieres revisar migraciones antes)
php artisan migrate
php artisan db:seed
```

Solo sembrar (cuando la BD ya está migrada y quieres refrescar datos de prueba):

```bash
php artisan db:seed
```

Sembrar un seeder concreto:

```bash
php artisan db:seed --class=UserSeeder
```

Si ejecutas `db:seed` sin haber ejecutado `migrate` antes, los seeders lanzarán un error indicando que debes correr las migraciones.

## Reiniciar y volver a sembrar

```bash
php artisan migrate:fresh --seed
```

**Atención:** `migrate:fresh` borra todas las tablas y las vuelve a crear. No uses en producción.

## Emails de prueba

- seller@demo.local  
- buyer@demo.local  
- admin@demo.local  
- seller2@demo.local  
- buyer2@demo.local  

El login de la API usa **username** (no email). Para obtener un token:

```bash
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"seller","password":"password"}'
```
