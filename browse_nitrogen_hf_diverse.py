#!/usr/bin/env python3
import os
import sys
import ast
import re
import json
import random
import argparse
import textwrap
import tempfile
import subprocess
import shutil
from collections import defaultdict, deque
from datetime import datetime

from datasets import load_dataset


# ============================================================
# UTILIDADES
# ============================================================

def clear_screen():
    os.system("clear")


def normalize(value):
    if value is None:
        return ""
    return str(value)


def parse_list_like(value):
    """
    Convierte strings tipo:
      "['Nitrogen metabolism', 'Nitrate']"
      '["Nitrogen metabolism", "Nitrate"]'
    a lista Python.
    """
    if value is None:
        return []

    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]

    s = str(value).strip()

    if s in ["", "[]", "None", "null", "nan"]:
        return []

    try:
        parsed = ast.literal_eval(s)
        if isinstance(parsed, list):
            return [str(x).strip() for x in parsed if str(x).strip()]
        if isinstance(parsed, tuple):
            return [str(x).strip() for x in parsed if str(x).strip()]
    except Exception:
        pass

    s = s.strip("[]")
    parts = [p.strip().strip("'").strip('"') for p in s.split(",")]
    return [p for p in parts if p]


def is_nitrogen_row(row):
    is_nitrogen = bool(row.get("is_nitrogen", False))
    labels = parse_list_like(row.get("nitrogen_labels"))
    return is_nitrogen or len(labels) > 0


def get_class_key(row, diversify_by="nitrogen_labels"):
    if diversify_by == "source_file":
        return normalize(row.get("source_file")) or "unknown_source"

    if diversify_by == "source_group":
        return normalize(row.get("source_group")) or "unknown_group"

    if diversify_by == "main_field":
        return normalize(row.get("main_field")) or "unknown_field"

    if diversify_by == "bio_labels":
        labels = parse_list_like(row.get("bio_labels"))
        if labels:
            return labels[0]
        return normalize(row.get("main_field")) or "unknown_bio_label"

    labels = parse_list_like(row.get("nitrogen_labels"))
    if labels:
        return labels[0]

    return "unknown_nitrogen_label"


def row_matches(row, keyword=None, label_filter=None, source_filter=None):
    if not is_nitrogen_row(row):
        return False

    text = normalize(row.get("text"))
    nitrogen_labels = normalize(row.get("nitrogen_labels"))
    bio_labels = normalize(row.get("bio_labels"))
    source = normalize(row.get("source_file"))
    main_field = normalize(row.get("main_field"))

    if keyword:
        k = keyword.lower()
        haystack = " ".join([
            text,
            nitrogen_labels,
            bio_labels,
            source,
            main_field,
            normalize(row.get("title")),
            normalize(row.get("doi")),
            normalize(row.get("pmcid")),
        ]).lower()

        if k not in haystack:
            return False

    if label_filter:
        if label_filter.lower() not in nitrogen_labels.lower():
            return False

    if source_filter:
        if source_filter.lower() not in source.lower():
            return False

    return True


def safe_filename(value, max_len=120):
    value = normalize(value)
    value = value.replace("/", "_").replace("\\", "_")
    value = re.sub(r"[^A-Za-z0-9._:-]+", "_", value)
    value = value.strip("._-")

    if not value:
        value = "document"

    return value[:max_len]


def make_dataset(repo_id, split, seed, shuffle_buffer):
    ds = load_dataset(
        repo_id,
        split=split,
        streaming=True,
    )

    ds = ds.shuffle(
        seed=seed,
        buffer_size=shuffle_buffer,
    )

    return iter(ds)


def fill_pool(
    iterator,
    pool,
    target_size,
    keyword=None,
    label_filter=None,
    source_filter=None,
    max_scan=50000,
):
    scanned = 0

    while len(pool) < target_size and scanned < max_scan:
        try:
            row = next(iterator)
        except StopIteration:
            break

        scanned += 1

        if row_matches(
            row,
            keyword=keyword,
            label_filter=label_filter,
            source_filter=source_filter,
        ):
            pool.append(row)

    return scanned


def choose_diverse_row(
    pool,
    diversify_by,
    recent_classes,
    recent_sources,
    rng,
):
    if not pool:
        return None

    grouped = defaultdict(list)

    for idx, row in enumerate(pool):
        class_key = get_class_key(row, diversify_by=diversify_by)
        source_key = normalize(row.get("source_file"))
        grouped[class_key].append((idx, row, source_key))

    recent_classes_set = set(recent_classes)
    recent_sources_set = set(recent_sources)

    # 1. Preferir clase nueva y fuente nueva
    candidate_classes = []

    for class_key, items in grouped.items():
        if class_key in recent_classes_set:
            continue

        has_new_source = any(src not in recent_sources_set for _, _, src in items)

        if has_new_source:
            candidate_classes.append(class_key)

    if candidate_classes:
        chosen_class = rng.choice(candidate_classes)
        items = [
            item for item in grouped[chosen_class]
            if item[2] not in recent_sources_set
        ]
        chosen_idx, chosen_row, source_key = rng.choice(items)
        pool.pop(chosen_idx)
        return chosen_row, chosen_class, source_key

    # 2. Clase nueva, aunque fuente se repita
    candidate_classes = [
        class_key
        for class_key in grouped.keys()
        if class_key not in recent_classes_set
    ]

    if candidate_classes:
        chosen_class = rng.choice(candidate_classes)
        chosen_idx, chosen_row, source_key = rng.choice(grouped[chosen_class])
        pool.pop(chosen_idx)
        return chosen_row, chosen_class, source_key

    # 3. Si todo se repite, elegir al azar
    chosen_idx = rng.randrange(len(pool))
    chosen_row = pool.pop(chosen_idx)
    chosen_class = get_class_key(chosen_row, diversify_by=diversify_by)
    source_key = normalize(chosen_row.get("source_file"))

    return chosen_row, chosen_class, source_key


# ============================================================
# FORMATO COMPLETO
# ============================================================

def build_metadata_markdown(row, class_key):
    lines = [
        "---",
        f"saved_at: {datetime.utcnow().isoformat()}Z",
        f"doc_id: {json.dumps(normalize(row.get('doc_id')), ensure_ascii=False)}",
        f"source_group: {json.dumps(normalize(row.get('source_group')), ensure_ascii=False)}",
        f"source_file: {json.dumps(normalize(row.get('source_file')), ensure_ascii=False)}",
        f"pmcid: {json.dumps(normalize(row.get('pmcid')), ensure_ascii=False)}",
        f"doi: {json.dumps(normalize(row.get('doi')), ensure_ascii=False)}",
        f"year: {json.dumps(normalize(row.get('year')), ensure_ascii=False)}",
        f"main_field: {json.dumps(normalize(row.get('main_field')), ensure_ascii=False)}",
        f"is_biology: {row.get('is_biology')}",
        f"is_nitrogen: {row.get('is_nitrogen')}",
        f"class_key: {json.dumps(normalize(class_key), ensure_ascii=False)}",
        f"text_length_chars: {row.get('text_length_chars')}",
        "---",
        "",
    ]

    return "\n".join(lines)


def build_full_markdown(row, class_key):
    title = normalize(row.get("title")).strip()
    doc_id = normalize(row.get("doc_id")).strip()
    text = normalize(row.get("text"))

    if not title:
        title = doc_id or "Bio-Nitrogen Text"

    md = []

    md.append(build_metadata_markdown(row, class_key))
    md.append(f"# {title}")
    md.append("")
    md.append("## Metadata")
    md.append("")
    md.append(f"- **doc_id:** `{normalize(row.get('doc_id'))}`")
    md.append(f"- **source_group:** `{normalize(row.get('source_group'))}`")
    md.append(f"- **source_file:** `{normalize(row.get('source_file'))}`")
    md.append(f"- **pmcid:** `{normalize(row.get('pmcid'))}`")
    md.append(f"- **doi:** `{normalize(row.get('doi'))}`")
    md.append(f"- **year:** `{normalize(row.get('year'))}`")
    md.append(f"- **main_field:** `{normalize(row.get('main_field'))}`")
    md.append(f"- **is_biology:** `{row.get('is_biology')}`")
    md.append(f"- **is_nitrogen:** `{row.get('is_nitrogen')}`")
    md.append(f"- **class_key:** `{class_key}`")
    md.append(f"- **bio_labels:** `{normalize(row.get('bio_labels'))}`")
    md.append(f"- **nitrogen_labels:** `{normalize(row.get('nitrogen_labels'))}`")
    md.append(f"- **text_length_chars:** `{row.get('text_length_chars')}`")
    md.append("")
    md.append("## Full text")
    md.append("")
    md.append(text)
    md.append("")

    return "\n".join(md)


def build_full_txt(row):
    return normalize(row.get("text"))


def make_output_basename(row, class_key):
    doc_id = normalize(row.get("doc_id"))
    pmcid = normalize(row.get("pmcid"))
    doi = normalize(row.get("doi"))
    year = normalize(row.get("year"))
    source = normalize(row.get("source_file"))

    main_id = doc_id or pmcid or doi or "bio_nitrogen_text"

    parts = [
        safe_filename(year, 20) if year else "",
        safe_filename(class_key, 60),
        safe_filename(source, 60),
        safe_filename(main_id, 80),
    ]

    parts = [p for p in parts if p]
    return "__".join(parts)


def save_full_file(row, class_key, args, fmt="md"):
    save_dir = args.save_dir
    os.makedirs(save_dir, exist_ok=True)

    basename = make_output_basename(row, class_key)

    if fmt == "txt":
        path = os.path.join(save_dir, f"{basename}.txt")
        content = build_full_txt(row)
    else:
        path = os.path.join(save_dir, f"{basename}.md")
        content = build_full_markdown(row, class_key)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\nArchivo guardado: {path}")
    return path


def open_full_text_pager(row, class_key, args):
    """
    Abre el texto completo usando less si está disponible.
    less permite:
      espacio -> avanzar
      b       -> retroceder
      /word   -> buscar
      q       -> salir
    """
    content = build_full_markdown(row, class_key)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".md",
        delete=False,
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    pager = os.environ.get("PAGER", "less")

    try:
        if shutil.which(pager):
            subprocess.run([pager, "-R", tmp_path])
        elif shutil.which("less"):
            subprocess.run(["less", "-R", tmp_path])
        else:
            fallback_paged_print(content, width=args.width)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def fallback_paged_print(content, width=120, page_lines=40):
    clear_screen()

    lines = content.splitlines()
    total = len(lines)
    i = 0

    while i < total:
        clear_screen()
        chunk = lines[i:i + page_lines]

        for line in chunk:
            print(line[:width])

        i += page_lines

        print("\n" + "=" * width)
        print(f"Mostrando líneas {max(1, i - page_lines + 1)}-{min(i, total)} de {total}")
        print("ENTER/ESPACIO: siguiente página | q: salir")
        print("=" * width)

        cmd = input("> ").strip().lower()

        if cmd == "q":
            break


# ============================================================
# IMPRESIÓN DEL PREVIEW
# ============================================================

def print_row(row, index, class_key, keyword, label_filter, source_filter, args):
    clear_screen()

    text = normalize(row.get("text"))
    preview = text[:args.preview_chars]
    width = args.width

    print("=" * width)
    print(f"BIO-NITROGEN RANDOM VIEWER | resultado #{index}")
    print("=" * width)
    print(f"doc_id:          {row.get('doc_id')}")
    print(f"source_group:    {row.get('source_group')}")
    print(f"source_file:     {row.get('source_file')}")
    print(f"pmcid:           {row.get('pmcid')}")
    print(f"doi:             {row.get('doi')}")
    print(f"year:            {row.get('year')}")
    print(f"main_field:      {row.get('main_field')}")
    print(f"is_biology:      {row.get('is_biology')}")
    print(f"is_nitrogen:     {row.get('is_nitrogen')}")
    print(f"class_key:       {class_key}")
    print(f"bio_labels:      {row.get('bio_labels')}")
    print(f"nitrogen_labels: {row.get('nitrogen_labels')}")
    print(f"text_length:     {row.get('text_length_chars')}")
    print("-" * width)

    if keyword:
        print(f"Filtro keyword:  {keyword}")
    if label_filter:
        print(f"Filtro label:    {label_filter}")
    if source_filter:
        print(f"Filtro source:   {source_filter}")

    if keyword or label_filter or source_filter:
        print("-" * width)

    wrapped = textwrap.fill(
        preview,
        width=width,
        replace_whitespace=False,
        drop_whitespace=False,
    )

    print(wrapped)

    if len(text) > args.preview_chars:
        print(
            f"\n[Texto recortado. Se muestran {args.preview_chars} caracteres "
            f"de {len(text)}.]"
        )

    print("=" * width)
    print("ENTER/ESPACIO: siguiente")
    print("e/v/full: ver texto completo | m: guardar .md | t: guardar .txt | f: favorito JSONL")
    print("/ palabra | l etiqueta | src fuente | c clase | r reset | q salir")
    print("=" * width)


def save_favorite(row, class_key, path):
    item = {
        "saved_at": datetime.utcnow().isoformat() + "Z",
        "class_key": class_key,
        "doc_id": row.get("doc_id"),
        "source_group": row.get("source_group"),
        "source_file": row.get("source_file"),
        "pmcid": row.get("pmcid"),
        "doi": row.get("doi"),
        "year": row.get("year"),
        "main_field": row.get("main_field"),
        "is_biology": row.get("is_biology"),
        "is_nitrogen": row.get("is_nitrogen"),
        "bio_labels": row.get("bio_labels"),
        "nitrogen_labels": row.get("nitrogen_labels"),
        "text_length_chars": row.get("text_length_chars"),
        "text_preview": normalize(row.get("text"))[:3000],
    }

    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\nGuardado en favoritos: {path}")


# ============================================================
# ARGUMENTOS
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Interactive random/diverse browser for nitrogen texts from Hugging Face."
    )

    parser.add_argument(
        "--repo-id",
        default="rbnqc/bio-nitrogen",
        help="Hugging Face dataset repo."
    )

    parser.add_argument(
        "--split",
        default="train",
        help="Dataset split. For a single Parquet dataset, Hugging Face usually exposes it as train."
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed."
    )

    parser.add_argument(
        "--shuffle-buffer",
        type=int,
        default=100000,
        help="Streaming shuffle buffer. Larger = more random, but more memory."
    )

    parser.add_argument(
        "--pool-size",
        type=int,
        default=500,
        help="Candidate pool size for local random/diverse selection."
    )

    parser.add_argument(
        "--max-scan",
        type=int,
        default=100000,
        help="Max rows scanned when refilling the candidate pool."
    )

    parser.add_argument(
        "--diversify-by",
        default="nitrogen_labels",
        choices=[
            "nitrogen_labels",
            "bio_labels",
            "source_file",
            "source_group",
            "main_field",
        ],
        help="Field used as class for diversification."
    )

    parser.add_argument(
        "--avoid-last-classes",
        type=int,
        default=8,
        help="Avoid repeating the last N classes."
    )

    parser.add_argument(
        "--avoid-last-sources",
        type=int,
        default=3,
        help="Avoid repeating the last N sources when possible."
    )

    parser.add_argument(
        "--preview-chars",
        type=int,
        default=3500,
        help="Characters shown per preview."
    )

    parser.add_argument(
        "--width",
        type=int,
        default=120,
        help="Terminal text width."
    )

    parser.add_argument(
        "--favorites-path",
        default="nitrogen_favorites.jsonl",
        help="Where favorites are saved."
    )

    parser.add_argument(
        "--save-dir",
        default="saved_nitrogen_texts",
        help="Directory for saved .md and .txt full texts."
    )

    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================

def main():
    args = parse_args()

    rng = random.Random(args.seed)

    keyword = None
    label_filter = None
    source_filter = None

    recent_classes = deque(maxlen=args.avoid_last_classes)
    recent_sources = deque(maxlen=args.avoid_last_sources)

    seed = args.seed

    print("Cargando dataset desde Hugging Face en modo streaming...")
    print(f"Repo: {args.repo_id}")
    print(f"Diversificación por clase: {args.diversify_by}")
    print(f"Directorio de guardado: {args.save_dir}")

    iterator = make_dataset(
        repo_id=args.repo_id,
        split=args.split,
        seed=seed,
        shuffle_buffer=args.shuffle_buffer,
    )

    pool = []
    shown = 0
    current_row = None
    current_class = None

    while True:
        fill_pool(
            iterator=iterator,
            pool=pool,
            target_size=args.pool_size,
            keyword=keyword,
            label_filter=label_filter,
            source_filter=source_filter,
            max_scan=args.max_scan,
        )

        if not pool:
            print("\nNo encontré más resultados con los filtros actuales.")
            print("Usa r para resetear, / palabra para buscar, l etiqueta para filtrar, q para salir.")
            cmd = input("> ").strip()

            if cmd.lower() == "q":
                return

            if cmd.lower() == "r":
                keyword = None
                label_filter = None
                source_filter = None
                recent_classes.clear()
                recent_sources.clear()
                pool.clear()
                seed += 1
                rng.seed(seed)
                iterator = make_dataset(args.repo_id, args.split, seed, args.shuffle_buffer)
                shown = 0
                continue

            if cmd.startswith("/"):
                keyword = cmd[1:].strip() or None
                recent_classes.clear()
                recent_sources.clear()
                pool.clear()
                seed += 1
                rng.seed(seed)
                iterator = make_dataset(args.repo_id, args.split, seed, args.shuffle_buffer)
                shown = 0
                continue

            if cmd.lower().startswith("l "):
                label_filter = cmd[2:].strip() or None
                recent_classes.clear()
                recent_sources.clear()
                pool.clear()
                seed += 1
                rng.seed(seed)
                iterator = make_dataset(args.repo_id, args.split, seed, args.shuffle_buffer)
                shown = 0
                continue

            continue

        chosen = choose_diverse_row(
            pool=pool,
            diversify_by=args.diversify_by,
            recent_classes=recent_classes,
            recent_sources=recent_sources,
            rng=rng,
        )

        if chosen is None:
            continue

        current_row, current_class, current_source = chosen

        recent_classes.append(current_class)
        recent_sources.append(current_source)

        shown += 1

        print_row(
            row=current_row,
            index=shown,
            class_key=current_class,
            keyword=keyword,
            label_filter=label_filter,
            source_filter=source_filter,
            args=args,
        )

        cmd = input("> ").strip()

        if cmd == "" or cmd == " ":
            continue

        cmd_lower = cmd.lower()

        if cmd_lower == "q":
            print("Saliendo.")
            return

        if cmd_lower in ["e", "v", "ver", "expand", "full", "completo"]:
            open_full_text_pager(current_row, current_class, args)
            continue

        if cmd_lower in ["m", "md", "save md", "guardar md"]:
            save_full_file(current_row, current_class, args, fmt="md")
            input("\nENTER para continuar...")
            continue

        if cmd_lower in ["t", "txt", "save txt", "guardar txt"]:
            save_full_file(current_row, current_class, args, fmt="txt")
            input("\nENTER para continuar...")
            continue

        if cmd_lower == "f":
            save_favorite(current_row, current_class, args.favorites_path)
            input("\nENTER para continuar...")
            continue

        if cmd_lower == "r":
            keyword = None
            label_filter = None
            source_filter = None
            recent_classes.clear()
            recent_sources.clear()
            pool.clear()
            seed += 1
            rng.seed(seed)
            iterator = make_dataset(args.repo_id, args.split, seed, args.shuffle_buffer)
            shown = 0
            continue

        if cmd.startswith("/"):
            keyword = cmd[1:].strip() or None
            recent_classes.clear()
            recent_sources.clear()
            pool.clear()
            seed += 1
            rng.seed(seed)
            iterator = make_dataset(args.repo_id, args.split, seed, args.shuffle_buffer)
            shown = 0
            continue

        if cmd_lower.startswith("l "):
            label_filter = cmd[2:].strip() or None
            recent_classes.clear()
            recent_sources.clear()
            pool.clear()
            seed += 1
            rng.seed(seed)
            iterator = make_dataset(args.repo_id, args.split, seed, args.shuffle_buffer)
            shown = 0
            continue

        if cmd_lower.startswith("src "):
            source_filter = cmd[4:].strip() or None
            recent_classes.clear()
            recent_sources.clear()
            pool.clear()
            seed += 1
            rng.seed(seed)
            iterator = make_dataset(args.repo_id, args.split, seed, args.shuffle_buffer)
            shown = 0
            continue

        if cmd_lower.startswith("c "):
            new_class = cmd[2:].strip()

            allowed = [
                "nitrogen_labels",
                "bio_labels",
                "source_file",
                "source_group",
                "main_field",
            ]

            if new_class in allowed:
                args.diversify_by = new_class
                recent_classes.clear()
                recent_sources.clear()
                pool.clear()
                seed += 1
                rng.seed(seed)
                iterator = make_dataset(args.repo_id, args.split, seed, args.shuffle_buffer)
                shown = 0
            else:
                print(f"\nClase no válida. Usa una de: {allowed}")
                input("ENTER para continuar...")

            continue

        print("\nComando no reconocido.")
        input("ENTER para continuar...")


if __name__ == "__main__":
    main()