import telebot
import make_request
import requests
from collections import defaultdict
import os


user_request = defaultdict(lambda: None)
bot = telebot.TeleBot('582824205:AAGaNsND2bCU6XtJ_x9VQjpzd0dNfqq3yhA')


def send_new_docs(message):
    """
    Отпраляет самые свежие документы
    :param message: сообщение, в котором содержится информация о чате
    :return: None
    """
    if message.text.isdigit():
        documents = make_request.get_fresh_news(int(message.text))
        for i in range(len(documents)):
            response_text = str(i + 1) + ". " + documents[i].title + \
                            "\n\n" + documents[i].url
            bot.send_message(message.chat.id, response_text)
    else:
        bot.send_message(message.chat.id,
                         "Введите корректное число")


def send_new_topics(message):
    """
    Отпраляет самые свежие темы
    :param message: сообщение, в котором содержится информация о чате
    :return: None
    """
    if message.text.isdigit():
        topics = make_request.get_fresh_topics(int(message.text))

        for i in range(len(topics)):
            response_text = str(i + 1) + ". " + topics[i].name + \
                            "\n\n" + topics[i].url
            bot.send_message(message.chat.id, response_text)
    else:
        bot.send_message(message.chat.id,
                         "Введите корректное число")


def send_topic_description(message):
    """
    Отпраляет описание темы и 5 свежих новостей из нее
    :param message: сообщение, в котором содержится информация о чате
    :return: None
    """
    description = make_request.get_topic_description(message.text)

    if description is not None:
        response_text = message.text + '\n\n' + description
        bot.send_message(message.chat.id, response_text)
        documents = make_request.get_topic_fresh_news(message.text, 5)

        for i in range(len(documents)):
            response_text = str(i + 1) + ". " + documents[i].title + \
                            "\n\n" + documents[i].url
            bot.send_message(message.chat.id, response_text)

    else:
        bot.send_message(message.chat.id,
                         "Введите корректное название темы")


def send_words(message):
    """
    Отпраляет 5 слов лучше всего описывающих данную тему
    :param message: сообщение, в котором содержится информация о чате
    :return: None
    """
    tags = make_request.get_best_words(message.text, 5)

    if tags is not None:
        response_text = message.text + '\n\n' + '\n'.join(tags)
        bot.send_message(message.chat.id, response_text)
    else:
        bot.send_message(message.chat.id,
                         "Введите корректное название темы")


def send_doc_text(message):
    """
    Отпраляет текст документа
    :param message: сообщение, в котором содержится информация о чате
    :return: None
    """
    text = make_request.get_document_text(message.text)

    if text is not None:
        response_text = message.text + '\n\n' + text
        bot.send_message(message.chat.id, response_text)

    else:
        bot.send_message(message.chat.id,
                         "Введите корректное название документа")


def describe_doc(message):
    """
    Отпраляет статистику по документу
    :param message: сообщение, в котором содержится информация о чате
    :return: None
    """
    plot1_file_name = 'plot1' + str(message.chat.id) + '.png'
    plot2_file_name = 'plot2' + str(message.chat.id) + '.png'
    word_cloud_file_name = 'wcloud' + str(message.chat.id) + '.png'
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


def describe_topic(message):
    """
    Отпраляет статистику по теме
    :param message: сообщение, в котором содержится информация о чате
    :return: None
    """
    plot1_file_name = 'plot1' + str(message.chat.id) + '.png'
    plot2_file_name = 'plot2' + str(message.chat.id) + '.png'
    word_cloud_file_name = 'wcloud' + str(message.chat.id) + '.png'
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

replies = {'new_docs': 'Сколько документов надо вывести?',
           'new_topics': 'Сколько тем надо вывести?',
           'topic': 'Описание какой темы вы хотите узнать?',
           'words': 'Cлова для какой темы вы хотите узнать?',
           'doc': 'Текст какого документа надо вывести?',
           'describe_doc': 'Статистику по какому документу надо вывести?',
           'describe_topic': 'Статистику по какой теме надо вывести?'}


@bot.message_handler(commands=['new_docs', 'new_topics', 'topic', 'words',
                               'doc', 'describe_doc', 'describe_topic'])
def reply_to_new_docs(message):
    status = message.text.split()[0][1:]
    user_request[message.chat.id] = status
    bot.send_message(message.chat.id, replies[status])


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


commands = {'new_docs': 'send_new_docs(message)',
            'new_topics': 'send_new_topics(message)',
            'topic': 'send_topic_description(message)',
            'words': 'send_words(message)',
            'doc': 'send_doc_text(message)',
            'describe_doc': 'describe_doc(message)',
            'describe_topic': 'describe_topic(message)'}


@bot.message_handler(content_types=['text'])
def reply_to_text(message):
    if message.chat.id in user_request:
        eval(commands[user_request[message.chat.id]])
        del user_request[message.chat.id]
    else:
        bot.send_message(message.chat.id, "Введите комнаду")


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except requests.exceptions.ReadTimeout:
            print("А вот сейчас бот упал из-за polling")
