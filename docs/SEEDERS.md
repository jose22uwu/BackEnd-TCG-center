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
3. **CardSeeder**: 8 cartas para el carrusel (swsh1-1 a swsh1-8) y 2 más para usuarios de prueba: **Lapras V** (Holo Rare V) y **Lapras VMAX** (Holo Rare VMAX). Obtiene nombre, imagen y rareza desde TCGdex; si falla la petición, usa fallback con datos reales.
4. **UserCardSeeder**: Asigna cartas a seller, buyer y seller2. Incluye al menos una **Holo Rare V** (Lapras V) y una **Holo Rare VMAX** (Lapras VMAX) para seller y buyer, además del resto de cartas de demo para anuncios y ventas.
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

### Si al sembrar ves errores de SSL (TCGdex)

Si aparece "unable to get local issuer certificate", el seeder usa un fallback con datos reales de TCGdex y las 8 cartas se crean con nombre, imagen y rareza correctos. Para que en el futuro se obtengan datos siempre desde la API (p. ej. precios o datos actualizados), puedes poner en `.env`:

```env
TCGDEX_SSL_VERIFY=false
```

y volver a ejecutar `php artisan db:seed --class=CardSeeder` o `php artisan migrate:fresh --seed`.

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
