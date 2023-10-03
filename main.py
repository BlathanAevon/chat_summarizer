# This Python file uses the following encoding: utf-8

import telebot
import openai
import threading
import time
import os
import csv
import pandas as pd
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
                "content": "Проанализируй сообщения и сделай краткую выжимку из 10-15 пунктов которые могут быть наиболее интересны аудитории чата, верни каждое сообщение гиперссылкой (используя ссылку на каждое сообщение) в формате <a href='ссылка'>сообщение</a>, оформи весь ответ красиво",
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
            for row in csv_reader:
                message, link = row[0], row[1]
                messages_data += f"Сообщение: {message}, Ссылка: {link}\n"

            if len(messages_data) < 250:
                return

            summary_message = summarize(messages_data)["choices"][0]["message"][
                "content"
            ]

            bot.send_message(os.getenv("CHAT_ID"), summary_message, parse_mode="HTML")

        time.sleep(600)

        with open("messages.csv", mode="w", newline="") as file:
            pass


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
