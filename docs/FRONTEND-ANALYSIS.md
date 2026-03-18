# Análisis del frontend FrontPKMNTCG

Frontend Vue 3 de la aplicación Pokemon TCG Center (compra/venta y subastas). Ubicación en el repo: **`FrontPKMNTCG/`** (carpeta hermana del backend Laravel en la raíz del proyecto).

---

## 1. Stack y entorno

| Tecnología | Versión / Uso |
|------------|----------------|
| Vue | 3.5.x |
| Vite | 8.x (build y dev server) |
| Vue Router | 4.6.x |
| Pinia | 3.x (estado global) |
| Axios | 1.13.x (HTTP al API) |

- **Dev:** `npm run dev` → http://localhost:5173. Proxy de Vite: `/api` → `http://127.0.0.1:8000`.
- **API base:** `import.meta.env.VITE_API_URL` o en dev `/api` (proxy). En producción se usa `VITE_API_URL` (ej. `http://localhost:8000/api` o URL del backend en Docker).
- **Producción:** `npm run build` → `dist/`. Docker sirve ese build con nginx en el puerto 8080.

---

## 2. Estructura del proyecto

```
FrontPKMNTCG/
  index.html
  package.json
  vite.config.js
  Dockerfile
  nginx.conf
  src/
    main.js              # createApp, Pinia, Router, main.css
    App.vue              # RouterView + useScreenDust (efecto polvo)
    router/index.js      # Rutas y guard de auth
    services/api.js      # Axios baseURL + interceptors (token, 401 → logout)
    stores/auth.js       # Pinia: token, user, setAuth, logout, validateSession
    layouts/MainLayout.vue
    views/
      LoginView.vue
      RegisterView.vue
      HomeView.vue
      BuyView.vue
      SellView.vue
      MyListingsView.vue
      ProfileView.vue
    components/
      CardThumb.vue
      HoloModalLowPolyBg.vue
    composables/
      useClickOutside.js
      useScreenDust.js
    constants/
      rarityModalStyles.js   # Rareza → estilos modal (Holo Rare V, etc.)
    utils/
      apiResponse.js        # normalizeApiList(data, defaultVal)
      cardImage.js          # cardImageSrc(url) → URL imagen TCGdex
    styles/
      main.css, app.css, base.css, variables.css
      screen-dust.css
      views/*.css
      layouts/MainLayout.css
      components/HoloModalLowPolyBg.css
```

---

## 3. Rutas y vistas

| Ruta | Vista | Auth | Descripción |
|------|--------|------|-------------|
| `/login` | LoginView | Guest (redirige a home si ya logueado) | Login por username + password |
| `/register` | RegisterView | Guest | Registro (username, name, email opcional, password) |
| `/` | HomeView | Sí | Inicio: carrusel de cartas (`/carousel`) y enlaces a Comprar / Vender |
| `/profile` | ProfileView | Sí | Álbum del usuario: listado de `/user/cards` con filtro por rareza |
| `/buy` | BuyView | Sí | Listado de ofertas activas (`/listings?status=active`), aceptar o contraoferta |
| `/sell` | SellView | Sí | Cartas del usuario no en anuncios activos; crear anuncio (precio + carta) |
| `/listings` | MyListingsView | Sí | Mis anuncios (`/user/listings`), filtros activas/cerradas/contraofertas |
| `/chat` | ChatView | Sí | Asistente IA: preguntas sobre reglas, escenarios, colección; llama a `POST /ai/chat` |

- **Guard:** rutas con `meta.auth` requieren sesión; si no hay token → redirect a `/login?redirect=...`. Rutas con `meta.guest` redirigen a `/` si ya hay sesión.
- **Título:** `document.title = to.meta.title + " | Pokemon TCG Center"`.

---

## 4. Endpoints del API utilizados

Resumen de llamadas desde el front (todas vía `api` de `services/api.js`):

| Método | Endpoint | Vista / Store |
|--------|----------|----------------|
| POST | `/login` | LoginView |
| POST | `/register` | RegisterView |
| GET | `/user` | auth store (validateSession) |
| GET | `/carousel` | HomeView |
| GET | `/listings` | BuyView (params: status=active, per_page=30) |
| POST | `/listings/:id/accept` | BuyView |
| POST | `/listings/:id/bids` | BuyView (body: { amount }) |
| GET | `/user/cards` | ProfileView, SellView (per_page 100) |
| GET | `/user/listings` | SellView, MyListingsView (per_page, status, has_pending_bids) |
| POST | `/listings` | SellView (body: starting_price, cards: [{ card_id, quantity }]) |
| PATCH | `/listings/:id/bids/:bidId` | MyListingsView (body: { action: 'accept' \| 'decline' }) |
| DELETE | `/listings/:id` | MyListingsView |
| GET | `/cards/:id/price-history` | SellView (gráfico de precios al crear oferta) |
| POST | `/ai/chat` | ChatView (body: `{ question }`; respuesta con helpMessage, rules, scenarioConclusions, similarCards, etc.) |

**No se usan en el front (existen en el backend):**

- `GET /cards` (catálogo público con filtros)
- `GET /cards/:id` (detalle de carta)

---

## 5. Autenticación y estado

- **Token:** guardado en `localStorage` como `token`; usuario en `user` (JSON). El store Pinia los lee al iniciar y los actualiza en login/validateSession.
- **Interceptor request:** añade `Authorization: Bearer <token>` si existe.
- **Interceptor response:** ante 401 elimina token y user de localStorage y redirige a `/login` con `window.location.href`.
- **Validación al cargar:** en `App.vue` (onMounted), si hay token se llama a `auth.validateSession()` (GET `/user`) y se actualiza el usuario en el store.

El backend usa **Sanctum** con login por **username** (no email); el front ya usa `username` en el formulario de login.

---

## 6. Normalización de respuestas y datos

- **normalizeApiList(data, defaultVal):** extrae el array de la respuesta estándar del backend (`{ success, data }`). Soporta `data` como array o como `{ data: [] }`. Si `data.success` es falso o no hay datos, devuelve `defaultVal`.
- Las vistas asumen que el backend devuelve `{ success: true, data: ... }`. Errores se leen de `e.response?.data?.message` o `e.response?.data?.errors`.

---

## 7. Estilos y UX

- **Fuentes:** Fredoka, Red Hat Display (Google Fonts).
- **Preconnect:** assets.tcgdex.net, fonts.googleapis.com, fonts.gstatic.com.
- **Efectos:** “screen dust” en App.vue; modales con fondo holofoil (`HoloModalLowPolyBg`) para cartas Holo Rare V; filtros por rareza en Buy, Profile y Sell (dropdown con `RARITY_FILTER_OPTIONS`).
- **Responsive:** carrusel en Home usa lógica móvil (eje vertical en pantallas &lt; 768px); navegación con toggler en MainLayout.
- **Accesibilidad:** aria-label en botones, role listbox en filtros, role="dialog" en modales.

---

## 8. Integración con el backend actual

- **Coincide con el backend:** login (username/password), register, `/user`, `/carousel`, `/listings`, `/listings/:id/accept`, `/listings/:id/bids`, `/user/cards`, `/user/listings`, POST/PATCH/DELETE de listings y bids, `/cards/:id/price-history`. Formato de respuesta `{ success, message, data }` y manejo de errores son compatibles.
- **CORS:** en desarrollo el proxy de Vite evita CORS; en producción el backend debe permitir el origen del front (config/cors.php).
- **Paginación:** el front envía `per_page` (30, 50 o 100); el backend puede devolver paginación Laravel; el front no muestra controles de página siguiente/anterior, solo la primera página.

---

## 9. Lo que el front no cubre (respecto al backend)

1. **Chatbot / IA:** integrado en la ruta `/chat` (vista Asistente): llama a `POST /ai/chat`, muestra helpMessage, rules, scenarioConclusions, collectionSummary, recommendations, relevantCards, similarCards, recommendedCatalogCards y unrecognizedHint.
2. **Catálogo público:** no hay vista de búsqueda/exploración del catálogo (`GET /cards` con search, category, set). En Vender se eligen solo cartas que el usuario ya tiene (`/user/cards`).
3. **Facturas:** `GET /user/invoices` y `GET /invoices/:id` existen en el API pero no hay vista “Mis facturas” o historial de compras/ventas.
4. **Detalle de carta pública:** no se usa `GET /cards/:id` para una ficha de carta del catálogo (solo precio-history en Sell para una carta del usuario).
5. **Variables de entorno:** no hay `.env` en el repo (sí `.env.example` en la documentación del README); en Docker se inyecta `VITE_API_URL` en build.

---

## 10. Posibles desajustes o mejoras

- **Paginación:** si el backend devuelve `data` con estructura paginada (ej. `data: { data: [], current_page, last_page }`), `normalizeApiList` ya contempla `d.data` como array; si en algún endpoint se devuelve solo `data` con links/meta, alguna vista podría necesitar adaptación para mostrar “siguiente página”.
- **Mensajes de error:** algunas respuestas 4xx del backend pueden traer `errors` por campo (ej. validación Laravel); el front suele mostrar solo `message`; en SellView se usa también `errors?.starting_price?.[0]` para el precio.
- **Logout:** el front hace `auth.logout()` y `router.push('/')`; no llama a `POST /logout` del backend para invalidar el token en servidor. El token sigue siendo válido hasta que expire o se revoque desde otro cliente.
- **Ayuda en chat:** no hay ruta ni UI para “?” o “help” que despliegue el mensaje de ayuda del modelo; eso solo está implementado en el backend (campo `helpMessage` cuando la pregunta es "?" o "help").

---

## 11. Resumen ejecutivo

El front es una SPA Vue 3 + Vite + Pinia + Vue Router que cubre registro, login, inicio con carrusel, comprar (ofertas y contraofertas), vender (crear anuncios desde la colección del usuario), mis anuncios (aceptar/declinar bids, cancelar), perfil (álbum con filtro por rareza) y **Asistente** (`/chat`), que llama a `POST /ai/chat` y muestra la respuesta estructurada (helpMessage, rules, cartas similares/recomendadas, etc.). Quedan fuera: exploración del catálogo (`/cards`), facturas y logout vía API.
