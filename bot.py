"""Telegram bot: asks for the book settings with buttons and sends back interior.pdf, cover.pdf and listing.txt.

Runs on your computer (long polling, no server). Settings live in the .env file next to this one.
"""
import asyncio
import logging
import os
import random
import time
from logging.handlers import RotatingFileHandler

import httpx
from dotenv import load_dotenv
from telegram import (BotCommand, InlineKeyboardButton as Btn, InlineKeyboardMarkup, InputMediaPhoto, MenuButtonCommands,
                      Update)
from telegram.constants import ParseMode
from telegram.error import NetworkError
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.request import HTTPXRequest

from puzzlebook.book import ORDER, Book, BookSpec
from puzzlebook.cover import Cover
from puzzlebook.listing import make_listing

HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(HERE, ".env"))

os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[RotatingFileHandler(os.path.join(HERE, "logs", "bot.log"), maxBytes=2_000_000, backupCount=3,
                                  encoding="utf-8"), logging.StreamHandler()])
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("bot")

BOOKS_DIR = os.path.join(HERE, "books")

THEMES = {"christmas": "🎄 Рождество", "halloween": "🎃 Хэллоуин", "space": "🚀 Космос", "animals": "🐾 Животные"}
KINDS = {"maze": "🌀 Лабиринты", "wordsearch": "🔤 Поиск слов", "hidden": "🔍 Найди и посчитай", "dots": "✏️ Точка к точке"}
TOTALS = [20, 30, 40, 50, 60]
LEVELS = {"progressive": "📈 Нарастает (советую)", "easy": "🙂 Лёгкая", "medium": "😐 Средняя", "hard": "🤯 Сложная"}

build_lock = asyncio.Lock()          # one book at a time: building uses the whole processor


def admin_ids():
    raw = os.getenv("ADMIN_IDS", "")
    return {int(x) for x in raw.replace(" ", "").split(",") if x.strip().lstrip("-").isdigit()}


async def allowed(update: Update) -> bool:
    uid = update.effective_user.id if update.effective_user else None
    if uid in admin_ids():
        return True
    text = (f"Ваш Telegram ID: <code>{uid}</code>\n\n"
            "Бот пока не знает, что это вы. Откройте файл <b>.env</b> в папке бота, впишите строку\n"
            f"<code>ADMIN_IDS={uid}</code>\nсохраните файл и перезапустите бота (закройте окно и снова откройте start.bat).")
    if update.callback_query:
        await update.callback_query.answer("Нет доступа", show_alert=True)
    elif update.effective_message:
        await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)
    log.info("refused user %s", uid)
    return False


# ----------------------------------------------------------------- dialogue
def draft(context):
    return context.user_data.setdefault("draft", {"theme": None, "kinds": list(ORDER), "total": 30,
                                                  "difficulty": "progressive"})


def split_counts(kinds, total):
    base, extra = divmod(total, len(kinds))
    return {k: base + (1 if i < extra else 0) for i, k in enumerate(kinds)}


def kb(rows):
    return InlineKeyboardMarkup([[Btn(text, callback_data=data) for text, data in row] for row in rows])


def theme_keyboard():
    items = list(THEMES.items())
    return kb([[(items[i][1], f"theme:{items[i][0]}"), (items[i + 1][1], f"theme:{items[i + 1][0]}")]
               for i in range(0, len(items), 2)])


def kinds_keyboard(d):
    rows = [[(("✅ " if k in d["kinds"] else "⬜ ") + label, f"kind:{k}")] for k, label in KINDS.items()]
    rows.append([("Дальше ➡️", "kinds_done")])
    return kb(rows)


def totals_keyboard():
    return kb([[(str(n), f"total:{n}") for n in TOTALS]])


def levels_keyboard():
    return kb([[(label, f"level:{k}")] for k, label in LEVELS.items()])


def summary(d):
    counts = split_counts(d["kinds"], d["total"])
    lines = [f"Тема: <b>{THEMES[d['theme']]}</b>", f"Сложность: <b>{LEVELS[d['difficulty']]}</b>", ""]
    lines += [f"{KINDS[k]}: {n}" for k, n in counts.items()]
    pages = len(Book(spec_from(d, 0)).pages)
    lines += ["", f"Получится примерно <b>{pages} страниц</b> (с ответами и служебными страницами)."]
    return "\n".join(lines)


def spec_from(d, seed):
    return BookSpec(theme=d["theme"], counts=split_counts(d["kinds"], d["total"]), difficulty=d["difficulty"], seed=seed)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await allowed(update):
        return
    await update.message.reply_text(
        "Привет! Я собираю книги-головоломки для Amazon KDP.\n\n"
        "/new — новая книга\n/help — подсказка\nЭти же команды есть под кнопкой «Меню» слева от поля ввода.\n\n"
        "Бот присылает три файла для KDP: interior.pdf (страницы книги, 8.5×11\", ч/б), cover.pdf (цветная обложка "
        "с корешком) и listing.txt (название, описание, ключевые слова). Копия сохраняется в папку books на компьютере.")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await allowed(update):
        return
    await update.message.reply_text(
        "Как пользоваться:\n1. Напишите /new\n2. Выберите тему, виды головоломок, количество и сложность\n"
        "3. Нажмите «Собрать» и подождите 1–2 минуты\n4. Не понравилось — «Другой вариант»: те же настройки, "
        "новые головоломки.\n\nЕсли что-то сломалось, пришлите Claude файл logs/bot.log из папки бота.")


async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await allowed(update):
        return
    context.user_data.pop("draft", None)
    await update.effective_message.reply_text("Выберите тему книги:", reply_markup=theme_keyboard())


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await allowed(update):
        return
    q = update.callback_query
    data = q.data
    d = draft(context)
    if data.startswith("theme:"):
        d["theme"] = data.split(":", 1)[1]
        await q.answer()
        await q.edit_message_text(f"Тема: {THEMES[d['theme']]}\n\nКакие головоломки положить в книгу?",
                                  reply_markup=kinds_keyboard(d))
    elif data.startswith("kind:"):
        k = data.split(":", 1)[1]
        d["kinds"] = [x for x in ORDER if (x in d["kinds"]) != (x == k)]
        await q.answer()
        await q.edit_message_reply_markup(reply_markup=kinds_keyboard(d))
    elif data == "kinds_done":
        if not d["kinds"]:
            await q.answer("Выберите хотя бы один вид", show_alert=True)
            return
        await q.answer()
        await q.edit_message_text("Сколько всего головоломок в книге?", reply_markup=totals_keyboard())
    elif data.startswith("total:"):
        d["total"] = int(data.split(":", 1)[1])
        await q.answer()
        await q.edit_message_text("Сложность:", reply_markup=levels_keyboard())
    elif data.startswith("level:"):
        d["difficulty"] = data.split(":", 1)[1]
        await q.answer()
        await q.edit_message_text(summary(d), parse_mode=ParseMode.HTML,
                                  reply_markup=kb([[("🚀 Собрать", "build")], [("↩️ Начать заново", "new")]]))
    elif data == "build":
        await q.answer()
        await q.edit_message_reply_markup(reply_markup=None)
        await build_and_send(update, context, d, random.randint(1, 99999))
    elif data == "again":
        last = context.user_data.get("last")
        await q.answer()
        if not last:
            await q.message.reply_text("Не помню прошлые настройки. Начните с /new")
            return
        await build_and_send(update, context, last, random.randint(1, 99999))
    elif data == "new":
        await q.answer()
        await cmd_new(update, context)
    else:
        await q.answer()


# ------------------------------------------------------------------- build
async def build_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE, d, seed):
    chat = update.effective_chat
    if build_lock.locked():
        await chat.send_message("⏳ Уже собираю другую книгу, эта встанет в очередь.")
    async with build_lock:
        status = await chat.send_message("⚙️ Собираю книгу… 0%")
        loop = asyncio.get_running_loop()
        shown = {"pct": 0, "t": 0.0}

        def progress(n, total, _elapsed):
            pct = int(n * 100 / total)
            if pct - shown["pct"] >= 10 and time.time() - shown["t"] > 2:
                shown.update(pct=pct, t=time.time())
                asyncio.run_coroutine_threadsafe(status.edit_text(f"⚙️ Собираю книгу… {pct}%"), loop)

        spec = spec_from(d, seed)
        out_dir = os.path.join(BOOKS_DIR, time.strftime("%Y-%m-%d_%H-%M") + f"_{d['theme']}_{seed}")
        t0 = time.time()
        try:
            book, files, previews = await asyncio.to_thread(render, spec, out_dir, progress)
        except Exception:
            log.exception("build failed: %s", spec)
            await status.edit_text("😕 Не получилось собрать книгу. Подробности записаны в logs/bot.log — "
                                   "пришлите этот файл Claude.")
            return
        log.info("built %s in %.0fs: %s", out_dir, time.time() - t0, book.summary())
        context.user_data["last"] = dict(d)
        await status.edit_text(f"✅ Готово за {time.time() - t0:.0f} с. Отправляю…")
        media = []
        for p in previews[:10]:
            with open(p, "rb") as f:
                media.append(InputMediaPhoto(f.read()))
        if media:
            await chat.send_media_group(media)
        margins = book.margin_report()
        captions = {
            "interior": (f"📘 <b>{book.title}</b>\n{len(book.pages)} страниц, тема {THEMES[d['theme']]}, "
                         f"номер варианта {seed}\nПоля: {margins['gutter']:.2f}\" у корешка (KDP просит ≥ 0.375\")"),
            "cover": (f"🎨 Обложка для KDP: задняя сторона, корешок {files['spine']:.3f}\" и лицевая, "
                      f"с вылетами 0.125\". Белый прямоугольник сзади оставлен под штрихкод KDP."),
            "listing": ("📝 Тексты для страницы книги на KDP: название, описание, 7 ключевых слов, категории "
                        f"и настройки печати.\nКопия всех файлов на компьютере: books/{os.path.basename(out_dir)}"),
        }
        for key in ("interior", "cover", "listing"):
            path = files[key]
            ext = os.path.splitext(path)[1]
            last = key == "listing"
            with open(path, "rb") as f:
                await chat.send_document(f, filename=f"{d['theme']}-{seed}-{key}{ext}", caption=captions[key],
                                         parse_mode=ParseMode.HTML,
                                         reply_markup=kb([[("🔄 Другой вариант", "again"), ("🆕 Новая книга", "new")]])
                                         if last else None)
        await status.delete()


def render(spec, out_dir, progress):
    """interior.pdf, cover.pdf and listing.txt in out_dir; previews start with the cover."""
    book = Book(spec)
    # previews: the first page of every puzzle section (the cover preview replaces the title page)
    pages = {first for first, _ in (book.sections[k] for k in book.kinds)}
    pdf, previews = book.render(out_dir, pages, progress)
    cover = Cover(book)
    cover_pdf, cover_preview = cover.render(out_dir)
    listing = os.path.join(out_dir, "listing.txt")
    with open(listing, "w", encoding="utf-8") as f:
        f.write(make_listing(book))
    files = {"interior": pdf, "cover": cover_pdf, "listing": listing, "spine": cover.spine / 72}
    return book, files, [cover_preview] + previews


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await allowed(update):
        return
    await update.message.reply_text("Чтобы собрать книгу, напишите /new")


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error("unhandled error", exc_info=context.error)
    if isinstance(update, Update) and update.effective_chat:
        try:
            await update.effective_chat.send_message("😕 Что-то пошло не так. Подробности в logs/bot.log.")
        except Exception:
            pass


class PatientRequest(HTTPXRequest):
    """Waits longer for Telegram and retries when the connection itself could not be opened.

    On some networks the first connection to api.telegram.org takes several seconds. Retrying is safe
    only for connect errors: then the request never reached Telegram, so nothing gets sent twice.
    """

    async def do_request(self, *args, **kwargs):
        for attempt in range(4):
            try:
                return await super().do_request(*args, **kwargs)
            except NetworkError as e:
                if attempt == 3 or not isinstance(e.__cause__, (httpx.ConnectTimeout, httpx.ConnectError)):
                    raise
                log.warning("no connection to Telegram, retry %d: %r", attempt + 1, e.__cause__)
                await asyncio.sleep(2 * (attempt + 1))


MENU = [BotCommand("new", "📚 Новая книга"),
        BotCommand("help", "❓ Как пользоваться"),
        BotCommand("start", "🏠 Начало")]


async def setup_menu(app):
    """The "Menu" button left of the input field, as in the IQRacer bot: Telegram lists these commands."""
    try:
        await app.bot.set_my_commands(MENU)
        await app.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    except NetworkError as e:
        log.warning("could not set the menu button: %r", e)


def main():
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token or token.startswith("вставьте"):
        print("\nНе найден токен бота. Откройте файл .env в Блокноте и вставьте токен от @BotFather после BOT_TOKEN=\n")
        return
    timeouts = dict(connect_timeout=20, read_timeout=30, write_timeout=60, media_write_timeout=180, pool_timeout=20)
    app = (Application.builder().token(token)
           .request(PatientRequest(connection_pool_size=8, **timeouts))
           .get_updates_request(PatientRequest(**timeouts))
           .post_init(setup_menu)
           .build())
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("new", cmd_new))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(on_error)
    print("\nБот запущен. Откройте его в Telegram и напишите /new\nНе закрывайте это окно, пока пользуетесь ботом.\n")
    log.info("bot started, admins: %s", admin_ids() or "none yet")
    # Python 3.14 no longer creates an event loop on demand, so give run_polling one to use
    asyncio.set_event_loop(asyncio.new_event_loop())
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
