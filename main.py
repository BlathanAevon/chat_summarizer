import telebot
import openai
import threading
import time
import os
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))


def summarize(input_data):
    return openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Проанализируй сообщения и сделай краткую выжимку из 10-15 пунктов которые могут быть наиболее интересны аудитории чата, верни каждое сообщение гиперссылкой (используя ссылку на каждое сообщение) в формате <a href='ссылка'>сообщение</a>, оформи весь ответ красиво, если информация не подана или ее слишком мало - верни 0",
            },
            {
                "role": "user",
                "content": input_data,
            },
        ],
        temperature=0,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )


def get_gpt_response(input_data):
    return openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "проведи анализ, чтобы определить, содержит ли сообщение информацию, связанную с криптовалютами или финансами. Для этого просканируй текст сообщения в поисках ключевых слов или фраз, связанных с криптовалютами (например, 'биткоин', 'эфириум', 'доллар') или финансовой тематикой (например, 'инвестиции', 'акции', 'биржа'). Если такие и другие подобные упоминания обнаруживаются, верни значение 1, указывая на наличие связанных с криптовалютами или финансами данных. В противном случае, если в сообщении отсутствуют такие упоминания, верни значение 0, сигнализируя об их отсутствии.",
            },
            {
                "role": "user",
                "content": input_data,
            },
        ],
        temperature=0,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )


def send_summary():
    while True:
        with open("important_messages.txt", "r") as messages_file:
            message = summarize(messages_file.read())["choices"][0]["message"][
                "content"
            ]

            bot.send_message(os.getenv("CHAT_ID"), message, parse_mode="HTML")

        time.sleep(600)

        with open("important_messages.txt", "w") as file:
            file.write("")


@bot.message_handler(func=lambda message: True)
def echo(message):
    message_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.id}"
    message_text = message.text

    if len(message_text) < 20:
        return

    response = get_gpt_response(message_text)["choices"][0]["message"]["content"]

    if "1" in response:
        with open("important_messages.txt", "a+") as messages_file:
            messages_file.write(f"{message_text} {message_link}\n")

        logger.info(f"Сообщение {message_link} помечено как 'Важное' ")
    else:
        pass


def main():
    bot.polling()


if __name__ == "__main__":
    t1 = threading.Thread(target=send_summary)
    t2 = threading.Thread(target=main)
    t1.start()
    t2.start()
