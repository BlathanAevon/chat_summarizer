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


def get_gpt_output(input_data, prompt):
    return openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                # "content": "Сделай анализ сообщений и выбери из них 5-15 самых важных, составь из этого список с гиперссылками в формате [текст](ссылка), ссылкой должна быть ссылкан а сообщение и также, ссылкой должно быть какое-то важное слово в каждом пунтке, при выборе опирайся на то, что 'важными' имеются ввиду сообщения связаные с криптовалютой, технологиями, финансами и тд.",
                "content": prompt
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
                prompt = "проанализируй все сообщения, сделай краткую выжимку из 1 - 15 пунктов, верни все сообщения красиво оформленным списком гиперссылок в формате [сообщение](ссылка), начни сообщение с: Вот выжимка самых полезных сообщений:"
                summary_message = get_gpt_output(messages_data, prompt)["choices"][0]["message"][
                    "content"
                ]
                summary_message = summary_message.replace('.', '\\.')
                summary_message = summary_message.replace('-', '\\-')
                summary_message = summary_message.replace('(', '\\(')
                summary_message = summary_message.replace(')', '\\)')
                bot.send_message(
                    os.getenv("CHAT_ID"), summary_message, parse_mode="MarkdownV2"
                )
                logger.success("Выжимка успешно отправлена!")

                with open("messages.csv", mode="w", newline="") as file:
                    pass
        tts = 1800
        logger.info(f"Жду {tts / 60} минут до следующей выжимки...")
        time.sleep(tts)


@bot.message_handler(func=lambda message: True)
def echo(message):
    message_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.id}"
    message_text = message.text

    if len(message_text) < 60:
        return

    is_useful = get_gpt_output(message.text, "если сообщение каким либо образом содержит тематику криптовалют, финансов, технологий и подобных тем - верни 1 слово - 1, в противном случае верни 1 слово - 0")
    if "1" in is_useful:
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