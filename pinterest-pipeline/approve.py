#!/usr/bin/env python3
"""
Подтверждение публикаций перед публикацией.

Публикуются ТОЛЬКО строки со статусом approved. Этот скрипт переводит
строки assigned -> approved после того, как ты проверила dashboard.html.

    python3 approve.py series-01            # подтвердить всю серию
    python3 approve.py series-01 pic_3.jpg  # подтвердить отдельные фото
    python3 approve.py --list               # показать статусы

Откатить (если передумала) — вернуть в assigned:
    python3 approve.py series-01 --undo
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "ledger.csv"
FIELDS = ["hash", "filename", "series", "account", "assigned_at", "status"]


def read_rows() -> list[dict]:
    with LEDGER.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_rows(rows: list[dict]) -> None:
    with LEDGER.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    if not LEDGER.exists():
        sys.exit("Нет ledger.csv — сначала разложи серию.")
    argv = sys.argv[1:]

    if "--list" in argv:
        rows = read_rows()
        for r in rows:
            print(f"  [{r['status']:<9}] {r['series']:<10} {r['account']:<12} {r['filename']}")
        return

    undo = "--undo" in argv
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        sys.exit("Укажи серию, напр.:  python3 approve.py series-01")
    series = args[0]
    files = set(args[1:])  # пусто = вся серия

    target = "assigned" if undo else "approved"
    source = "approved" if undo else "assigned"

    rows = read_rows()
    n = 0
    for r in rows:
        if r["series"] != series:
            continue
        if files and r["filename"] not in files:
            continue
        if r["status"] == source:
            r["status"] = target
            n += 1
    write_rows(rows)
    verb = "возвращено в assigned" if undo else "подтверждено (approved)"
    print(f"{verb}: {n} публикаций в {series}.")
    if not undo and n:
        print("Готово к публикации. Скажи мне — опубликую approved через postmypost.")


if __name__ == "__main__":
    main()
