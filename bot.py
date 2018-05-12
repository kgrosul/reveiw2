import telebot
import make_request
import requests
from collections import defaultdict
import os


user_request = defaultdict(lambda: None)
bot = telebot.TeleBot('582824205:AAGaNsND2bCU6XtJ_x9VQjpzd0dNfqq3yhA')


@bot.message_handler(commands=['new_docs'])
def reply_to_new_docs(message):
    bot.send_message(message.chat.id, 'Сколько документов надо вывести?')
    user_request[message.chat.id] = 'new_docs'


@bot.message_handler(commands=['new_topics'])
def reply_to_new_topic(message):
    bot.send_message(message.chat.id, 'Сколько тем надо вывести?')
    user_request[message.chat.id] = 'new_topics'


@bot.message_handler(commands=['topic'])
def reply_to_topic(message):
    bot.send_message(message.chat.id, 'Описание какой темы вы хотите узнать?')
    user_request[message.chat.id] = 'topic'


@bot.message_handler(commands=['words'])
def reply_to_words(message):
    bot.send_message(message.chat.id, 'Cлова для какой темы вы хотите узнать?')
    user_request[message.chat.id] = 'words'


@bot.message_handler(commands=['doc'])
def reply_to_doc(message):
    bot.send_message(message.chat.id,
                     'Текст какого документа надо вывести?')
    user_request[message.chat.id] = 'doc'


@bot.message_handler(commands=['describe_doc'])
def reply_to_describe_doc(message):
    bot.send_message(message.chat.id,
                     'Статистику по какому документу надо вывести?')
    user_request[message.chat.id] = 'describe_doc'


@bot.message_handler(commands=['describe_topic'])
def reply_to_describe_topic(message):
    bot.send_message(message.chat.id,
                     'Статистику по какой теме надо вывести?')
    user_request[message.chat.id] = 'describe_topic'


@bot.message_handler(commands=['help', 'start'])
def reply_to_describe_topic(message):
    text = "Привет! Вот что умеет бот:\n" + \
            "/help - список возможностей\n" + \
            "/new_docs - самые свежие новости\n" + \
            "/new_topics - самые свежие темы\n" + \
            "/topic - описание темы\n" + \
            "/words - 5 слов лучше всего описывающих тему\n" + \
            "/doc - текст документа\n" + \
            "/describe_doc - статистика по документу\n" + \
            "/describe_topic - статистика по теме"
    bot.send_message(message.chat.id, text)


@bot.message_handler(content_types=['text'])
def reply_to_text(message):
    if user_request[message.chat.id] == 'new_docs':
        if message.text.isdigit():
            documents = make_request.get_fresh_news(int(message.text))
            for i in range(len(documents)):
                response_text = str(i+1)+". " + documents[i].title + \
                    "\n\n" + documents[i].url
                bot.send_message(message.chat.id, response_text)
        else:
            bot.send_message(message.chat.id,
                             "Введите корректное число")

    elif user_request[message.chat.id] == 'new_topics':
        if message.text.isdigit():

            topics = make_request.get_fresh_topics(int(message.text))

            for i in range(len(topics)):
                response_text = str(i+1)+". " + topics[i].name + \
                    "\n\n" + topics[i].url
                bot.send_message(message.chat.id, response_text)

        else:
            bot.send_message(message.chat.id,
                             "Введите корректное число")

    elif user_request[message.chat.id] == 'topic':
        description = make_request.get_topic_description(message.text)

        if description is not None:
            response_text = message.text + '\n\n' + description
            bot.send_message(message.chat.id, response_text)
            documents = make_request.get_topic_fresh_news(message.text, 5)

            for i in range(len(documents)):
                response_text = str(i+1)+". " + documents[i].title + \
                    "\n\n" + documents[i].url
                bot.send_message(message.chat.id, response_text)

        else:
            bot.send_message(message.chat.id,
                             "Введите корректное название темы")

    elif user_request[message.chat.id] == 'words':
        tags = make_request.get_best_words(message.text, 5)

        if tags is not None:
            response_text = message.text + '\n\n' + '\n'.join(tags)
            bot.send_message(message.chat.id, response_text)
            del user_request[message.chat.id]

        else:
            bot.send_message(message.chat.id,
                             "Введите корректное название темы")

    elif user_request[message.chat.id] == 'doc':
        text = make_request.get_document_text(message.text)

        if text is not None:
            response_text = message.text + '\n\n' + text
            bot.send_message(message.chat.id, response_text)
            del user_request[message.chat.id]

        else:
            bot.send_message(message.chat.id,
                             "Введите корректное название документа")

    elif user_request[message.chat.id] == 'describe_doc':
        plot1_file_name = 'plot1'+str(message.chat.id)+'.png'
        plot2_file_name = 'plot2'+str(message.chat.id)+'.png'
        word_cloud_file_name = 'wcloud'+str(message.chat.id)+'.png'
        result = make_request.make_distribution_plot(message.text,
                                                     'document',
                                                     plot1_file_name,
                                                     plot2_file_name
                                                     )
        if result:
            with open(plot1_file_name, 'rb') as plot1:
                bot.send_photo(message.chat.id, plot1)
            with open(plot2_file_name, 'rb') as plot2:
                bot.send_photo(message.chat.id, plot2)
            make_request.document_word_cloud(message.text,
                                             word_cloud_file_name)
            with open(word_cloud_file_name, 'rb') as word_cloud:
                bot.send_photo(message.chat.id, word_cloud)
            os.remove(plot1_file_name)
            os.remove(plot2_file_name)
            os.remove(word_cloud_file_name)
        else:
            bot.send_message(message.chat.id,
                             "Введите корректное название документа")

    elif user_request[message.chat.id] == 'describe_topic':
        plot1_file_name = 'plot1'+str(message.chat.id)+'.png'
        plot2_file_name = 'plot2'+str(message.chat.id)+'.png'
        word_cloud_file_name = 'wcloud'+str(message.chat.id)+'.png'
        result = make_request.make_distribution_plot(message.text,
                                                     'topic',
                                                     plot1_file_name,
                                                     plot2_file_name
                                                     )
        if result:
            bot.send_message(message.chat.id,
                             "Средняя длина документа: " +
                             str(make_request.
                                 get_avg_document_len(message.text)))

            bot.send_message(message.chat.id,
                             "Всего документов: " +
                             str(make_request.
                                 get_documents_number(message.text)))

            with open(plot1_file_name, 'rb') as plot1:
                bot.send_photo(message.chat.id, plot1)
            with open(plot2_file_name, 'rb') as plot2:
                bot.send_photo(message.chat.id, plot2)
            make_request.topic_word_cloud(message.text,
                                          word_cloud_file_name)
            with open(word_cloud_file_name, 'rb') as word_cloud:
                bot.send_photo(message.chat.id, word_cloud)
            os.remove(plot1_file_name)
            os.remove(plot2_file_name)
            os.remove(word_cloud_file_name)
        else:
            bot.send_message(message.chat.id,
                             "Введите корректное название темы")


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except requests.exceptions.ReadTimeout:
            print("А вот сейчас бот упал из-за polling")
