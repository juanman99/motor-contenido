#!/usr/bin/env python3
"""
Motor de contenido automático para un sitio de afiliados.

Cómo funciona:
1. Pones archivos JSON con productos en la carpeta `cola/` (uno por artículo
   que quieras publicar). Mira `cola/ejemplo-vendas-boxeo.json` como modelo.
2. Cada vez que corres este script (manualmente o vía GitHub Actions), toma
   el PRIMER archivo de la cola, le pide a la API de Claude que escriba el
   artículo, lo guarda como HTML en `output/`, actualiza `output/index.html`
   y mueve el archivo procesado a `publicados/` para no repetirlo.
3. Si la cola está vacía, el script no hace nada (no falla, no publica basura).

Esto es lo único que automatiza: la REDACCIÓN y PUBLICACIÓN.
Investigar productos reales y llenar la cola sigue siendo trabajo tuyo —
automatizar eso también produciría contenido genérico que Google penaliza.
"""

import json
import os
import re
import sys
from datetime import date
from pathlib import Path

import anthropic

API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not API_KEY:
    sys.exit(
        "Error: define la variable de entorno ANTHROPIC_API_KEY antes de ejecutar este script.\n"
        "Consigue una key en https://console.anthropic.com"
    )

client = anthropic.Anthropic(api_key=API_KEY)

BASE_DIR = Path(__file__).parent
COLA_DIR = BASE_DIR / "cola"
PUBLICADOS_DIR = BASE_DIR / "publicados"
OUTPUT_DIR = BASE_DIR / "output"

for carpeta in (COLA_DIR, PUBLICADOS_DIR, OUTPUT_DIR):
    carpeta.mkdir(exist_ok=True)

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{meta_description}">
<style>
  body{{font-family:-apple-system,'Segoe UI',Roboto,sans-serif;max-width:760px;margin:0 auto;padding:40px 20px;line-height:1.65;color:#1a1a1a;}}
  h1{{font-size:1.9rem;margin-bottom:6px;}}
  h2{{font-size:1.35rem;margin-top:2.2em;}}
  table{{width:100%;border-collapse:collapse;margin:1.5em 0;}}
  th,td{{border:1px solid #ddd;padding:10px;text-align:left;font-size:0.92rem;}}
  th{{background:#f4f4f4;}}
  .disclosure{{font-size:0.85rem;color:#555;background:#f7f7f5;padding:12px 16px;border-radius:8px;margin:18px 0 32px;}}
  footer{{margin-top:3em;font-size:0.78rem;color:#888;}}
</style>
</head>
<body>
<h1>{title}</h1>
<p class="disclosure">Como Asociado de Amazon, gano por las compras que califican. Esto no representa un costo extra para ti.</p>
{body}
<footer>Publicado el {fecha}.</footer>
</body>
</html>
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Blog</title>
<style>body{{font-family:sans-serif;max-width:700px;margin:40px auto;padding:0 20px;}} li{{margin-bottom:10px;}}</style>
</head>
<body>
<h1>Últimos artículos</h1>
<ul>
{items}
</ul>
</body>
</html>
"""


def slugify(texto):
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9\s-]", "", texto)
    texto = re.sub(r"\s+", "-", texto).strip("-")
    return texto or "articulo"


def generar_cuerpo_html(nicho, titulo, productos):
    lista_productos = "\n".join(
        f"- {p['nombre']} (${p['precio']}): {p['descripcion']} — enlace: {p['link']}"
        for p in productos
    )
    prompt = f"""Eres un redactor experto en SEO especializado en el nicho de {nicho}.

Escribe el cuerpo de un artículo en español titulado "{titulo}" sobre estos productos:

{lista_productos}

Requisitos:
- Introducción de 2 párrafos que conecte con un problema real del lector.
- Una tabla comparativa (producto, precio, ideal para).
- Una sección por producto: un párrafo, lista de pros, lista de contras.
- Sección final "Cómo elegir" con un párrafo de guía práctica.
- 3 preguntas frecuentes con respuesta breve.
- Tono honesto y directo. No inventes características que no te di arriba.
- Responde SOLO con HTML usando las etiquetas h2, h3, p, table, tr, td, th, ul, li.
  No incluyas las etiquetas html, head ni body, ni la palabra "html" al inicio.
"""
    respuesta = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    return respuesta.content[0].text.strip()


def actualizar_indice():
    archivos = sorted(
        [p for p in OUTPUT_DIR.glob("*.html") if p.name != "index.html"],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    items = []
    for p in archivos:
        contenido = p.read_text(encoding="utf-8")
        match = re.search(r"<title>(.*?)</title>", contenido)
        titulo = match.group(1) if match else p.stem
        items.append(f'  <li><a href="{p.name}">{titulo}</a></li>')
    (OUTPUT_DIR / "index.html").write_text(
        INDEX_TEMPLATE.format(items="\n".join(items)), encoding="utf-8"
    )


def main():
    pendientes = sorted(COLA_DIR.glob("*.json"))
    if not pendientes:
        print("No hay artículos pendientes en la cola. No se hizo nada.")
        return

    archivo = pendientes[0]
    data = json.loads(archivo.read_text(encoding="utf-8"))

    nicho = data["nicho"]
    titulo = data["titulo"]
    productos = data["productos"]

    print(f"Generando artículo: {titulo}")
    cuerpo = generar_cuerpo_html(nicho, titulo, productos)

    pagina = PAGE_TEMPLATE.format(
        title=titulo,
        meta_description=data.get("meta_description", titulo),
        body=cuerpo,
        fecha=date.today().isoformat(),
    )

    slug = slugify(titulo)
    salida = OUTPUT_DIR / f"{slug}.html"
    salida.write_text(pagina, encoding="utf-8")
    print(f"Guardado en: {salida}")

    actualizar_indice()

    archivo.rename(PUBLICADOS_DIR / archivo.name)
    print(f"Movido {archivo.name} a publicados/ (no se repetirá)")


if __name__ == "__main__":
    main()
