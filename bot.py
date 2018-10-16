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
    Sends str_number of fresh news to user with char_id or
    ask him to еnter the correct number
    :param chat_id: user's id
    :param str_number: amount of news
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
        bot.send_message(chat_id, config.CORRECT_NUMBER_REQUEST)


def send_new_topics(chat_id, str_number):
    """
    Sends str_number of fresh topics to user with char_id or
    ask him to еnter the correct number
    :param chat_id: user's id
    :param str_number: amount of topics
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
        bot.send_message(chat_id, config.CORRECT_NUMBER_REQUEST)


def send_topic_description(chat_id, topic_name):
    """
    Sends the description of the topic with topic_name to
    user with char_id or ask him to еnter the correct number
    :param chat_id: user's id
    :param topic_name:
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
        bot.send_message(chat_id, config.CORRECT_NAME_REQUEST)


def send_words(chat_id, topic_name):
    """
    Sends the  user 5 words best describing topics
    or ask him to еnter the correct topic name
    :param chat_id:
    :param topic_name:
    :return: None
    """
    words = make_request.get_best_words(topic_name, config.BEST_WORDS_NUM)

    if words is not None:
        response_text = topic_name + '\n\n' + '\n'.join(words)
        bot.send_message(chat_id, response_text)
        del user_request[chat_id]

    else:
        bot.send_message(chat_id, config.CORRECT_NAME_REQUEST)


def send_doc_text(chat_id, doc_title):
    """
    Sends the text of the document to the
    user or ask him to еnter the correct title
    :param chat_id:
    :param doc_title:
    :return: None
    """
    text = make_request.get_document_text(doc_title)

    if text is not None:
        response_text = doc_title + '\n\n' + text
        bot.send_message(chat_id, response_text)
        del user_request[chat_id]

    else:
        bot.send_message(chat_id, config.CORRECT_NAME_REQUEST)


def show_statistic(chat_id, item_title):
    """
    Sends the statistics on the item to the
    user or ask him to еnter the correct title
    :param chat_id:
    :param item_title: title of a document or a topic
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
                             "Average document length: " +
                             str(make_request.
                                 get_avg_document_len(item_title)))

            bot.send_message(chat_id,
                             "Total documents: " +
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
        bot.send_message(chat_id, config.CORRECT_NAME_REQUEST)

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
    """process messages that start with the command"""
    status = message.text.split()[0][1:]
    user_request[message.chat.id] = status
    eval(commands[user_request[message.chat.id]])


@bot.message_handler(commands=['help', 'start'])
def reply_to_help_start(message):
    """process messages that start with the help command"""
    bot.send_message(message.chat.id, config.HELP)


@bot.message_handler(content_types=['text'])
def reply_to_text(message):
    """process messages that start with no commands"""
    if message.chat.id in user_request:
        eval(commands[user_request[message.chat.id]])
    else:
        bot.send_message(message.chat.id, "Insert the command")


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except requests.exceptions.ReadTimeout:
            print("ReadTimeout")
