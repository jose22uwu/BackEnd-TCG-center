# Cursor: reglas, comandos y skills

Carpetas para que el asistente use lo que definas en el proyecto.

| Carpeta      | Uso |
|-------------|-----|
| **rules/**  | Reglas del proyecto: archivos `.mdc` o `.md` con convenciones, estándares de código, arquitectura o instrucciones que el AI debe seguir al trabajar aquí. |
| **commands/** | Comandos personalizados o instrucciones reutilizables que quieras que el AI ejecute (scripts, flujos, plantillas). |
| **skills/** | Skills (habilidades) propias del proyecto: procedimientos, patrones o capacidades que extienden lo que el asistente puede hacer en este repo. |

**Skill de visión del proyecto:** `skills/pokemon-tcg-app-vision` — define el núcleo de la app (full stack, subastas Pokemon TCG, ver cartas, perfiles estéticos). Se aplica en todo el proyecto vía la regla `rules/project-vision.mdc`.

Puedes añadir archivos en cada carpeta; Cursor los tendrá en cuenta según su configuración.
