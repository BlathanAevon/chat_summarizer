# This Python file uses the following encoding: utf-8

import telebot
import openai
import threading
import time
import os
import csv
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
                # "content": "Сделай анализ сообщений и выбери из них 5-15 самых важных, составь из этого список с гиперссылками в формате [текст](ссылка), ссылкой должна быть ссылкан а сообщение и также, ссылкой должно быть какое-то важное слово в каждом пунтке, при выборе опирайся на то, что 'важными' имеются ввиду сообщения связаные с криптовалютой, технологиями, финансами и тд.",
                "content": "Задача заключается в проведении анализа сообщений и выборе наиболее значимых 5-15 из них, после чего необходимо сформировать список, в котором каждый элемент представляет собой гиперссылку в формате [текст](ссылка) извлекается из сообщения и используется в качестве текста ссылки, а ссылка ведет к исходному сообщению; определение важности сообщений основывается на наличии в них ключевых слов и фраз, связанных с криптовалютой, технологиями, финансами и смежными областями, и именно на основе этой аналитики формируется итоговый список.",
            },
            {
                "role": "user",
                "content": input_data,
            },
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )


def send_summary():
    logger.warning("Поток 1 - отправка выжимки запущен!")
    while True:
        with open("messages.csv", mode="r", newline="") as messages_file:
            csv_reader = csv.reader(messages_file)
            messages_data = ""
            for row in csv_reader:
                message, link = row[0], row[1]
                messages_data += f"Сообщение: {message}, Ссылка: {link}\n"

            if len(messages_data) < 250 or len(messages_data) > 7000:
                logger.error("Слишком много или мало данных для выжимки!")
                pass
            else:
                summary_message = summarize(messages_data)["choices"][0]["message"][
                    "content"
                ]

                bot.send_message(
                    os.getenv("CHAT_ID"), summary_message, parse_mode="MarkdownV2"
                )

                with open("messages.csv", mode="w", newline="") as file:
                    pass

        time.sleep(600)


@bot.message_handler(func=lambda message: True)
def echo(message):
    message_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.id}"
    message_text = message.text

    if len(message_text) < 45:
        return

    with open("messages.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([message_text, message_link])
        logger.info(f"Сообщение {message_link} записано в таблицу ")


def main():
    logger.warning("Поток 2 - основной поток бота запущен!")
    bot.polling()


if __name__ == "__main__":
    t1 = threading.Thread(target=send_summary)
    t2 = threading.Thread(target=main)
    t1.start()
    t2.start()
