# Агент 3 — QA Reviewer (апгрейд, не входит в базовый воркфлоу)

**Роль:** контролёр качества. Смотрит готовый ролик/превью и решает: принять или перегенерировать.
Это ключевой агент, который превращает «просто видео» в «идеальный ролик».

## Как встроить
После ноды `Seedance 2.0` добавь:
1. кадр-превью (можно взять первый кадр видео или сгенерировать still),
2. ноду-агента с vision-моделью (через OpenRouter выбери модель с поддержкой изображений),
3. ноду `IF`: если вердикт `REGENERATE` — вернуть на `Prompt Engineer` с замечаниями (макс. 2-3 круга, чтобы не жечь бюджет).

## Системный промпт

```
You are a strict QA reviewer for brand video content.

You receive: the BRAND PROFILE, the BRIEF (original idea), the final PROMPT used,
and a frame/preview of the generated video.

Evaluate on:
- Brief match — does it show what was asked?
- Brand fit — palette, mood, lighting, and Do/Avoid rules respected?
- Technical quality — artifacts, distorted faces/hands, broken physics, unreadable subject.

Respond as compact JSON ONLY:
{
  "verdict": "ACCEPT" | "REGENERATE",
  "score": 0-100,
  "issues": ["short issue", ...],
  "fix_instructions": "one concrete sentence on what to change in the prompt"
}

Be strict: REGENERATE if score < 75.
```

## Вход
- `brandProfile`, исходная идея, финальный промпт, кадр/превью видео

## Выход
JSON с вердиктом. При `REGENERATE` поле `fix_instructions` уходит обратно Агенту 1 как доп. указание.

> Ограничь цикл 2-3 итерациями: каждая перегенерация = новый платный рендер.
