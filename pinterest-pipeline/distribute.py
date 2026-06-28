#!/usr/bin/env python3
"""
Распределение фото по 9 аккаунтам Pinterest с гарантией «1 фото = 1 раз».

Можно брать фото:
  - из стандартной папки серии  photos/series/series-01/
  - или из любой папки по пути   --from "/путь/к/папке"
  - или пачкой из таблицы sources.csv  (см. run_sources.py)

Что делает:
  1. Считает хэш (отпечаток) каждого фото.
  2. Сверяет с реестром ledger.csv — фото, использованное в ЛЮБОЙ серии или на
     ЛЮБОМ аккаунте, пропускается (повтор!).
  3. Раздаёт новые фото по аккаунтам по кругу (round-robin).
  4. Перемещает фото в photos/published/<серия>/<аккаунт>/.
  5. Дописывает строки в ledger.csv со статусом «assigned» (ждёт проверки).
  6. Сохраняет план серии в plans/<серия>.csv.

Статусы публикации (колонка status в ledger.csv):
  assigned   — разложено, ждёт твоей проверки в dashboard.html
  approved   — ты подтвердила (см. approve.py) — можно публиковать
  published  — опубликовано через postmypost

Запуск:
  python3 distribute.py series-01
  python3 distribute.py series-01 --from "/путь/к/папке"
  python3 distribute.py series-01 --dry-run
"""

import csv
import hashlib
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SERIES_DIR = ROOT / "photos" / "series"
PUBLISHED_DIR = ROOT / "photos" / "published"
PLANS_DIR = ROOT / "plans"
LEDGER = ROOT / "ledger.csv"
ACCOUNTS_FILE = ROOT / "accounts.txt"

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}
LEDGER_FIELDS = ["hash", "filename", "series", "account", "assigned_at", "status"]


def file_hash(path: Path) -> str:
    """SHA-256 по содержимому файла — ловит дубликат, даже если переименован."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_accounts() -> list[str]:
    accounts = []
    for line in ACCOUNTS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            accounts.append(line)
    if not accounts:
        sys.exit("В accounts.txt нет ни одного аккаунта.")
    return accounts


def load_used_hashes() -> set[str]:
    used = set()
    if LEDGER.exists():
        with LEDGER.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("hash"):
                    used.add(row["hash"])
    return used


def append_ledger(rows: list[dict]) -> None:
    new_file = not LEDGER.exists() or LEDGER.stat().st_size == 0
    with LEDGER.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LEDGER_FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerows(rows)


def distribute_folder(series: str, src: Path, dry_run: bool = False) -> dict:
    """Разложить фото из папки src по аккаунтам. Возвращает сводку."""
    if not src.is_dir():
        sys.exit(f"Папки нет: {src}")

    accounts = load_accounts()
    used = load_used_hashes()
    photos = sorted(p for p in src.iterdir()
                    if p.is_file() and p.suffix.lower() in IMAGE_EXT)
    if not photos:
        sys.exit(f"В {src} нет фото.")

    plan, ledger_rows, skipped = [], [], []
    seen_in_batch: set[str] = set()
    slot = 0
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for photo in photos:
        digest = file_hash(photo)
        if digest in used or digest in seen_in_batch:
            skipped.append(photo.name)
            continue
        seen_in_batch.add(digest)
        account = accounts[slot % len(accounts)]
        slot += 1
        plan.append({"filename": photo.name, "account": account,
                     "hash": digest, "path": photo})
        ledger_rows.append({"hash": digest, "filename": photo.name,
                            "series": series, "account": account,
                            "assigned_at": now, "status": "assigned"})

    print(f"\nСерия: {series}  (источник: {src})")
    print(f"Аккаунтов: {len(accounts)} | Фото в папке: {len(photos)} | "
          f"К публикации: {len(plan)} | Пропущено (повтор): {len(skipped)}\n")
    for item in plan:
        print(f"  {item['account']:<12} <- {item['filename']}")
    if skipped:
        print("\n  Пропущены как повтор:")
        for name in skipped:
            print(f"    - {name}")

    if dry_run:
        print("\n[--dry-run] Ничего не изменено.")
        return {"assigned": 0, "skipped": len(skipped)}
    if not plan:
        print("\nНовых фото нет — реестр не тронут.")
        return {"assigned": 0, "skipped": len(skipped)}

    PLANS_DIR.mkdir(exist_ok=True)
    plan_csv = PLANS_DIR / f"{series}.csv"
    with plan_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["series", "account", "filename", "published_path"])
        for item in plan:
            dest_dir = PUBLISHED_DIR / series / item["account"]
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / item["filename"]
            shutil.move(str(item["path"]), str(dest))
            writer.writerow([series, item["account"], item["filename"],
                             dest.relative_to(ROOT)])

    append_ledger(ledger_rows)
    print(f"\nГотово. План: {plan_csv.relative_to(ROOT)}")
    print(f"Фото перемещены в photos/published/{series}/<аккаунт>/")
    print("Статус: assigned (ждёт проверки в dashboard.html).")
    return {"assigned": len(plan), "skipped": len(skipped)}


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in sys.argv
    if not args:
        sys.exit("Укажи серию, напр.:  python3 distribute.py series-01")
    series = args[0]

    src = None
    if "--from" in sys.argv:
        i = sys.argv.index("--from")
        if i + 1 >= len(sys.argv):
            sys.exit("После --from укажи путь к папке.")
        src = Path(sys.argv[i + 1]).expanduser()
    else:
        src = SERIES_DIR / series

    distribute_folder(series, src, dry_run=dry_run)


if __name__ == "__main__":
    main()
