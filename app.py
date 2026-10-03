"""Conversor local PDF ↔ EPUB con una interfaz mínima."""

from concurrent.futures import ThreadPoolExecutor
from html import escape
from pathlib import Path
import re
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from uuid import uuid4

import pymupdf
from ebooklib import epub


def pdf_a_epub(origen, destino):
    """Extrae bloques de texto y crea un EPUB de lectura adaptable."""
    with pymupdf.open(origen) as documento:
        if documento.needs_pass:
            raise ValueError("El PDF tiene contraseña. Guarda una copia sin protección.")
        libro = epub.EpubBook()
        libro.set_identifier(str(uuid4()))
        libro.set_title(documento.metadata.get("title") or origen.stem)
        libro.set_language("und")  # No presuponemos el idioma del documento.
        if documento.metadata.get("author"):
            libro.add_author(documento.metadata["author"])
        capitulos = []
        for numero, pagina in enumerate(documento, 1):
            parrafos = []
            for bloque in pagina.get_text("blocks", sort=True):
                if bloque[6] != 0:
                    continue
                texto = " ".join(bloque[4].split())
                texto = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", texto)
                if texto:
                    parrafos.append(f"<p>{escape(texto)}</p>")
            if not parrafos:
                raise ValueError(
                    f"La página {numero} no contiene texto extraíble. "
                    "Esta versión no incluye OCR; tampoco convierte páginas solo con imágenes."
                )
            capitulo = epub.EpubHtml(
                title=f"Página {numero}", file_name=f"pagina_{numero}.xhtml", lang="und"
            )
            capitulo.content = "".join(parrafos)
            libro.add_item(capitulo)
            capitulos.append(capitulo)
        if not capitulos:
            raise ValueError("El PDF no contiene páginas.")
        libro.toc = capitulos
        libro.spine = ["nav", *capitulos]
        libro.add_item(epub.EpubNcx())
        libro.add_item(epub.EpubNav())
        epub.write_epub(str(destino), libro, {"raise_exceptions": True})


def epub_a_pdf(origen, destino):
    """Maqueta el EPUB en páginas y genera un PDF con texto seleccionable."""
    with pymupdf.open(origen) as documento:
        documento.layout(width=420, height=595, fontsize=12)
        if not documento.page_count:
            raise ValueError("El EPUB no contiene páginas legibles.")
        with pymupdf.open("pdf", documento.convert_to_pdf()) as pdf:
            pdf.set_toc(documento.get_toc())
            pdf.save(str(destino), garbage=4, deflate=True)


def convertir(origen, destino):
    """Escribe primero un temporal para no dejar resultados incompletos."""
    if origen.resolve() == destino.resolve():
        raise ValueError("El destino debe ser distinto del archivo original.")
    funcion = {".pdf": pdf_a_epub, ".epub": epub_a_pdf}.get(origen.suffix.lower())
    if funcion is None:
        raise ValueError("Selecciona un archivo PDF o EPUB.")
    with tempfile.NamedTemporaryFile(dir=destino.parent, suffix=destino.suffix, delete=False) as archivo:
        temporal = Path(archivo.name)
    try:
        funcion(origen, temporal)
        temporal.replace(destino)
    finally:
        temporal.unlink(missing_ok=True)


class Aplicacion:
    def __init__(self, ventana):
        self.ventana = ventana
        self.origen = None
        self.tarea = None
        self.ejecutor = ThreadPoolExecutor(max_workers=1)
        ventana.title("Conversor de archivos")
        ventana.geometry("600x380")
        ventana.minsize(540, 380)
        ventana.protocol("WM_DELETE_WINDOW", self.cerrar)
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("TFrame", background="#f5f7fb")
        estilo.configure("TLabel", background="#f5f7fb", font=("Segoe UI", 11))
        estilo.configure("Titulo.TLabel", font=("Segoe UI", 22, "bold"))
        estilo.configure("TButton", font=("Segoe UI", 11), padding=10)
        marco = ttk.Frame(ventana, padding=28)
        marco.pack(fill="both", expand=True)
        ttk.Label(marco, text="Conversor de archivos", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(marco, text="PDF ↔ EPUB · Conversión local").pack(anchor="w", pady=(4, 20))
        self.nombre = tk.StringVar(value="Selecciona un PDF o EPUB para empezar.")
        ttk.Label(marco, textvariable=self.nombre, wraplength=480).pack(anchor="w", pady=(0, 12))
        self.elegir = ttk.Button(marco, text="Seleccionar archivo", command=self.seleccionar)
        self.elegir.pack(fill="x")
        self.boton = ttk.Button(marco, text="Convertir y guardar", command=self.iniciar, state="disabled")
        self.boton.pack(fill="x", pady=8)
        self.estado = tk.StringVar(value="PDF → EPUB: solo texto, sin imágenes ni OCR.")
        ttk.Label(marco, textvariable=self.estado, wraplength=480).pack(anchor="w", pady=8)
        self.progreso = ttk.Progressbar(marco, mode="indeterminate")
        self.progreso.pack(fill="x")

    def seleccionar(self):
        ruta = filedialog.askopenfilename(filetypes=[("PDF y EPUB", "*.pdf *.epub")])
        if ruta:
            self.origen = Path(ruta)
            self.nombre.set(self.origen.name)
            self.boton.configure(state="normal")

    def iniciar(self):
        extension = ".epub" if self.origen.suffix.lower() == ".pdf" else ".pdf"
        ruta = filedialog.asksaveasfilename(
            initialdir=str(self.origen.parent), initialfile=self.origen.stem + extension,
            defaultextension=extension, filetypes=[(extension[1:].upper(), "*" + extension)],
        )
        if not ruta:
            return
        destino = Path(ruta)
        if destino.suffix.lower() != extension:
            messagebox.showerror("Formato incorrecto", f"El archivo debe terminar en {extension}.")
            return
        self.boton.configure(state="disabled")
        self.elegir.configure(state="disabled")
        self.estado.set("Convirtiendo…")
        self.progreso.start(12)
        self.tarea = self.ejecutor.submit(convertir, self.origen, destino)
        self.ventana.after(150, lambda: self.comprobar(destino))

    def comprobar(self, destino):
        # La ventana se actualiza desde su hilo; la conversión trabaja en segundo plano.
        if not self.tarea.done():
            self.ventana.after(150, lambda: self.comprobar(destino))
            return
        self.progreso.stop()
        self.boton.configure(state="normal")
        self.elegir.configure(state="normal")
        try:
            self.tarea.result()
        except Exception as error:
            self.estado.set("No se pudo convertir el archivo.")
            messagebox.showerror("Error de conversión", str(error))
        else:
            self.estado.set("Conversión completada.")
            messagebox.showinfo("Archivo guardado", f"Guardado en:\n{destino}")

    def cerrar(self):
        if self.tarea and not self.tarea.done():
            messagebox.showinfo("Conversión en curso", "Espera a que termine antes de cerrar.")
            return
        self.ejecutor.shutdown(wait=False)
        self.ventana.destroy()


if __name__ == "__main__":
    raiz = tk.Tk()
    Aplicacion(raiz)
    raiz.mainloop()
