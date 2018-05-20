from data_base import Topic, \
    Document, TopicStatistic, \
    DocumentStatistic, Tag

from peewee import fn
from collections import defaultdict
import pandas as pd
import json
import matplotlib
import wordcloud
import config
import stop_words
import pymorphy2
import re


matplotlib.use('Agg')

import matplotlib.pyplot as plt


def get_fresh_news(number):
    """
    Получить самые свежие новости
    :param number: количество новостей
    :return: список из объектов типа <class 'data_base.Document'>
    """
    return [document for document in Document.select().
            order_by(-Document.last_update)][:number]


def get_fresh_topics(number):
    """
    Получить самые свежие темы
    :param number: количество тем
    :return: список из объектов типа <class 'data_base.Topic'>
    """
    topics = Topic().select().join(Document).\
        where(Topic.name == Document.topic and
              Document.last_update ==
              Document().select(fn.Max(Document.last_update)).
              where(Document.topic == Topic.name)).\
        order_by(-Document.last_update)
    return [topic for topic in topics][:number]


def get_topic_description(topic_name):
    """
    Опсание темы
    :param topic_name: заголовок темы
    :return: описание или None, если темы не существует
    """
    response = Topic.select().where(Topic.name == topic_name)
    if len(response) == 0:
        return None
    return response.get().description


def get_topic_fresh_news(topic_name, number):
    """
    Получить самые свежие новости для данной темы
    :param topic_name: название темы
    :param number: количество новостей
    :return: список из объектов типа <class 'data_base.Document'> или None,
            если темы не существует
    """
    if len(Topic.select().where(Topic.name == topic_name)) == 0:
        return None
    return [news for news in Document.select().
            where(Document.topic == topic_name).
            order_by(-Document.last_update)][:number]


def get_document_text(document_title):
    """
    Получить текст данного документа
    :param document_title: заголовог документа
    :return: текст или None, если документа не существует
    """
    if len(Document.select().
            where(Document.title == document_title)) == 0:
        return None
    return Document.select().\
        where(Document.title == document_title).get().text


def make_plot(data, label, xlabel, ylabel):
    """
    Создает график и возвращает его
    :param data: данные в виде dict
    :param label: название графика
    :param xlabel: название оси X
    :param ylabel: название оси Y
    """

    data_frame = pd.DataFrame(data)
    plot = data_frame.plot(kind="bar",
                           title=label,
                           colormap='jet',
                           legend=None)

    plot.set_xlabel(xlabel)
    plot.set_ylabel(ylabel)
    plot.set_xlim(1)

    return plot


def make_distribution_plot(title_or_name, object, file_name1, file_name2):
    """
    Создает графики распределения для документа/темы
    :param title_or_name: название
    :param object: 'document' или 'topic'
    :param file_name1: файл, куда сохранить первый график
    :param file_name2: файл, куда сохранить второй график
    :return: True - в случае удачного выполнения, False - иначе
    """
    if object == 'document':
        statistic = DocumentStatistic.select().\
            where(DocumentStatistic.document == Document.select().
                  where(Document.title == title_or_name))
    elif object == 'topic':
        statistic = TopicStatistic.select().\
            where(TopicStatistic.topic == Topic.select().
                  where(Topic.name == title_or_name))
    else:
        return False
    if len(statistic) == 0:
        return False
    make_plot(data=json.loads(statistic.get().length_distribution),
              label="Распределение длины",
              xlabel='Длина слова',
              ylabel='Количество слов с такой длиной'
              )

    plt.savefig(file_name1)
    plt.close()

    make_plot(data=[0] + json.loads(statistic.get().
                              occurrences_distribution)[config.min_occurrence:
                                                        config.max_occurrence],
              label="Распределение частот слов",
              xlabel='Встречаемость слова',
              ylabel='Количество слов с такой встречаемостью'
              )
    plt.savefig(file_name2)

    return True


def get_documents_number(topic_name):
    """
    Получить количество документов в теме
    :param topic_name: название темы
    :return: количество документов или None, если темы не существует
    """
    statistic = TopicStatistic.select().\
        where(TopicStatistic.topic == Topic.select().
              where(Topic.name == topic_name))
    if len(statistic) == 0:
        return None
    return statistic.get().documents_number


def get_avg_document_len(topic_name):
    """
    Получить среднюю длину документа теме
    :param topic_name: название темы
    :return: средяя длина или None, если темы не существует
    """
    statistic = TopicStatistic.select().\
        where(TopicStatistic.topic == Topic.select().
              where(Topic.name == topic_name))
    if len(statistic) == 0:
        return None
    return statistic.get().avg_document_len


def get_best_words(topic_name, number):
    """
    Возвращает слова лучше всего описывающее эту тему
    :param topic_name: название темы
    :param number: количество слов
    :return: list из тегов или None, если темы не существует
    """
    if len(Topic.select().where(Topic.name == topic_name)) == 0:
        return None
    documents = Document.select().\
        where(Document.topic == Topic.select().
              where(Topic.name == topic_name))
    word_occurrence = defaultdict(lambda: 0)
    words = re.findall(r'\w+', ' '.join(document.title for document in documents))
    morph = pymorphy2.MorphAnalyzer()
    for word in words:
        morph_information = morph.parse(word)[0]
        if 'NOUN' in morph_information.tag or 'UNKN' in morph_information.tag:
            word_occurrence[str(morph_information.normal_form)] += 1

    word_list = [word for word in word_occurrence]
    word_list.sort(key=lambda tag: -word_occurrence[tag])
    return word_list[:number]


def make_word_cloud(text, file_name):
    """
    Строит облако слов по данному тексту
    :param text: текст
    :param file_name: файл, в который нужно сохранить облако
    :return: None
    """
    stopwords = set(stop_words.get_stop_words('ru'))
    word_cloud = wordcloud.WordCloud(max_words=config.cloud_max_words,
                                     height=config.picture_height,
                                     width=config.picture_width,
                                     background_color='white',
                                     stopwords=stopwords).generate(text)

    image = word_cloud.to_image()
    image.save(file_name)


def topic_word_cloud(topic_name, file_name):
    """
    Строит облако слов по всем документам данной темы
    :param topic_name: название темы
    :param file_name: файл, в который нужно сохранить облако
    :return: True при удачном выполнении, False - иначе
    """
    documents = Document.select().\
        where(Document.topic == Topic.select().
              where(Topic.name == topic_name))
    if len(documents) == 0:
        return False
    text = ' '.join(document.text for document in documents)
    make_word_cloud(text, file_name)
    return True


def document_word_cloud(document_title, file_name):
    """
    Строит облако слов по тексту данного документа
    :param document_title: заголовок документа
    :param file_name: файл, в который нужно сохранить облако
    :return: True при удачном выполнении, False - иначе
    """
    document = Document.select().where(Document.title == document_title)
    if len(document) == 0:
        return False
    text = document.get().text
    make_word_cloud(text, file_name)
    return True


print(get_best_words("Война санкций", 5))
