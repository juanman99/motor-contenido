# Motor de contenido automático para sitio de afiliados

Genera y publica artículos de reseña/comparativa con IA, casi sin intervención manual.

## Qué automatiza y qué NO automatiza

- SÍ automatiza: escribir el artículo, darle formato HTML, actualizar el índice del sitio,
  subirlo a GitHub y publicarlo (vía Netlify/Vercel conectado al repo).
- NO automatiza: investigar productos reales y decidir cuáles vender. Eso lo metes tú
  en archivos JSON dentro de `cola/`. Automatizar también esa parte produce contenido
  genérico y repetido, que es justo lo que penaliza Google.

## Instalación (una sola vez)

1. Crea una cuenta gratis en GitHub y sube esta carpeta como un repositorio nuevo.
2. Crea una cuenta en https://console.anthropic.com y genera una API key.
   Esto NO es gratis ilimitado: se paga por uso, pero generar un artículo cuesta
   centavos de dólar, no dólares completos.
3. En tu repo de GitHub: Settings → Secrets and variables → Actions → New repository secret.
   Nombre: `ANTHROPIC_API_KEY`. Valor: tu API key.
4. Instala dependencias localmente si quieres probar antes de automatizar:
   ```
   pip install anthropic
   export ANTHROPIC_API_KEY="tu-key-aqui"
   python generador_articulos.py
   ```

## Uso diario

1. Investiga 1-3 productos reales de tu nicho (precio, descripción honesta, link de afiliado).
2. Crea un archivo nuevo en `cola/` copiando el formato de `ejemplo-vendas-boxeo.json`.
3. Sube ese archivo a GitHub (commit + push).
4. El workflow de GitHub Actions (`.github/workflows/generar-contenido.yml`) corre cada
   lunes automáticamente, toma el primer archivo de la cola, genera el artículo y lo
   sube al repo. También puedes correrlo manualmente desde la pestaña "Actions" en GitHub.

## Conectar el sitio para que se publique solo

1. Crea una cuenta gratis en Netlify o Vercel.
2. Conecta tu repositorio de GitHub.
3. Configura la carpeta de publicación como `output`.
4. Cada vez que el bot suba un artículo nuevo a `output/`, el sitio se actualiza solo.

## Antes de monetizar con Amazon Associates

- Necesitas tener tu sitio público con contenido real (no vacío) antes de aplicar.
- Una vez aprobado de forma condicional, tienes 180 días para generar 3 ventas
  calificadas o Amazon cierra la cuenta automáticamente.
- Cada página con enlaces de afiliado debe llevar el aviso:
  "Como Asociado de Amazon, gano por las compras que califican."
  (el script ya lo incluye automáticamente en cada artículo).

## Cambiar de nicho

Solo edita los archivos JSON en `cola/` — el campo `nicho`, `titulo` y `productos`.
El código no necesita ningún cambio para funcionar con otro nicho.
