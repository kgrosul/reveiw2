import dateparser
import requests
from bs4 import BeautifulSoup
import locale
from data_base import Topic, Document, Tag, data_base, TopicStatistic, DocumentStatistic
from collections import defaultdict
import re
import json


updated_topics = set()


def parse_and_save_topics():
    data = BeautifulSoup(requests.get("https://www.rbc.ru/story/").text, 'lxml')
    topics = data.find_all('div', {'class': 'item item_story js-story-item'})
    for topic in topics:
        url = topic.find('a', {'class': 'item__link no-injects'})['href'].strip()
        title = topic.find('span', {'class': 'item__title'}).text.strip()
        description = topic.find('span', {'class': 'item__text'}).text.strip()
        if len(Topic.select().where(Topic.url == url)) == 0:
            Topic.create(url=url,
                         name=title,
                         description=description)


def get_document_text_and_tags(url):
    data = BeautifulSoup(requests.get(url).text, 'lxml')
    paragraphs = data.find_all('p')
    text = ' '.join(map(lambda paragraph: paragraph.text, paragraphs))
    if len(text) == 0:
        paragraphs = data.find_all('div', {'class': 'article__text'})
        text = ' '.join(map(lambda paragraph: paragraph.text, paragraphs))

    tags = data.find_all('', {'class': 'article__tags__link'})
    return {'text': text, 'tags': tuple(map(lambda tag: tag.text, tags))}


def calculate_statistic(text):
    words = re.findall(r'\w+', text)
    lengths = defaultdict(lambda: 0)
    occurrences_per_word = defaultdict(lambda: 0)
    occurrences = defaultdict(lambda: 0)
    for word in words:
        lengths[len(word)] += 1
        occurrences_per_word[word] += 1

    for word in occurrences_per_word:
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
    try:
        statistic = calculate_statistic(document.text)
    except ValueError:
        print("Возникла проблема с save_document_statistic, url=", document.url)

    DocumentStatistic.create(document=document,
                             length_distribution=json.dumps(statistic['length']),
                             occurrences_distribution=json.dumps(statistic['occurrence'])
                             )


def add_distribution(final_distribution, distribution):
    for i in range(len(distribution)):
        if i < len(final_distribution):
            final_distribution[i] += distribution[i]
        else:
            final_distribution += [distribution[i]]


def save_topic_statistic(topic_name):
    documents = Document.select().where(Document.topic == Topic.select().
                                        where(Topic.name == topic_name))
    avg_length = 0
    for document in documents:
        avg_length += len(re.findall(r'\w+', document.text))
    try:
        avg_length /= len(documents)
    except ZeroDivisionError:
        avg_length = 0
        print("Возникла проблема с save_topic_statistic, url =", topic.url)

    length_distribution = []
    occurrences_distribution = []

    for document in documents:
        add_distribution(length_distribution, json.loads(DocumentStatistic.select().
                         where(DocumentStatistic.document == document).get().length_distribution))

        add_distribution(occurrences_distribution, json.loads(DocumentStatistic.select().
                         where(DocumentStatistic.document == document).get().occurrences_distribution))
    topic = Topic.select().where(Topic.name == topic_name).get()
    TopicStatistic.create(topic=topic,
                          avg_document_len=avg_length,
                          documents_number=len(documents),
                          length_distribution=json.dumps(length_distribution),
                          occurrences_distribution=json.dumps(occurrences_distribution)
                          )


def clear_topics():
    topics = Topic.select()
    for topic in topics:
        if len(Document.select().where(Document.topic == topic)) == 0:
            print(topic.name)
            updated_topics.discard(topic.name)
            Topic.delete().where(Topic.name == topic.name).execute()


def parse_ans_save_documents(topic_name):
    topic = Topic.select().where(Topic.name == topic_name)

    if len(topic) == 0:
        return

    topic_url = topic.get().url
    data = BeautifulSoup(requests.get(topic_url).text, 'lxml')
    documents = data.find_all('div', {'class': 'item item_story-single js-story-item'})

    for document in documents:
        url = document.find('a', {'class': 'item__link no-injects js-yandex-counter'})['href'].strip()
        title = document.find('span', {'class': 'item__title'}).text.strip()
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
        last_update = dateparser.parse(document.find('span', {'class': 'item__info'}).text, languages=['ru'])

        if len(Document.select().where(Document.url == url and Document.last_update == last_update)) == 0:
            updated_topics.add(Topic)
            Tag.delete().where(Tag.document == Document.select().where(Document.url == url)).execute()
            DocumentStatistic.delete().where(DocumentStatistic.document == Document.select().where(Document.url == url)).execute()
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

            save_document_statistic(new_document)

            for tag in page['tags']:
                Tag.create(document=new_document, name=tag)


if __name__ == '__main__':
    data_base.connect()
    data_base.create_tables([Document, Tag, Topic, DocumentStatistic, TopicStatistic])
    parse_and_save_topics()
    for topic in Topic.select():
        parse_ans_save_documents(topic.name)

    for topic_name in updated_topics:
        TopicStatistic.delete().where(TopicStatistic.topic == Topic.select().
                                      where(Topic.name == topic_name)).execute()
