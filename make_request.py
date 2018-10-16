from data_base import Topic, \
    Document, TopicStatistic, \
    DocumentStatistic, Tag

from peewee import fn
from collections import defaultdict
import pandas as pd
import json
import wordcloud
import config
import stop_words
import pymorphy2
import re
import matplotlib.pyplot as plt


def get_fresh_news(number):
    """
    :param number: number of the news
    :return: list of <class 'data_base.Document'>
    """
    return [document for document in Document.select().
            order_by(-Document.last_update)][:number]


def get_fresh_topics(number):
    """
    :param number: number of the topics
    :return: list of <class 'data_base.Topic'>
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
    :param topic_name:
    :return: string with description or None if the topic doesn't exist
    """
    response = Topic.select().where(Topic.name == topic_name)
    if len(response) == 0:
        return None
    return response.get().description


def get_topic_fresh_news(topic_name, number):
    """
    gets the freshest news for the topic
    :param topic_name:
    :param number:
    :return: list of <class 'data_base.Document'> or None if the topic doesn't exist
    """
    if len(Topic.select().where(Topic.name == topic_name)) == 0:
        return None
    return [news for news in Document.select().
            where(Document.topic == topic_name).
            order_by(-Document.last_update)][:number]


def get_document_text(document_title):
    """
    :param document_title:
    :return: string with the text or None if the document doesn't exist
    """
    if len(Document.select().
            where(Document.title == document_title)) == 0:
        return None
    return Document.select().\
        where(Document.title == document_title).get().text


def make_plot(data, label, xlabel, ylabel):
    """
    creates the plot and return them
    :param data: dict of data
    :param label: label of the plot
    :param xlabel:  X axis label
    :param ylabel: Y axis label
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
    creates plot of the distribution for the document/topic
    :param title_or_name:
    :param object: 'document' or 'topic'
    :param file_name1: file to save first plot
    :param file_name2: file to save second plot
    :return: True - everything is OK, False - something went wrong
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
              label='The length distribution',
              xlabel="Word's length",
              ylabel='Number of words with such length'
              )

    plt.savefig(file_name1)
    plt.close()

    make_plot(data=[0] + json.
              loads(statistic.get().
                    occurrences_distribution)[config.MIN_OCCURRENCE:
                                              config.MAX_OCCURRENCE],
              label="The frequency distribution of words",
              xlabel='The frequency of the word',
              ylabel='The number of words with that frequency'
              )
    plt.savefig(file_name2)

    return True


def get_documents_number(topic_name):
    """
    gets number of documents in the topic
    :param topic_name:
    :return: number of documents or None if the topic doesn't exist
    """
    statistic = TopicStatistic.select().\
        where(TopicStatistic.topic == Topic.select().
              where(Topic.name == topic_name))
    if len(statistic) == 0:
        return None
    return statistic.get().documents_number


def get_avg_document_len(topic_name):
    """
    gets the average length of a topic document
    :param topic_name
    :return: the average length or None if the topic doesn't exist
    """
    statistic = TopicStatistic.select().\
        where(TopicStatistic.topic == Topic.select().
              where(Topic.name == topic_name))
    if len(statistic) == 0:
        return None
    return statistic.get().avg_document_len


def get_best_words(topic_name, number):
    """
    gets the words that best describe the topic
    :param topic_name:
    :param number: number of words
    :return: list of tags or None if the topic doesn't exist
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
    builds a cloud of words on this text
    :param text:
    :param file_name: file to save the wordcloud
    :return: None
    """
    stopwords = set(stop_words.get_stop_words('ru'))

    word_cloud = wordcloud.WordCloud(max_words=config.CLOUD_MAX_WORDS,
                                     height=config.PICTURE_HEIGHT,
                                     width=config.PICTURE_WIDTH,
                                     background_color='white',
                                     stopwords=stopwords).generate(text)

    image = word_cloud.to_image()
    image.save(file_name)


def topic_word_cloud(topic_name, file_name):
    """
    builds a word cloud across all documents in a given topic
    :param topic_name:
    :param file_name: file to save the wordcloud
    :return: True - everything is OK, False - something went wrong
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
    Build a word cloud across the text of this document
    :param document_title:
    :param file_name: file to save the wordcloud
    :return: True - everything is OK, False - something went wrong
    """
    document = Document.select().where(Document.title == document_title)
    if len(document) == 0:
        return False
    text = document.get().text
    make_word_cloud(text, file_name)
    return True
