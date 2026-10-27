# KDP Puzzle Bot

Генератор детских книг-головоломок (6–8 лет) для Amazon KDP Paperback, бренд Invisible KID.
Сейчас готово ядро: генератор книги. Telegram-бот (@kid_01_bot) будет следующим шагом и будет
вызывать этот же код.

## Что умеет

- Головоломки: лабиринты, поиск слов (word search), «найди и посчитай» (seek and find), dot-to-dot.
- Сложность: `progressive` (от лёгких к сложным, по умолчанию), `easy`, `medium`, `hard`.
- Темы: `christmas`, `halloween`, `space`, `animals` (файл `puzzlebook/themes.py`).
- Книга: титул, «This book belongs to» + copyright, страница с инструкцией, головоломки,
  сертификат, ответы в конце. Страниц всегда чётное число и не меньше 24 (требование KDP).
- Формат: 8.5×11", ч/б, без bleed, 300 DPI, поля по требованиям KDP.

## Запуск из командной строки

```
pip install -r requirements.txt
python make_book.py --theme christmas --maze 10 --wordsearch 10 --hidden 6 --dots 6 --preview 1,4,20
```

Готовый `interior.pdf` и картинки-превью появятся в папке `output`. Одинаковые настройки и
одинаковый `--seed` дают одну и ту же книгу; другой `--seed` даёт новые головоломки.

## Структура

- `puzzlebook/lib.py`: холст и запись PDF (только Pillow).
- `puzzlebook/icons.py`: контурные иконки, которые ребёнок может раскрасить.
- `puzzlebook/puzzles/`: по файлу на каждый тип головоломки (страница + ответ).
- `puzzlebook/book.py`: сборка всей книги.
- `fonts/`: шрифты Andika и Fredoka (SIL Open Font License, можно использовать в коммерческих книгах).
