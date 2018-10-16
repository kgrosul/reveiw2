import dateparser
import requests
from bs4 import BeautifulSoup
import locale
from data_base import Topic, Document, Tag, \
    data_base, TopicStatistic, DocumentStatistic
from collections import defaultdict
import re
import json
import config


updated_topics = set()


def parse_and_save_topics():
    """
    parses topics and, if necessary, adds them to the database
    :return: None
    """
    session = requests.Session()
    session.max_redirects = config.REDIRECTS
    data = BeautifulSoup(session.get("https://www.rbc.ru/story/").text, 'lxml')
    # collects all of the topics
    topics = data.find_all('div', {'class': 'item item_story js-story-item'})
    for topic in topics:
        url = topic.find('a', {'class': 'item__link no-injects'})['href'].\
            strip()
        title = topic.find('span', {'class': 'item__title'}).text.strip()
        description = topic.find('span', {'class': 'item__text'}).text.strip()
        # checks that the theme is not yet in the database
        if len(Topic.select().where(Topic.url == url)) == 0:
            Topic.create(url=url,
                         name=title,
                         description=description)
        # or that her description changed.
        elif Topic.select().where(Topic.url == url).\
                get().description != description:
            Topic.update(description=description).\
                where(Topic.url == url).execute()


def get_document_text_and_tags(url):
    """
    :param url: url of the document
    :return:  {text1 : (tag1, tag2, tag3...)}
    """
    session = requests.Session()
    session.max_redirects = config.REDIRECTS
    data = BeautifulSoup(session.get(url).text, 'lxml')
    paragraphs = data.find_all('p')
    text = ' '.join(map(lambda paragraph: paragraph.text, paragraphs))
    if len(text) == 0:
        paragraphs = data.find_all('div', {'class': 'article__text'})
        text = ' '.join(map(lambda paragraph: paragraph.text, paragraphs))

    tags = data.find_all('', {'class': 'article__tags__link'})
    return {'text': text, 'tags': tuple(map(lambda tag: tag.text, tags))}


def calculate_statistic(text):
    """
    :param text:
    :return: a dictionary that uses the length key to determine the length distribution,
             and on the key occurrence - distribution of occurrence
    """
    words = re.findall(r'\w+', text)
    lengths = defaultdict(lambda: 0)
    occurrences_per_word = defaultdict(lambda: 0)
    occurrences = defaultdict(lambda: 0)

    for word in words:
        lengths[len(word)] += 1
        occurrences_per_word[word] += 1

    # calculates the standard deviation
    avg_occurrences_num = sum(occurrences_per_word.values())/len(occurrences_per_word)
    deviation = 0
    for word in occurrences_per_word:
        deviation += (avg_occurrences_num - occurrences_per_word[word])**2

    deviation = (deviation/len(occurrences_per_word))**0.5
    for word in occurrences_per_word:
        """takes into account only those words, the meaning of which fall 
        the desired frequency range"""
        if abs(avg_occurrences_num - occurrences_per_word[word]) < 3*deviation:
            occurrences[occurrences_per_word[word]] += 1

    max_length = max(lengths.keys()) + 1

    max_occurrence = max(occurrences.keys()) + 1
    occurrences_list = [0] * max_occurrence
    lengths_list = [0] * max_length
    for length in lengths:
        lengths_list[length] = lengths[length]

    for occurrence in occurrences:
        occurrences_list[occurrence] = occurrences[occurrence]

    return {'length': lengths_list,
            'occurrence': occurrences_list}


def save_document_statistic(document):
    """
    collects and stores statistics for a document in the database
    :param document:
    :return: None
    """
    try:
        statistic = calculate_statistic(document.text)
        DocumentStatistic.create(document=document,
                                 length_distribution=json.
                                 dumps(statistic['length']),
                                 occurrences_distribution=json.
                                 dumps(statistic['occurrence'])
                                 )
    except ValueError:
        print("problem with save_document_statistic, url=",
              document.url)


def save_topic_statistic(topic_name):
    """
    collects and save statistics on this topic in the database
    :param topic_name: название темы
    :return: None
    """
    documents = Document.select().where(Document.topic == Topic.select().
                                        where(Topic.name == topic_name))
    avg_length = 0
    for document in documents:
        avg_length += len(re.findall(r'\w+', document.text))
    try:
        avg_length /= len(documents)
    except ZeroDivisionError:
        avg_length = 0
        print("problem with save_topic_statistic, url =", topic_name)

    text = ' '.join(document.text for document in documents)

    statistic = calculate_statistic(text)
    topic = Topic.select().where(Topic.name == topic_name).get()
    TopicStatistic.create(topic=topic,
                          avg_document_len=avg_length,
                          documents_number=len(documents),
                          length_distribution=json.
                          dumps(statistic['length']),
                          occurrences_distribution=json.
                          dumps(statistic['occurrence'])
                          )


def parse_ans_save_documents(topic_name):
    """
    parses all documents for this topic
    and if necessary, add them to the database
    :param topic_name:
    :return: None
    """
    topic = Topic.select().where(Topic.name == topic_name)

    if len(topic) == 0:
        return

    topic_url = topic.get().url
    session = requests.Session()
    session.max_redirects = config.REDIRECTS
    data = BeautifulSoup(session.get(topic_url).text, 'lxml')
    documents = data.\
        find_all('div', {'class': 'item item_story-single js-story-item'})

    for document in documents:
        url = document.find(
            'a', {'class': 'item__link no-injects js-yandex-counter'}
        )['href'].strip()

        title = document.find('span', {'class': 'item__title'}).text.strip()
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
        last_update = dateparser.parse(document.
                                       find('span', {'class': 'item__info'}).
                                       text, languages=['ru'])
        """checks that the database has no documents with such
        url or it needs to be updated"""
        if len(Document.select().where(
                                Document.url == url and
                                Document.last_update == last_update)) == 0:
            """remembers that we need to recalculate
            statistics on the subject of the document"""
            updated_topics.add(topic_name)
            """removes tags related to this document because 
            they could change"""
            Tag.delete().where(Tag.document == Document.select().
                               where(Document.url == url)).execute()
            # removes previous statistics
            DocumentStatistic.delete().\
                where(DocumentStatistic.document == Document.select().
                      where(Document.url == url)).execute()
            Document.delete().where(Document.url == url).execute()
            page = get_document_text_and_tags(url)
            text = page['text']
            cur_top = Topic.select().where(Topic.name == topic_name).get()

            new_document = Document(url=url,
                                    title=title,
                                    topic=cur_top,
                                    ast_update=last_update,
                                    text=text,
                                    last_update=last_update)

            new_document.save()
            # gets statistics
            save_document_statistic(new_document)
            # adds tags
            for tag in page['tags']:
                Tag.create(document=new_document, name=tag)


if __name__ == '__main__':
    data_base.connect()
    data_base.create_tables([Document,
                             Tag,
                             Topic,
                             DocumentStatistic,
                             TopicStatistic])
    parse_and_save_topics()
    for topic in Topic.select():
        parse_ans_save_documents(topic.name)

    for topic_name in updated_topics:
        TopicStatistic.delete().\
            where(TopicStatistic.topic == Topic.select().
                  where(Topic.name == topic_name)).execute()
        save_topic_statistic(topic_name)
