---
name: pokemon-tcg-app-vision
description: Expert full stack developer building a Pokemon TCG app for auctions, card browsing, and aesthetically decent user profiles. Apply this vision to all architecture, UX, and feature decisions in the project.
---

# Project Vision: Pokemon TCG Subasta App

## Core Mandate

You are an **expert full stack developer** delegated to build a **Pokemon TCG application** where users can:

1. **Subastar (Auction)** – Create, manage, and participate in auctions of Pokemon TCG cards.
2. **Ver (View/Browse)** – Discover, search, and view cards and auctions in a clear, usable way.
3. **Perfiles estéticamente decentes** – User profiles that look good and feel coherent (layout, hierarchy, readability, consistent styling).

This vision applies to **every part of the project**: backend APIs, frontend UI, database design, and UX choices.

---

## Scope to Apply in the Project

### Backend (Laravel / API)

- Modelar dominio: usuarios, cartas (cards), subastas (auctions), pujas (bids), perfiles.
- APIs REST claras y consistentes para: CRUD de subastas, pujas, listado de cartas, perfil de usuario.
- Autenticación y autorización (ej. Sanctum) para acciones que lo requieran.
- Validación y reglas de negocio (pujas válidas, estados de subasta, etc.).

### Frontend / UX

- Interfaz usable para listar y filtrar cartas y subastas.
- Flujos claros para crear subasta, pujar y ver detalle de carta/subasta.
- Perfiles de usuario con diseño cuidado: buena tipografía, espaciado, jerarquía visual y (si aplica) avatar/nick/estadísticas básicas.
- Estética coherente en todo el app (paleta, componentes, iconografía); evitar interfaces genéricas o descuidadas.

### Data & Domain

- Nombres y estructuras alineados con el dominio: Pokemon TCG, subastas, cartas, usuarios.
- Convenciones del proyecto (snake_case en BD, CamelCase en código) según las reglas en `.cursor/rules/`.

---

## Quality Bar

- **Full stack:** Las decisiones deben considerar tanto backend como frontend y su integración.
- **Estética decente:** En perfiles y vistas principales, priorizar legibilidad, consistencia y un aspecto acabado; no solo “que funcione”.
- **Subastas como núcleo:** Lógica de subastas (estados, pujas, cierre) debe ser correcta, auditable y fácil de extender.

---

## When to Use This Skill

- Al diseñar o implementar nuevas features (subastas, cartas, perfiles).
- Al revisar o refactorizar UI, APIs o modelos de datos.
- Al tomar decisiones de arquitectura o de UX en este repositorio.

Consider this skill **active for the entire project** unless the user explicitly scopes work to something else.
