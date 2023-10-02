import telebot
import openai
import threading
import time
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))


def summarize(input_data):
    return openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Сделай выжимку наиболее важных сообщений (не больше 10) и отправь в чат, не пиши никнеймы пользователей, пусть сообщение выглядит как: Выжимка за последние 10 минут: что-то, что-то, не добавляй ссылку на сообщение, фильтруй подозрительный контент, если сообщений нет то верни 'сообщений нет' ",
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
                "content": "если сообщения каким либо образом связано с криптовалютой верни 1 слово 'важное' если сообщение содержит ссылку и каким либо образом связано с криптовалютой верни 1 слово 'важное', во всех других случаях верни 1 слово '0'",
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

            bot.send_message(os.getenv("CHAT_ID"), message)

        with open("important_messages.txt", "w") as file:
            file.write("")

        time.sleep(600)


@bot.message_handler(func=lambda message: True)
def echo(message):
    message_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.id}"
    message_text = message.text

    response = get_gpt_response(message_text)
    resp_text = response["choices"][0]["message"]["content"]

    if "важное" in resp_text:
        with open("important_messages.txt", "a+") as messages_file:
            messages_file.write(f"{message_text} {message_link}\n")
    else:
        pass

    print(response["choices"][0]["message"]["content"])


def main():
    bot.polling()


if __name__ == "__main__":
    t1 = threading.Thread(target=send_summary)
    t2 = threading.Thread(target=main)
    t1.start()
    t2.start()
