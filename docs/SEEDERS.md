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
| **coleccion75** | `password` | Usuario  | Usuario con 75 cartas en inventario (para pruebas de colección/IA) |

## Qué genera el seed

Al ejecutar `php artisan db:seed` (o `migrate --seed`) se lanza **DatabaseSeeder**, que ejecuta en este orden:

1. **UserTypeSeeder**: Tipos de usuario (user, administrator).
2. **UserSeeder**: Los 5 usuarios seller, buyer, admin, seller2, buyer2.
3. **CardSeeder**: 8 cartas para el carrusel (swsh1-1 a swsh1-8) y 2 más para usuarios de prueba: **Lapras V** (Holo Rare V) y **Lapras VMAX** (Holo Rare VMAX). Obtiene nombre, imagen y rareza desde TCGdex; si falla la petición, usa fallback con datos reales.
4. **Sync300TcgdexCardsSeeder**: Sincroniza hasta 300 cartas desde la API TCGdex (swsh1 + swsh2) con HP, ataques, tipos, debilidades, resistencias, habilidades. En Docker se ejecuta igual que en local; la primera vez puede tardar 1–2 minutos.
5. **UserWith75CardsSeeder**: Crea/actualiza el usuario **coleccion75** y le asigna 75 cartas distintas en inventario (o todas las disponibles si hay menos de 75).
6. **UserCardSeeder**: Asigna cartas a seller, buyer y seller2. Incluye al menos una **Holo Rare V** (Lapras V) y una **Holo Rare VMAX** (Lapras VMAX) para seller y buyer, además del resto de cartas de demo para anuncios y ventas.
7. **ListingSeeder**:  
   - Un anuncio **cerrado** (venta completada a buyer; se crea factura y se mueven cartas).  
   - Varios anuncios **activos** (seller y seller2).  
   - Un anuncio **cancelado**.
8. **BidSeeder**: Contraofertas en un anuncio activo: pendientes, aceptadas y declinadas (solo registros; no ejecuta la lógica de aceptar/declinar).

En **Docker**, al arrancar el backend con `ARTISAN_SEED=1` (valor por defecto) se ejecuta este mismo DatabaseSeeder, así que obtienes los mismos usuarios, las mismas cartas (incluidas las 300 de TCGdex si la API responde) y el mismo usuario coleccion75.

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

### Sincronizar ~300 cartas con HP, ataques y sinergias (TCGdex)

Para tener unas 300 cartas en la base con datos completos del API (HP, ataques, tipos, debilidades, resistencias, habilidades), ejecuta el seeder de sincronización o el comando artisan:

```bash
# Opción 1: seeder (tras migrate)
php artisan db:seed --class=Sync300TcgdexCardsSeeder

# Opción 2: comando (mismo resultado)
php artisan tcgdex:sync-cards --limit=300
```

Por defecto se traen cartas de los sets **swsh1** (Sword & Shield) y **swsh2**. Para otros sets: `php artisan tcgdex:sync-cards --limit=300 --sets=swsh1,swsh2,swsh3`. Cada carta se guarda con `api_data` en JSON que incluye: `hp`, `attacks` (nombre, coste, daño, efecto), `types`, `weaknesses`, `resistances`, `abilities` (sinergias). La API REST devuelve ese `api_data` en `GET /cards` y `GET /cards/{id}`. Si falla por SSL, usa `TCGDEX_SSL_VERIFY=false` en `.env`. El límite es configurable con `TCGDEX_SYNC_LIMIT=300` en `.env`.

## Emails de prueba

- seller@demo.local  
- buyer@demo.local  
- admin@demo.local  
- seller2@demo.local  
- buyer2@demo.local  
- coleccion75@demo.local  

El login de la API usa **username** (no email). Para obtener un token:

```bash
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"seller","password":"password"}'
```
