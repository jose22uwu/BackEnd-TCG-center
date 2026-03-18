# Chat IA: fallo WSL 0x8007072c

Cuando el asistente devuelve "AI process failed" con el código **Wsl/Service/0x8007072c** ("La llamada RPC contiene un identificador que difiere del tipo de identificador declarado"), el origen está en cómo Windows lanza WSL desde PHP, no en el script ni en las comillas.

## Causas probables

1. **Directorio de trabajo**  
   PHP (p. ej. con `php artisan serve`) puede tener el CWD en `public/`. Al lanzar `wsl.exe` desde ese contexto, el subsistema a veces falla con ese RPC. Por eso el controlador fuerza **CWD = raíz del proyecto** al crear el proceso.

2. **Servicio WSL / .wslconfig**  
   El error suele relacionarse con el servicio `wslservice.exe` o con opciones inválidas en `%USERPROFILE%\.wslconfig` (p. ej. parámetros no reconocidos o mal formados). Solución: revisar o vaciar `.wslconfig` y reiniciar WSL.

3. **Contexto de proceso**  
   Lanzar WSL desde un proceso que no es una consola interactiva (p. ej. PHP vía servidor web o artisan) puede provocar el fallo en algunas versiones de Windows/WSL.

## Qué hace ya el código

- **CWD en la raíz del proyecto** al ejecutar el proceso WSL.
- **Fallback con Python en Windows**: si WSL falla con exit code -1 y el mensaje contiene "0x8007072c", se intenta ejecutar el chatbot con **Python en Windows** (`python` o `py -3` desde la raíz del proyecto). Así el chat puede funcionar aunque WSL siga fallando.

## Requisitos para el fallback en Windows

- **Recomendado: venv en el proyecto**  
  El `python.exe` de WindowsApps (o el de la terminal) puede no ver los mismos paquetes cuando lo ejecuta PHP (proceso no interactivo), por eso aparece `ModuleNotFoundError: No module named 'numpy'` desde el front aunque por consola funcione. Para evitarlo, crea un venv local y deja que el backend lo use:
  1. En PowerShell, desde la raíz del proyecto: `.\ai model\setup_venv_windows.ps1`
  2. El script crea `ai model/.venv-windows`, instala las dependencias de `requirements.txt` y el controlador usará ese Python automáticamente (tiene prioridad sobre `AI_PYTHON_PATH`).
- **Alternativa:** Python 3 instalado y ruta en `.env`:
  ```env
  AI_PYTHON_PATH=C:\ruta\completa\a\python.exe
  ```
  Ese Python debe tener instaladas las dependencias del chatbot (numpy, mysql-connector-python, python-dotenv, etc.). Si usas el de WindowsApps, puede que desde PHP no vea los paquetes; en ese caso usa el venv anterior.
- MySQL accesible en `127.0.0.1` desde Windows (el script usa el `.env` del proyecto, con `DB_HOST=127.0.0.1` en Windows).

## Si quieres seguir usando WSL

1. Ejecutar `wsl --shutdown` y volver a abrir la distro (p. ej. Ubuntu).
2. Revisar `C:\Users\<tu_usuario>\.wslconfig`: quitar opciones raras o dejar solo lo necesario; reiniciar WSL después de cambiar.
3. Actualizar WSL: `wsl --update`.
4. Reiniciar el servicio (como administrador): `sc stop wslservice` y luego `sc start wslservice`.

Cuando WSL funcione de nuevo, el chat usará WSL (con GPU si está configurado); si no, seguirá usando el fallback con Python en Windows.
