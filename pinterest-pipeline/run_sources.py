#!/usr/bin/env python3
"""
Обработать таблицу sources.csv — твою таблицу ввода.

Ты заполняешь sources.csv:
    series,folder_path,status
    series-01,/путь/к/папке/с/фото,new

Запускаешь:
    python3 run_sources.py

Скрипт для каждой строки со status=new берёт фото из folder_path, раскладывает
их по 9 аккаунтам (с проверкой «1 фото = 1 раз») и меняет status на done.
Дальше: сгенерировать подписи -> собрать dashboard.html -> проверить -> approve.
"""

import csv
import sys
from pathlib import Path

from distribute import distribute_folder

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources.csv"
FIELDS = ["series", "folder_path", "status"]


def main() -> None:
    if not SOURCES.exists():
        sys.exit("Нет sources.csv")

    with SOURCES.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    changed = False
    for row in rows:
        if (row.get("status") or "").strip().lower() != "new":
            continue
        series = (row.get("series") or "").strip()
        folder = (row.get("folder_path") or "").strip()
        if not series or not folder:
            print(f"Пропуск строки: не заполнены series/folder_path -> {row}")
            continue
        src = Path(folder).expanduser()
        print(f"\n=== Обрабатываю {series} из {src} ===")
        distribute_folder(series, src)
        row["status"] = "done"
        changed = True

    if changed:
        with SOURCES.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        print("\nsources.csv обновлён (обработанные строки -> done).")
    else:
        print("Нет строк со status=new.")


if __name__ == "__main__":
    main()
