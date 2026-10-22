from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔎 Find partner"), KeyboardButton(text="⛔ Stop")],
            [KeyboardButton(text="📜 Rules"), KeyboardButton(text="🔒 Privacy")],
        ],
        resize_keyboard=True,
    )


def chat_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Next"), KeyboardButton(text="⛔ Stop")],
            [KeyboardButton(text="🚩 Report")],
        ],
        resize_keyboard=True,
    )


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_search")]]
    )


def search_again_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Search again", callback_data="search_again")]
        ]
    )
