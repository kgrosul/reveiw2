import telebot
import make_request
import requests
from collections import defaultdict
import os
import config


user_request = defaultdict(lambda: None)
bot = telebot.TeleBot('582824205:AAGaNsND2bCU6XtJ_x9VQjpzd0dNfqq3yhA')


def send_new_docs(chat_id, str_number):
    """
    Отправляет заданному пользователю определенное количество самых свежих новостей 
    или, если необходимо, просьбу ввести корректные данные 
    :param chat_id: id пользователя
    :param str_number: количество новостей
    :return: None
    """
    if str_number == '':
        str_number = str(config.DEFAULT_NEW_DOCS)
    if str_number.isdigit():
        documents = make_request.get_fresh_news(int(str_number))
        for i in range(len(documents)):
            response_text = str(i + 1) + ". " + documents[i].title + \
                            "\n\n" + documents[i].url
            bot.send_message(chat_id, response_text)
        del user_request[chat_id]
    else:
        bot.send_message(chat_id,
                         "Введите корректное число")


def send_new_topics(chat_id, str_number):
    """
    Отправляет заданному пользователю определенное количество самых свежих тем
    или, если необходимо, просьбу ввести корректные данные 
    :param chat_id: id пользователя
    :param str_number: количество тем
    :return: None
    """
    if str_number == '':
        str_number = str(config.DEFAULT_NEW_TOPICS)
    if str_number.isdigit():
        topics = make_request.get_fresh_topics(int(str_number))

        for i in range(len(topics)):
            response_text = str(i + 1) + ". " + topics[i].name + \
                            "\n\n" + topics[i].url
            bot.send_message(chat_id, response_text)
        del user_request[chat_id]

    else:
        bot.send_message(chat_id,
                         "Введите корректное число")


def send_topic_description(chat_id, topic_name):
    """
    Отправляет заданному пользователю описание определенной темы
    или, если необходимо, просьбу ввести корректные данные 
    :param chat_id: id пользователя
    :param topic_name: название темы
    :return: None
    """
    description = make_request.get_topic_description(topic_name)

    if description is not None:
        response_text = topic_name + '\n\n' + description
        bot.send_message(chat_id, response_text)
        documents = make_request.get_topic_fresh_news(topic_name, config.DEFAULT_NEW_DOCS)

        for i in range(len(documents)):
            response_text = str(i + 1) + ". " + documents[i].title + \
                            "\n\n" + documents[i].url
            bot.send_message(chat_id, response_text)
        del user_request[chat_id]


    else:
        bot.send_message(chat_id,
                         "Введите корректное название темы")


def send_words(chat_id, topic_name):
    """
    Отправляет заданному пользователю 5 слов лушче всего описывающих тем
    или, если необходимо, просьбу ввести корректные данные 
    :param chat_id: id пользователя
    :param topic_name: название темы
    :return: None
    """
    words = make_request.get_best_words(topic_name, 5)

    if words is not None:
        response_text = topic_name + '\n\n' + '\n'.join(words)
        bot.send_message(chat_id, response_text)
        del user_request[chat_id]

    else:
        bot.send_message(chat_id,
                         "Введите корректное название темы")


def send_doc_text(chat_id, doc_title):
    """
    Отправляет заданному пользователю текст документа
    или, если необходимо, просьбу ввести корректные данные 
    :param chat_id: id пользователя
    :param doc_title: название темы
    :return: None
    """
    text = make_request.get_document_text(doc_title)

    if text is not None:
        response_text = doc_title + '\n\n' + text
        bot.send_message(chat_id, response_text)
        del user_request[chat_id]

    else:
        bot.send_message(chat_id,
                         "Введите корректное название документа")


def show_statistic(chat_id, item_title):
    """
    Отправляет заданному пользователю статистику по теме или по документу
    или, если необходимо, просьбу ввести корректные данные 
    :param chat_id: id пользователя
    :param item_title: название темы/документа
    :return: None
    """
    if user_request[chat_id] == 'describe_topic':
        statistic_type = 'topic'
    else:
        statistic_type = 'document'

    plot1_file_name = 'plot1_' + str(chat_id) + '.png'
    plot2_file_name = 'plot2_' + str(chat_id) + '.png'
    word_cloud_file_name = 'wcloud' + str(chat_id) + '.png'

    if make_request.make_distribution_plot(item_title,
                                           statistic_type,
                                           plot1_file_name,
                                           plot2_file_name):
        if statistic_type == 'topic':

            bot.send_message(chat_id,
                             "Средняя длина документа: " +
                             str(make_request.
                                 get_avg_document_len(item_title)))

            bot.send_message(chat_id,
                             "Всего документов: " +
                             str(make_request.
                                 get_documents_number(item_title)))
            make_request.topic_word_cloud(item_title,
                                          word_cloud_file_name)
        else:

            make_request.document_word_cloud(item_title,
                                             word_cloud_file_name)

        with open(plot1_file_name, 'rb') as plot1:
            bot.send_photo(chat_id, plot1)
        with open(plot2_file_name, 'rb') as plot2:
            bot.send_photo(chat_id, plot2)

        with open(word_cloud_file_name, 'rb') as word_cloud:
            bot.send_photo(chat_id, word_cloud)
        os.remove(plot1_file_name)
        os.remove(plot2_file_name)
        os.remove(word_cloud_file_name)
        del user_request[chat_id]

    else:
        bot.send_message(chat_id,
                         "Введите корректное название")

# каждая команда переданная боту влечет за собой вызов определенной функциц
commands = {'new_docs': 'send_new_docs(message.chat.id, argument)',
            'new_topics': 'send_new_topics(message.chat.id, argument)',
            'topic': 'send_topic_description(message.chat.id, argument)',
            'words': 'send_words(message.chat.id, argument)',
            'doc': 'send_doc_text(message.chat.id, argument)',
            'describe_doc': 'show_statistic(message.chat.id, argument)',
            'describe_topic': 'show_statistic(message.chat.id, argument)'}


@bot.message_handler(commands=['new_docs', 'new_topics', 'topic', 'words',
                               'doc', 'describe_doc', 'describe_topic'])
def reply(message):
    """Обрабатываем сообщения, которые начинаются с команды"""
    status = message.text.split()[0][1:]
    user_request[message.chat.id] = status
    argument = message.text[len(status)+1:].strip()
    eval(commands[user_request[message.chat.id]])


@bot.message_handler(commands=['help', 'start'])
def reply_to_help_start(message):
    """Выводим справку"""
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
    """Обрабатываем сообщения без команды в начале"""
    if message.chat.id in user_request:
        argument = message.text.strip()
        eval(commands[user_request[message.chat.id]])
    else:
        bot.send_message(message.chat.id, "Введите комнаду")


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except requests.exceptions.ReadTimeout:
            print("А вот сейчас бот упал из-за polling")
