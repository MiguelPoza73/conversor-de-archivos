# Conversor de archivos

Aplicación de escritorio en Python para convertir **PDF a EPUB** y **EPUB a PDF**. Interfaz sencilla en español, sin servidor, cuentas ni servicios externos. Los archivos se procesan en tu ordenador.

## Preparar el proyecto en VS Code

1. Instala Python 3.13 desde https://www.python.org/downloads/ con Tcl/Tk y la opción de añadir Python al PATH.
2. Instala Visual Studio Code y la extensión **Python** de Microsoft.
3. Abre esta carpeta (`conversor-de-archivos`) en VS Code.
4. En **Terminal → Nueva terminal**, usando PowerShell, ejecuta:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

No necesitas activar el entorno ni cambiar la política de ejecución de PowerShell. Si Windows no reconoce `python`, prueba `py -3.13` en el primer comando.

En VS Code, pulsa `Ctrl+Shift+P`, elige **Python: Select Interpreter** y selecciona `.venv\Scripts\python.exe`.

## Manual de uso

1. Pulsa **Seleccionar archivo** y abre un PDF o EPUB.
2. Pulsa **Convertir y guardar**. El formato de salida se elige automáticamente: PDF → EPUB o EPUB → PDF.
3. Elige el nombre y la carpeta de destino. El diálogo solicita confirmación si el archivo ya existe.
4. Espera al mensaje de finalización. La ventana sigue respondiendo durante la conversión.

El original se conserva. Si la conversión falla, se muestra el error y no se publica un archivo incompleto ni se reemplaza el destino existente.

### Leer el EPUB en Kindle

Envía el EPUB mediante [Send to Kindle](https://www.amazon.com/sendtokindle), en un dispositivo compatible con ese servicio. La aplicación solo genera el archivo; no lo envía automáticamente. Un EPUB no está pensado para copiarlo directamente por USB a un Kindle.

## Crear y distribuir el ejecutable de Windows

Desde la carpeta del proyecto, con el entorno preparado:

```powershell
.\.venv\Scripts\python.exe -m pip install "pyinstaller>=6.16,<7"
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name ConversorDeArchivos app.py
```

El resultado será **`dist\ConversorDeArchivos.exe`**. Puedes copiar ese único archivo a otro equipo Windows de arquitectura compatible; el destinatario no necesita Python. El primer arranque puede tardar mientras se extraen las dependencias temporales. El ejecutable se genera en Windows; no es un JAR.

Para publicarlo en GitHub, sube el código y este README al repositorio. Adjunta el `.exe` a una **Release**; no subas `.venv`, `build` ni `dist` al código fuente. Si el repositorio contiene varios proyectos, este manual se muestra al abrir la carpeta del conversor; en un repositorio dedicado aparecerá en su portada.

## Alcance de esta primera versión

- **PDF → EPUB:** extrae bloques de texto, une sus líneas y crea una sección por página. El lector puede adaptar el tamaño de letra. No conserva imágenes, tablas, fuentes ni la maquetación original; pueden aparecer encabezados repetidos o un orden de lectura imperfecto en documentos con columnas.
- No incluye OCR. Omite las imágenes y las páginas sin texto extraíble (escaneadas o en blanco) y continúa con el resto. Al terminar muestra cuántas páginas se convirtieron y cuántas se omitieron. En páginas mixtas conserva solo el texto extraíble. Si todo el PDF carece de texto extraíble, muestra un error y no genera un EPUB vacío.
- **EPUB → PDF:** pagina el libro aproximadamente en A5, con letra base de 12 puntos. El resultado depende del contenido y CSS que soporte el motor; no garantiza reproducir toda la presentación del EPUB.
- No admite PDF con contraseña ni libros con DRM. No elimina protecciones.
- Sin procesamiento por lotes, edición ni pruebas unitarias en esta versión.

## Cómo seguir el código

Todo está en **`app.py`**, en este orden:

1. `pdf_a_epub`: extracción de texto y creación del libro.
2. `epub_a_pdf`: maquetación y exportación a PDF.
3. `convertir`: escritura temporal y guardado del resultado.
4. `Aplicacion`: selección, guardado y mensajes de la interfaz Tkinter.

`requirements.txt` contiene las dos dependencias de conversión. Tkinter viene con la instalación estándar de Python para Windows. PyInstaller solo se necesita para generar el ejecutable.

Documentación: [PyMuPDF](https://pymupdf.readthedocs.io/en/latest/document.html), [EbookLib](https://docs.sourcefabric.org/projects/ebooklib/en/latest/tutorial.html) y [PyInstaller](https://pyinstaller.org/en/stable/usage.html).

Antes de distribuir una versión, revisa las licencias de las dependencias: [PyMuPDF](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright) y [EbookLib](https://github.com/aerkalov/ebooklib#license).
