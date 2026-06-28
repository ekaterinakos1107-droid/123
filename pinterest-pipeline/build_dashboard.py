#!/usr/bin/env python3
"""
Собрать визуальную таблицу dashboard.html — твой экран проверки.

Колонки: превью картинки | серия | аккаунт | файл | подпись | статус | дата.
Картинка показывается прямо в таблице. Цвет статуса:
  assigned  — жёлтый (ждёт проверки)
  approved  — синий  (подтверждено тобой)
  published — зелёный (опубликовано)

Запуск:
    python3 build_dashboard.py
Потом открой pinterest-pipeline/dashboard.html в браузере.
"""

import csv
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "ledger.csv"
CAPTIONS = ROOT / "captions.csv"
PUBLISHED_DIR = ROOT / "photos" / "published"
OUT = ROOT / "dashboard.html"

STATUS_COLOR = {
    "assigned": "#f5c518",   # жёлтый
    "approved": "#3b82f6",   # синий
    "published": "#22c55e",  # зелёный
}


def load_captions() -> dict[str, str]:
    caps = {}
    if CAPTIONS.exists():
        with CAPTIONS.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("hash"):
                    caps[row["hash"]] = row.get("caption", "")
    return caps


def img_src(series: str, account: str, filename: str) -> str | None:
    rel = Path("photos") / "published" / series / account / filename
    return str(rel) if (ROOT / rel).exists() else None


def main() -> None:
    if not LEDGER.exists():
        raise SystemExit("Нет ledger.csv — сначала разложи серию.")

    captions = load_captions()
    with LEDGER.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    cells = []
    for r in sorted(rows, key=lambda x: (x["series"], x["account"])):
        color = STATUS_COLOR.get(r["status"], "#888")
        src = img_src(r["series"], r["account"], r["filename"])
        thumb = (f'<img src="{html.escape(src)}" alt="">' if src
                 else '<div class="noimg">нет файла</div>')
        caption = html.escape(captions.get(r["hash"], "")) or \
            '<span class="muted">— подпись ещё не сгенерирована —</span>'
        cells.append(f"""
        <tr>
          <td class="thumb">{thumb}</td>
          <td>{html.escape(r['series'])}</td>
          <td><b>{html.escape(r['account'])}</b></td>
          <td class="file">{html.escape(r['filename'])}</td>
          <td class="cap">{caption}</td>
          <td><span class="badge" style="background:{color}">{html.escape(r['status'])}</span></td>
          <td class="date">{html.escape(r.get('assigned_at',''))}</td>
        </tr>""")

    summary = " · ".join(f"{k}: {v}" for k, v in sorted(counts.items())) or "пусто"

    doc = f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<title>Pinterest — таблица публикаций</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 24px; color:#1f2937; }}
  h1 {{ font-size: 20px; }}
  .summary {{ color:#6b7280; margin-bottom:16px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border-bottom:1px solid #e5e7eb; padding:10px 12px; text-align:left; vertical-align:top; font-size:14px; }}
  th {{ background:#f9fafb; position:sticky; top:0; }}
  .thumb img {{ width:120px; height:120px; object-fit:cover; border-radius:8px; background:#f3f4f6; }}
  .noimg {{ width:120px; height:120px; display:flex; align-items:center; justify-content:center;
            background:#f3f4f6; border-radius:8px; color:#9ca3af; font-size:12px; }}
  .cap {{ max-width:380px; line-height:1.5; }}
  .file, .date {{ color:#6b7280; font-size:12px; }}
  .muted {{ color:#9ca3af; font-style:italic; }}
  .badge {{ color:#fff; padding:3px 10px; border-radius:999px; font-size:12px; font-weight:600; }}
</style></head>
<body>
  <h1>Pinterest — таблица публикаций</h1>
  <div class="summary">Всего: {len(rows)} · {summary}</div>
  <table>
    <thead><tr>
      <th>Картинка</th><th>Серия</th><th>Аккаунт</th><th>Файл</th>
      <th>Подпись</th><th>Статус</th><th>Добавлено</th>
    </tr></thead>
    <tbody>{''.join(cells)}
    </tbody>
  </table>
</body></html>"""

    OUT.write_text(doc, encoding="utf-8")
    print(f"Готово: {OUT.relative_to(ROOT)} ({len(rows)} строк). Открой в браузере.")


if __name__ == "__main__":
    main()
