import argparse
import json
import os
import re
import zipfile
from pathlib import Path


def should_translate_string(s: str) -> bool:
    if not s:
        return False
    # Avoid translating obvious IDs/keys.
    if s.startswith("cobblemon:") or s.startswith("minecraft:") or s.startswith("johto:"):
        return False
    if s.startswith("q.") or "q." in s:
        return False
    if s.startswith("/") or s.startswith("#"):
        return False
    if s.strip() in {"", "true", "false", "null"}:
        return False
    # Keep short tokens like enum values.
    if re.fullmatch(r"[A-Za-z0-9_\-.:/]+", s) and len(s) <= 24:
        return False
    return True


def load_overrides(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def make_translator():
    # Import argostranslate lazily; fail fast if not installed.
    from argostranslate import translate

    def t(s: str) -> str:
        return translate.translate(s, "en", "fr")

    return t


def translate_obj(obj, translate_fn):
    if isinstance(obj, str):
        if should_translate_string(obj):
            try:
                return translate_fn(obj)
            except Exception:
                return obj
        return obj
    if isinstance(obj, list):
        return [translate_obj(x, translate_fn) for x in obj]
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            # Only translate known user-facing keys.
            if k in ("lines", "text", "title", "subtitle"):
                out[k] = translate_obj(v, translate_fn)
            elif k == "name":
                # Do not translate speaker names by default (Pokemon names/localization).
                out[k] = v
            else:
                out[k] = translate_obj(v, translate_fn) if isinstance(v, (list, dict)) else v
        return out
    return obj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--johto-zip", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--overrides-json", default="")
    ap.add_argument("--include-mcfunction-tellraw", action="store_true")
    ap.add_argument("--johto-fixes-dir", default="")
    args = ap.parse_args()

    johto_zip = Path(args.johto_zip).resolve()
    out_dir = Path(args.out_dir).resolve()
    overrides_path = Path(args.overrides_json).resolve() if args.overrides_json else None
    fixes_dir = Path(args.johto_fixes_dir).resolve() if args.johto_fixes_dir else None

    overrides = load_overrides(overrides_path) if overrides_path else {}

    translate_fn = make_translator()

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "pack.mcmeta").write_text(
        json.dumps(
            {
                "pack": {
                    "pack_format": 48,
                    "description": "Cobblemon Johto (FR auto)",
                }
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    z = zipfile.ZipFile(str(johto_zip))

    # 1) Translate all dialogue JSON files.
    dlg_prefix = "data/cobblemon/dialogues/"
    dialogue_files = [n for n in z.namelist() if n.startswith(dlg_prefix) and n.endswith(".json")]

    translated_count = 0
    for n in dialogue_files:
        raw = z.read(n).decode("utf-8", "ignore")
        try:
            data = json.loads(raw)
        except Exception:
            continue
        data2 = translate_obj(data, translate_fn)
        # Apply manual overrides (exact string match) after translation.
        if overrides:
            data2s = json.dumps(data2, ensure_ascii=True)
            for src, dst in overrides.items():
                data2s = data2s.replace(src, dst)
            data2 = json.loads(data2s)

        out_path = out_dir / n
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(data2, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        translated_count += 1

    print(f"dialogues_translated={translated_count}")

    # 2) Optionally translate tellraw JSON blobs in mcfunctions.
    if args.include_mcfunction_tellraw:
        func_prefix = "data/johto/function/"
        func_files = [n for n in z.namelist() if n.startswith(func_prefix) and n.endswith(".mcfunction")]
        tellraw_re = re.compile(r"^(\\s*tellraw\\s+\\S+\\s+)(.+)$")

        def translate_tellraw_json(s: str) -> str:
            try:
                data = json.loads(s)
            except Exception:
                return s
            data2 = translate_obj(data, translate_fn)
            return json.dumps(data2, ensure_ascii=True, separators=(",", ":"))

        w = 0
        for n in func_files:
            # If a fixed version exists, use it as base (avoid reintroducing removed commands).
            if fixes_dir:
                alt = fixes_dir / n
                if alt.exists():
                    base = alt.read_text(encoding="utf-8", errors="ignore")
                else:
                    base = z.read(n).decode("utf-8", "ignore")
            else:
                base = z.read(n).decode("utf-8", "ignore")

            lines = []
            changed = False
            for ln in base.splitlines():
                m = tellraw_re.match(ln)
                if not m:
                    lines.append(ln)
                    continue
                prefix, j = m.group(1), m.group(2)
                j2 = translate_tellraw_json(j)
                if j2 != j:
                    changed = True
                lines.append(prefix + j2)
            if changed:
                out_path = out_dir / n
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                w += 1
        print(f"mcfunctions_with_tellraw_translated={w}")


if __name__ == "__main__":
    main()

