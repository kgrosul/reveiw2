from data_base import Topic, Document, TopicStatistic, DocumentStatistic, Tag, data_base
from peewee import fn
from collections import defaultdict
import pandas as pd
import json
import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt


def get_fresh_news(number):
    return [document for document in Document.select().order_by(-Document.last_update)][:number]


def get_fresh_topics(number):
    topics = Topic().select().join(Document).\
        where(Topic.name == Document.topic and
              Document.last_update ==
              Document().select(fn.Max(Document.last_update)).where(Document.topic == Topic.name)).\
        order_by(-Document.last_update)
    return [topic for topic in topics][:number]


def get_topic_description(topic_name):
    response = Topic.select().where(Topic.name == topic_name)
    if len(response) == 0:
        return None
    return response.get().description


def get_topic_fresh_news(topic_name, number):
    if len(Topic.select().where(Topic.name == topic_name)) == 0:
        return None
    return [news for news in Document.select().
            where(Document.topic == topic_name).order_by(-Document.last_update)][:number]


def get_document_text(document_title):
    if len(Document.select().where(Document.title == document_title)) == 0:
        return None
    return Document.select().where(Document.title == document_title).get().text


def make_plot(data, label, xlabel, ylabel):
    data_frame = pd.DataFrame(data)
    plot = data_frame.plot(kind="line",
                           title=label,
                           colormap='jet')

    plot.set_xlabel(xlabel)
    plot.set_ylabel(ylabel)

    return plot


def make_distribution_plot(title_or_name, object, file_name1, file_name2):
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

    make_plot(data=json.loads(statistic.get().occurrences_distribution),
              label="Распределение частот слов",
              xlabel='Встречаемость слова',
              ylabel='Количество слов с такой встречаемостью'
              )
    plt.savefig(file_name2)

    return True


def get_documents_number(topic_name):

    statistic = TopicStatistic.select().\
        where(TopicStatistic.topic == Topic.select().
              where(Topic.name == topic_name))
    if len(statistic) == 0:
        return None
    return statistic.get().documents_number


def get_avg_document_len(topic_name):
    statistic = TopicStatistic.select().\
        where(TopicStatistic.topic == Topic.select().
              where(Topic.name == topic_name))
    if len(statistic) == 0:
        return None
    return statistic.get().avg_document_len


def get_best_words(topic_name, number):
    if len(Topic.select().where(Topic.name == topic_name)) == 0:
        return None
    documents = Document.select().where(Document.topic == Topic.select().where(Topic.name == topic_name))
    tags_dict = defaultdict(lambda: 0)
    for document in documents:
        for tag in Tag.select().where(Tag.document == document):
            tags_dict[tag.name] += 1

    tag_list = [tag for tag in tags_dict]
    tag_list.sort(key=lambda tag: -tags_dict[tag])
    return tag_list[:number]
