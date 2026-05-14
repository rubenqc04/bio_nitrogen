# Bio-Nitrogen HF Diverse Browser

Visor interactivo por terminal para explorar textos relacionados con biología y nitrógeno desde Hugging Face.

Repositorio usado por defecto:

```text
rbnqc/bio-nitrogen
```

Este visor permite navegar de forma aleatoria y diversa por textos científicos relacionados con nitrógeno, evitando repetir constantemente ejemplos de la misma clase, etiqueta o fuente. Además, permite abrir textos completos, guardarlos como Markdown, guardarlos como TXT y marcar favoritos para revisión posterior.

---

## Objetivo

El objetivo del script es facilitar la revisión manual del dataset `rbnqc/bio-nitrogen`, especialmente para auditar textos relacionados con nitrógeno.

Permite:

- Consultar textos desde Hugging Face.
- Usar `streaming=True` para no descargar todo el dataset completo.
- Mostrar previews de textos largos.
- Elegir ejemplos de forma aleatoria.
- Diversificar resultados por etiquetas de nitrógeno, etiquetas biológicas, fuente o campo científico.
- Evitar ver siempre textos de la misma clase.
- Buscar por palabra clave.
- Filtrar por etiqueta de nitrógeno.
- Filtrar por fuente.
- Leer el texto completo.
- Guardar textos completos en `.md`.
- Guardar textos completos en `.txt`.
- Guardar favoritos resumidos en `.jsonl`.

---

## Archivo principal

```bash
browse_nitrogen_hf_diverse.py
```

---

## Dataset usado

Por defecto, el script usa:

```text
rbnqc/bio-nitrogen
```

Split usado:

```text
train
```

---

## Instalación

Instalar dependencias:

```bash
pip install -U datasets huggingface_hub
```

Si el dataset está privado, iniciar sesión:

```bash
hf auth login
```

También se recomienda tener disponible `less`, ya que el script lo usa para abrir textos completos:

```bash
sudo apt-get install less
```

En la mayoría de servidores Linux ya viene instalado.

---

## Uso básico

```bash
python3 -u browse_nitrogen_hf_diverse.py
```

---

## Uso recomendado

Para revisar textos con buena aleatoriedad y diversidad:

```bash
python3 -u browse_nitrogen_hf_diverse.py \
  --diversify-by nitrogen_labels \
  --shuffle-buffer 100000 \
  --pool-size 500 \
  --avoid-last-classes 8 \
  --avoid-last-sources 3
```

Esta configuración intenta evitar que se repitan las mismas etiquetas de nitrógeno y las mismas fuentes en resultados consecutivos.

---

## Controles dentro del visor

| Comando | Acción |
|---|---|
| `ENTER` | Mostrar siguiente texto |
| `ESPACIO` | Mostrar siguiente texto |
| `e` | Expandir / abrir texto completo |
| `v` | Ver texto completo |
| `full` | Ver texto completo |
| `completo` | Ver texto completo |
| `m` | Guardar texto completo como Markdown `.md` |
| `md` | Guardar texto completo como Markdown `.md` |
| `t` | Guardar texto completo como `.txt` |
| `txt` | Guardar texto completo como `.txt` |
| `f` | Guardar favorito resumido en JSONL |
| `/ palabra` | Buscar textos que contengan una palabra |
| `l etiqueta` | Filtrar por etiqueta de nitrógeno |
| `src fuente` | Filtrar por fuente |
| `c clase` | Cambiar criterio de diversificación |
| `r` | Resetear filtros |
| `q` | Salir |

---

## Leer texto completo

Cuando un texto te interese, presiona:

```text
e
```

o:

```text
v
```

Esto abre el texto completo usando `less`.

Dentro de `less` puedes usar:

| Tecla | Acción |
|---|---|
| `ESPACIO` | Avanzar una página |
| `b` | Retroceder una página |
| `/palabra` | Buscar una palabra |
| `n` | Ir al siguiente resultado de búsqueda |
| `q` | Salir y volver al visor |

Ejemplo:

```text
e
```

Luego, dentro de `less`, puedes buscar una palabra:

```text
/nitrate
```

Para salir del texto completo y volver al visor:

```text
q
```

---

## Guardar texto completo en Markdown

Para guardar el texto completo con metadata:

```text
m
```

El archivo se guarda por defecto en:

```text
saved_nitrogen_texts/
```

El archivo `.md` incluye:

- Bloque YAML con metadata.
- Título del documento.
- `doc_id`.
- Fuente.
- DOI.
- PMCID.
- Año.
- Campo científico.
- Etiquetas biológicas.
- Etiquetas de nitrógeno.
- Largo del texto.
- Texto completo.

Este es el formato recomendado para auditoría manual.

---

## Guardar texto completo en TXT

Para guardar solo el texto plano completo:

```text
t
```

El archivo se guarda por defecto en:

```text
saved_nitrogen_texts/
```

El `.txt` es útil si después quieres usar el texto en otro pipeline, por ejemplo:

- extracción de entidades,
- análisis de calidad,
- evaluación con modelos,
- indexación,
- limpieza adicional,
- revisión externa.

---

## Guardar favorito resumido

Para guardar un registro como favorito resumido:

```text
f
```

Esto guarda una línea JSON en:

```text
nitrogen_favorites.jsonl
```

Ejemplo de estructura:

```json
{
  "saved_at": "2026-05-14T00:00:00Z",
  "class_key": "Nitrogen fixation",
  "doc_id": "pmc:PMC123456",
  "source_group": "pmc_biology",
  "source_file": "pmc_biology_texts_plus_metadata",
  "pmcid": "PMC123456",
  "doi": "10.xxxx/example",
  "year": "2020",
  "main_field": "Biology",
  "is_biology": true,
  "is_nitrogen": true,
  "bio_labels": "...",
  "nitrogen_labels": "...",
  "text_length_chars": 45231,
  "text_preview": "..."
}
```

---

## Diferencia entre `e`, `m`, `t` y `f`

| Comando | Salida | Uso recomendado |
|---|---|---|
| `e` / `v` | Abre el texto completo en terminal | Leer sin guardar |
| `m` | Archivo `.md` completo | Auditoría manual con metadata |
| `t` | Archivo `.txt` completo | Procesamiento posterior |
| `f` | Registro JSONL resumido | Marcar ejemplos interesantes |

Recomendación principal: usar `m` para guardar ejemplos importantes, porque Markdown conserva tanto el texto completo como la metadata.

---

## Buscar por palabra clave

Dentro del visor, puedes escribir:

```text
/ nitrate
```

Otros ejemplos:

```text
/ nitrogen
/ ammonia
/ ammonium
/ denitrification
/ nitrification
/ nitrogen fixation
/ nitric oxide
/ rhizosphere
/ eutrophication
/ nitrogen metabolism
```

El visor reiniciará la búsqueda y mostrará solo textos que contengan esa palabra o frase en el texto o en su metadata asociada.

---

## Filtrar por etiqueta de nitrógeno

Para filtrar por una etiqueta específica:

```text
l Nitrogen fixation
```

Otros ejemplos:

```text
l Nitrate
l Ammonia
l Ammonium
l Denitrification
l Nitrification
l Nitric oxide
l Nitrogen metabolism
l Nitrogen cycle
```

---

## Filtrar por fuente

Para mostrar solo textos de una fuente específica:

```text
src pmc
```

Otros ejemplos:

```text
src plos
src biorxiv
src uniprotkb
src scielo
src elife
src go
```

---

## Cambiar criterio de diversificación

El visor intenta no repetir textos de la misma clase. Por defecto, la clase se define usando:

```text
nitrogen_labels
```

Puedes cambiar el criterio dentro del visor con:

```text
c source_file
```

Opciones disponibles:

```text
nitrogen_labels
bio_labels
source_file
source_group
main_field
```

Ejemplos:

```text
c nitrogen_labels
c bio_labels
c source_file
c source_group
c main_field
```

---

## Argumentos disponibles

Puedes ver todos los argumentos con:

```bash
python3 -u browse_nitrogen_hf_diverse.py --help
```

Argumentos principales:

| Argumento | Descripción | Valor por defecto |
|---|---|---|
| `--repo-id` | Repositorio Hugging Face | `rbnqc/bio-nitrogen` |
| `--split` | Split del dataset | `train` |
| `--seed` | Semilla aleatoria | `42` |
| `--shuffle-buffer` | Buffer de mezcla en streaming | `100000` |
| `--pool-size` | Bolsa local de candidatos | `500` |
| `--max-scan` | Máximo de filas escaneadas al rellenar la bolsa | `100000` |
| `--diversify-by` | Campo usado para diversificar | `nitrogen_labels` |
| `--avoid-last-classes` | Número de clases recientes a evitar | `8` |
| `--avoid-last-sources` | Número de fuentes recientes a evitar | `3` |
| `--preview-chars` | Caracteres mostrados en preview | `3500` |
| `--width` | Ancho visual en terminal | `120` |
| `--favorites-path` | Archivo JSONL de favoritos | `nitrogen_favorites.jsonl` |
| `--save-dir` | Carpeta para guardar `.md` y `.txt` | `saved_nitrogen_texts` |

---

## Ejemplos de ejecución

### Exploración general

```bash
python3 -u browse_nitrogen_hf_diverse.py
```

### Exploración con mayor diversidad

```bash
python3 -u browse_nitrogen_hf_diverse.py \
  --shuffle-buffer 100000 \
  --pool-size 500 \
  --avoid-last-classes 8 \
  --avoid-last-sources 3
```

### Diversificar por etiquetas de nitrógeno

```bash
python3 -u browse_nitrogen_hf_diverse.py \
  --diversify-by nitrogen_labels
```

### Diversificar por fuente

```bash
python3 -u browse_nitrogen_hf_diverse.py \
  --diversify-by source_file
```

### Diversificar por etiquetas biológicas

```bash
python3 -u browse_nitrogen_hf_diverse.py \
  --diversify-by bio_labels
```

### Mostrar previews más largos

```bash
python3 -u browse_nitrogen_hf_diverse.py \
  --preview-chars 8000
```

### Guardar textos en otra carpeta

```bash
python3 -u browse_nitrogen_hf_diverse.py \
  --save-dir /workspace1/rubenqc/.ibio/articulos/revision_nitrogen_texts
```

---

## Estructura de salida

Después de usar el visor, puedes obtener una estructura como:

```text
saved_nitrogen_texts/
├── 2020__Nitrogen_fixation__pmc_biology_texts_plus_metadata__pmc:PMC123456.md
├── 2018__Nitrate__plos_text_metadata_unified.parquet__plos:abc123.md
├── 2021__Nitric_oxide__pmc_biology_texts_plus_metadata__pmc:PMC789101.txt
└── ...
```

Además, los favoritos se guardan en:

```text
nitrogen_favorites.jsonl
```

---

## Formato del archivo Markdown guardado

Cada archivo `.md` comienza con metadata en formato YAML:

```yaml
---
saved_at: 2026-05-14T00:00:00Z
doc_id: "pmc:PMC123456"
source_group: "pmc_biology"
source_file: "pmc_biology_texts_plus_metadata"
pmcid: "PMC123456"
doi: "10.xxxx/example"
year: "2020"
main_field: "Biology"
is_biology: True
is_nitrogen: True
class_key: "Nitrogen fixation"
text_length_chars: 45231
---
```

Luego incluye una sección de metadata legible y finalmente el texto completo:

```markdown
## Metadata

- **doc_id:** `pmc:PMC123456`
- **source_group:** `pmc_biology`
- **source_file:** `pmc_biology_texts_plus_metadata`
- **pmcid:** `PMC123456`
- **doi:** `10.xxxx/example`
- **year:** `2020`
- **main_field:** `Biology`
- **is_biology:** `True`
- **is_nitrogen:** `True`
- **class_key:** `Nitrogen fixation`
- **bio_labels:** `...`
- **nitrogen_labels:** `...`
- **text_length_chars:** `45231`

## Full text

Texto completo del artículo...
```

---

## Cómo funciona internamente

El script realiza los siguientes pasos:

1. Carga el dataset desde Hugging Face usando `streaming=True`.
2. Mezcla el flujo usando `shuffle()` con un buffer configurable.
3. Filtra textos relacionados con nitrógeno usando `is_nitrogen=True` o `nitrogen_labels` no vacío.
4. Llena una bolsa local de candidatos.
5. Selecciona ejemplos aleatorios.
6. Intenta evitar clases y fuentes recientemente mostradas.
7. Muestra un preview del texto.
8. Permite expandir, guardar, filtrar o continuar.

---

## Flujo recomendado de revisión

```text
1. Ejecutar el visor.
2. Revisar el preview.
3. Si el texto parece interesante, presionar e para verlo completo.
4. Dentro de less, buscar palabras con /palabra.
5. Salir con q.
6. Si el ejemplo es útil, presionar m para guardarlo como Markdown.
7. Si solo quieres marcarlo, presionar f.
8. Continuar con ENTER.
```

---

## Comando recomendado para auditoría

```bash
python3 -u browse_nitrogen_hf_diverse.py \
  --diversify-by nitrogen_labels \
  --shuffle-buffer 100000 \
  --pool-size 500 \
  --avoid-last-classes 8 \
  --avoid-last-sources 3 \
  --preview-chars 3500 \
  --save-dir saved_nitrogen_texts
```

---

## Posibles problemas

### El dataset no carga

Verifica que tengas acceso al repositorio:

```bash
hf auth login
```

Prueba una carga mínima:

```python
from datasets import load_dataset

ds = load_dataset("rbnqc/bio-nitrogen", split="train", streaming=True)
print(next(iter(ds)))
```

### Aparecen textos muy repetidos

Aumenta el buffer y la bolsa:

```bash
python3 -u browse_nitrogen_hf_diverse.py \
  --shuffle-buffer 200000 \
  --pool-size 1000 \
  --avoid-last-classes 10 \
  --avoid-last-sources 5
```

### El visor demora en encontrar resultados

Puede ocurrir si el filtro es muy específico. Si demora mucho, prueba con una búsqueda más amplia:

```text
/ nitrogen
```

o resetea filtros:

```text
r
```

### No se abre `less`

Instalar `less`:

```bash
sudo apt-get install less
```

Si no está disponible, el script usa un visor simple por páginas como respaldo.

### Los archivos guardados tienen nombres muy largos

El script genera nombres a partir de metadata como año, clase, fuente y `doc_id`. Si el nombre resulta largo, puedes renombrar manualmente el archivo guardado o cambiar el valor de `safe_filename()` dentro del código.

---

## Archivos generados

| Archivo / carpeta | Descripción |
|---|---|
| `saved_nitrogen_texts/` | Carpeta con textos completos guardados en `.md` o `.txt` |
| `nitrogen_favorites.jsonl` | Favoritos resumidos |
| Archivos `.md` | Texto completo + metadata |
| Archivos `.txt` | Texto completo plano |

---

## Uso de los archivos guardados

Los archivos `.md` sirven para:

- auditoría manual,
- revisión de etiquetas,
- selección de ejemplos buenos,
- documentación,
- revisión científica,
- preparación de subconjuntos curados.

Los archivos `.txt` sirven para:

- procesamiento automático,
- extracción de entidades,
- análisis lingüístico,
- evaluación con modelos,
- indexación,
- pipelines externos.

El archivo `nitrogen_favorites.jsonl` sirve para:

- registrar ejemplos interesantes,
- construir una lista rápida de revisión,
- auditar errores,
- seleccionar candidatos para datasets curados.

---

## Nota final

Este visor no modifica el dataset alojado en Hugging Face. Solo lee ejemplos desde el repositorio remoto y permite guardar localmente textos completos o favoritos para revisión posterior.

La opción recomendada para guardar ejemplos importantes es Markdown (`m`), porque conserva metadata y texto completo en un formato fácil de leer, versionar y auditar.
