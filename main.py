import asyncio
import logging
import os
from collections import defaultdict, deque

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from openai import OpenAI

TELEGRAM_BOT_TOKEN = os.getenv("TG_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5.1-mini")

if not TELEGRAM_BOT_TOKEN or not OPENAI_API_KEY:
    raise RuntimeError("Потрібно задати TG_TOKEN і OPENAI_API_KEY.")

logging.basicConfig(level=logging.INFO)

client = OpenAI(api_key=OPENAI_API_KEY)

bot = Bot(
    token=TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

HISTORY_LIMIT = 12
user_history = defaultdict(lambda: deque(maxlen=HISTORY_LIMIT))

SYSTEM_PROMPT = """
Ти — приватний Telegram-помічник, який допомагає людям ставати успішними,
заробляти онлайн з нуля і без вкладень. Даєш чіткі, практичні поради,
покрокові плани, ніяких сірих чи незаконних методів.
"""

def build_messages(user_id: int, user_text: str):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(list(user_history[user_id]))
    messages.append({"role": "user", "content": user_text})
    return messages

async def ask_openai(user_id: int, user_text: str) -> str:
    messages = build_messages(user_id, user_text)

    resp = client.responses.create(
        model=MODEL_NAME,
        input=messages,
        temperature=0.7,
        max_output_tokens=600
    )

    answer = resp.output_text.strip()

    user_history[user_id].append({"role": "user", "content": user_text})
    user_history[user_id].append({"role": "assistant", "content": answer})

    return answer

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "Привіт! Я AI помічник, який допоможе тобі заробляти онлайн з нуля.\n"
        "Напиши, яку суму хочеш заробляти, і я підкажу план."
    )

@dp.message(F.text)
async def chat(message: types.Message):
    try:
        await message.chat.do(types.ChatAction.TYPING)
        answer = await ask_openai(message.from_user.id, message.text)
    except Exception:
        answer = "Помилка AI. Спробуй ще раз."
    await message.answer(answer)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
