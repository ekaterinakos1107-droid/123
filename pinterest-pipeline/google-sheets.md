# Google-таблицы проекта

Я могу создавать и читать эти таблицы, но **не редактирую ячейки существующих**
(ограничение коннектора). Поэтому: таблицы заполняешь ты, я их читаю.

## 1. Продукты и баркоды

- **Ссылка:** https://docs.google.com/spreadsheets/d/1dVIDO4H71eL5sOGwa3MtP0bKYaVZZ829-FN61lQ0HmI/edit
- **ID:** `1dVIDO4H71eL5sOGwa3MtP0bKYaVZZ829-FN61lQ0HmI`
- Колонки: Тип патча · Название · Баркод · Сайт · Факты для описания
- **Сделать:** удалить колонку «Артикул WB» (не нужна — артикул = баркод).

Данные (зеркало в `products.csv`):

| patch_type | Название | Баркод | Сайт |
|---|---|---|---|
| mood | Mood patches | 4640593820034 | patchelogia.ru |
| dream | Dream Patches | 4640593820041 | patchelogia.ru |
| berberine | Berberine patches | 4695145128014 | patchelogia.ru |

## 2. Ввод пинов (серия, фото, тип патча)

- **Ссылка:** https://docs.google.com/spreadsheets/d/1OyIpjo4FeLfLWWTZh1Px4CZQlmdLyPR_uCmXEpY4Vag/edit
- **ID:** `1OyIpjo4FeLfLWWTZh1Px4CZQlmdLyPR_uCmXEpY4Vag`
- Колонки: Серия · Файл фото · Тип патча (mood/dream/berberine) · Статус
- Здесь ты указываешь, к какому фото какой патч — по типу я подберу баркод и
  сгенерирую описание.

## Описание для Pinterest — что в него входит

Для каждого пина: сгенерированный текст в голосе Patchelogia (без мед. заявлений
и производственных секретов) + футер:

```
Артикул: <баркод по типу патча>
patchelogia.ru
```
