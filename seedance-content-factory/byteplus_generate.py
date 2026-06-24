#!/usr/bin/env python3
"""
Генерация ролика на Seedance 2.0 через BytePlus ModelArk API.

Как запустить:
  1) Вставь свой ключ в API_KEY ниже  (или: export ARK_API_KEY="твой_ключ")
  2) При желании поменяй PROMPT / RATIO / DURATION
  3) python3 byteplus_generate.py
  -> в конце он напечатает ссылку на готовое видео (MP4)

Зависимости: только стандартная библиотека Python 3 (ничего ставить не надо).
"""
import json, os, time, urllib.request, urllib.error

# ─── 1. КЛЮЧ ───────────────────────────────────────────────────────────────
# Вставь сюда ключ из консоли BytePlus, ЛИБО задай переменную окружения ARK_API_KEY.
API_KEY = os.environ.get("ARK_API_KEY", "PASTE_YOUR_BYTEPLUS_KEY_HERE")

# ─── 2. АДРЕС API ──────────────────────────────────────────────────────────
# Регион ap-southeast-1. Если будет ошибка хоста — посмотри точный Base URL
# в консоли BytePlus для своего региона и подставь сюда.
BASE = "https://ark.ap-southeast.bytepluses.com/api/v3"

# ─── 3. НАСТРОЙКИ РОЛИКА ────────────────────────────────────────────────────
MODEL = "dreamina-seedance-2-0-fast-260128"   # fast = дешевле. Макс. качество: dreamina-seedance-2-0-260128
PROMPT = (
    "A matte-black minimalist ceramic coffee mug at the center of a warm-grey stone "
    "surface, soft cream background, thin steam rising slowly. Slow cinematic push-in, "
    "soft natural daylight from the left, gentle shadows, shallow depth of field. "
    "Calm premium mood, photoreal, subtle film grain. Single continuous shot, no text."
)
RATIO = "9:16"          # 9:16 — Reels/TikTok, 16:9 — YouTube, 1:1 — лента
RESOLUTION = "720p"     # 480p (дешевле) или 720p
DURATION = 5            # секунды (4–15)
GENERATE_AUDIO = False  # True добавит звук (может стоить дороже)

# ───────────────────────────────────────────────────────────────────────────
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def _send(req):
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code} от сервера:\n{e.read().decode(errors='replace')}")
    except urllib.error.URLError as e:
        raise SystemExit(f"Сетевая ошибка/неверный хост: {e}\nПроверь BASE (точный адрес в консоли BytePlus).")


def post(url, payload):
    return _send(urllib.request.Request(url, data=json.dumps(payload).encode(),
                                        headers=HEADERS, method="POST"))


def get(url):
    return _send(urllib.request.Request(url, headers=HEADERS, method="GET"))


def main():
    if "PASTE_YOUR" in API_KEY:
        raise SystemExit("Вставь свой ключ в API_KEY или задай переменную окружения ARK_API_KEY.")

    print("Отправляю задачу в Seedance...")
    task = post(f"{BASE}/contents/generations/tasks", {
        "model": MODEL,
        "content": [{"type": "text", "text": PROMPT}],
        "ratio": RATIO,
        "resolution": RESOLUTION,
        "duration": DURATION,
        "generate_audio": GENERATE_AUDIO,
    })
    task_id = task.get("id") or task.get("task_id")
    if not task_id:
        raise SystemExit("Не получил task id. Ответ сервера:\n" + json.dumps(task, ensure_ascii=False, indent=2))
    print("Task ID:", task_id, "— ждём рендер (обычно 1–3 мин)...")

    for i in range(120):  # до ~10 минут
        time.sleep(5)
        data = get(f"{BASE}/contents/generations/tasks/{task_id}")
        status = (data.get("status") or "").lower()
        print(f"  [{i:>3}] статус: {status}")
        if status in ("succeeded", "success", "completed", "done"):
            content = data.get("content") or {}
            url = content.get("video_url") or data.get("video_url")
            print("\n✅ ГОТОВО! Ссылка на видео:\n" + str(url))
            return
        if status in ("failed", "error", "canceled", "cancelled"):
            print("\n❌ Задача не удалась:\n" + json.dumps(data, ensure_ascii=False, indent=2))
            return
    print("\n⏳ Время ожидания вышло — проверь задачу позже в консоли BytePlus.")


if __name__ == "__main__":
    main()
