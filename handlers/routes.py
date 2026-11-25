from pathlib import Path

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardButton,  InlineKeyboardMarkup, InputMediaPhoto

from handlers.products import CATEGORIES, PRODUCTS, find_item
from database import add_favorite, remove_favorite, is_favorite, get_favorites

router = Router()

BASE_DIR = Path(__file__).resolve().parent.parent
LOGO_PATH = BASE_DIR / "logo.png"
PHOTOS_DIR = BASE_DIR / "photos"
CATALOG_PATH = BASE_DIR / "CATALOG.png"

SITE_URL =  "https://t.me/FRG_wearlist"                              
CATALOG_URL =  "https://t.me/FRAGMENTUM_wear"
ORDER_URL = "https://t.me/FRG_order"    

WELCOME_TEXT = (
    "Привет! Это бот FRAGMENTUM, здесь ты можешь быстро выбрать товар, связаться c менеджером и не только.\n\n" 
    "FRAGMENTUM - магазин одежды ручной работы: Каждое изделие изготавливается вручную в индивидуальном порядке и "
    "доступно для заказа в других цветах и с другой фурнитурой. Также возможны изменения дизайна по желанию клиента."
    "Предоплата 50% за материалы, еще 50 перел отправкой."
    "Цены без учета доставки. Доставка СДЭКом.\n\n"
    "Подпишись на уведомления, чтобы не пропустить новый дроп."
)










def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=" Избранное", callback_data="wishlist"),
                InlineKeyboardButton(text=" Статус заказа", callback_data="status"),
            ],
            [
                InlineKeyboardButton(text=" Связь c менeджером", url=ORDER_URL),
                InlineKeyboardButton(text=" Телеграмм канал",url=CATALOG_URL),
            ],
            [
                InlineKeyboardButton(text=" Каталог", callback_data="catalog"),
            ],
        ]
    )

def categories_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=title, callback_data=f"cat:{key}")
        for key, title in CATEGORIES.items()
    ]

    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def item_keyboard(category: str, index: int, total: int, is_fav: bool) -> InlineKeyboardMarkup:
    order_button = InlineKeyboardButton(text="🛒 Заказать", url=ORDER_URL)

    if total > 1:
        prev_index = (index - 1) % total  
        next_index = (index + 1) % total  
        first_row = [
            InlineKeyboardButton(text="◀", callback_data=f"item:{category}:{prev_index}"),
            order_button,
            InlineKeyboardButton(text="▶", callback_data=f"item:{category}:{next_index}"),
        ]
    else:
        first_row = [order_button]

    fav_text = "❤️ В избранном" if is_fav else "🤍 В избранное"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            first_row,
            [InlineKeyboardButton(text=fav_text, callback_data=f"fav:{category}:{index}")],
            [InlineKeyboardButton(text="⬅️ К категориям", callback_data="catalog")],
        ]
    )


def item_text(item: dict) -> str:
    return (
        f"{item['code']} — {item['name']}\n"
        f"💰 {item['price']} ₽\n\n"
        f"{item['description']}\n\n"
        f"🧵 Материал:\n{item['materials']}\n\n"
        f"⏱ Срок пошива: {item['days']} дней"
    )


async def show_screen(callback: CallbackQuery, photo_path: Path, text: str, keyboard: InlineKeyboardMarkup):
    #zamena
    await callback.message.edit_media(
        media=InputMediaPhoto(media=FSInputFile(photo_path), caption=text),
        reply_markup=keyboard,
    )


async def show_item(callback: CallbackQuery, category: str, index: int):
    items = PRODUCTS[category]
    item = items[index]
    is_fav = is_favorite(callback.from_user.id, item["code"])

    await show_screen(
        callback,
        PHOTOS_DIR / item["photo"],
        item_text(item),
        item_keyboard(category, index, len(items), is_fav),
    )

#обработчкики

@router.message(CommandStart())
async def start(message: Message):
    if LOGO_PATH.exists():
        
        await message.answer_photo(
            photo=FSInputFile(LOGO_PATH),
            caption=WELCOME_TEXT,
            reply_markup=main_keyboard(),
        )
    else:
        
        await message.answer(WELCOME_TEXT, reply_markup=main_keyboard())

def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu")],
        ]
    )



@router.callback_query(F.data == "status")
async def open_status(callback: CallbackQuery):
    await show_screen(callback,LOGO_PATH,"Скоро появиться🩶",back_keyboard())
    await callback.answer()




@router.callback_query(F.data == "menu")
async def back_to_menu(callback: CallbackQuery):
    await show_screen(callback, LOGO_PATH, WELCOME_TEXT, main_keyboard())
    await callback.answer()


@router.callback_query(F.data == "catalog")
async def open_catalog(callback: CallbackQuery):
    await show_screen(callback, CATALOG_PATH, "Выберите категорию:", categories_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("cat:"))
async def open_category(callback: CallbackQuery):
    category = callback.data.split(":")[1]  

    if not PRODUCTS.get(category):  # список товаров пустой или такой категории нет
        await callback.answer("В этой категории пока пусто, скоро добавим", show_alert=True)
        return

    await show_item(callback, category, 0)
    await callback.answer()


@router.callback_query(F.data.startswith("item:"))
async def switch_item(callback: CallbackQuery):
    _, category, index = callback.data.split(":")  
    await show_item(callback, category, int(index))
    await callback.answer()


@router.callback_query(F.data.startswith("fav:"))
async def toggle_favorite(callback: CallbackQuery):
    _, category, index = callback.data.split(":")
    index = int(index)
    items = PRODUCTS[category]
    code = items[index]["code"]

    user_id = callback.from_user.id

    if is_favorite(user_id, code):
        remove_favorite(user_id, code)
        now_fav = False
        await callback.answer("Убрано из избранного")
    else:
        add_favorite(user_id, code)
        now_fav = True
        await callback.answer("Добавлено в избранное ❤️")

    # меняем только кнопки, фото заново не загружаем
    await callback.message.edit_reply_markup(
        reply_markup=item_keyboard(category, index, len(items), now_fav)
    )

    await callback.message.edit_reply_markup(
        reply_markup=item_keyboard(category, index, len(items), now_fav)
    )

#ИЗБРАННОЕ

def wishlist_keyboard(index: int, total: int) -> InlineKeyboardMarkup:
    order_button = InlineKeyboardButton(text="🛒 Заказать", url=ORDER_URL)

    if total > 1:
        prev_index = (index - 1) % total
        next_index = (index + 1) % total
        first_row = [
            InlineKeyboardButton(text="◀", callback_data=f"wl:{prev_index}"),
            order_button,
            InlineKeyboardButton(text="▶", callback_data=f"wl:{next_index}"),
        ]
    else:
        first_row = [order_button]

    return InlineKeyboardMarkup(
        inline_keyboard=[
            first_row,
            [InlineKeyboardButton(text="💔 Убрать из избранного", callback_data=f"wlrm:{index}")],
            [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu")],
        ]
    )


async def show_wishlist_item(callback: CallbackQuery, index: int):
    codes = get_favorites(callback.from_user.id)
    item = find_item(codes[index])

    await show_screen(
        callback,
        PHOTOS_DIR / item["photo"],
        item_text(item),
        wishlist_keyboard(index, len(codes)),
    )


@router.callback_query(F.data == "wishlist")
async def open_wishlist(callback: CallbackQuery):
    if not get_favorites(callback.from_user.id):
            await callback.answer("В избранном пока пусто", show_alert=True)
            return

    await show_wishlist_item(callback, 0)
    await callback.answer()


@router.callback_query(F.data.startswith("wl:"))
async def switch_wishlist_item(callback: CallbackQuery):
    index = int(callback.data.split(":")[1])
    await show_wishlist_item(callback, index)
    await callback.answer()


@router.callback_query(F.data.startswith("wlrm:"))
async def remove_from_wishlist(callback: CallbackQuery):
    index = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    codes = get_favorites(user_id)
    remove_favorite(user_id, codes[index])

    codes = get_favorites(user_id)  # список после удаления
    if not codes:
        await show_screen(callback, LOGO_PATH, WELCOME_TEXT, main_keyboard())
        await callback.answer("Избранное пусто")
        return

    await show_wishlist_item(callback, min(index, len(codes) - 1))
    await callback.answer("Убрано из избранного")
