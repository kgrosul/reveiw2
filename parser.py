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
    Парсит темы и при необходимости добавляет их в базу данных
    :return: None
    """
    session = requests.Session()
    session.max_redirects = config.redirects
    data = BeautifulSoup(session.get("https://www.rbc.ru/story/").text, 'lxml')
    # собираем все темы
    topics = data.find_all('div', {'class': 'item item_story js-story-item'})
    for topic in topics:
        url = topic.find('a', {'class': 'item__link no-injects'})['href'].\
            strip()
        title = topic.find('span', {'class': 'item__title'}).text.strip()
        description = topic.find('span', {'class': 'item__text'}).text.strip()
        # проверяем, что темы еще нет в базе данных
        if len(Topic.select().where(Topic.url == url)) == 0:
            Topic.create(url=url,
                         name=title,
                         description=description)
        # или что у неё изменилось описание
        elif Topic.select().where(Topic.url == url).\
                get().description != description:
            Topic.update(description=description).\
                where(Topic.url == url).execute()


def get_document_text_and_tags(url):
    """
    Собирает текст и теги
    :param url: url статьи
    :return: словарь, в котором по ключу text находитcя текст,
             а по ключу tag - кортеж тегов
    """
    session = requests.Session()
    session.max_redirects = config.redirects
    data = BeautifulSoup(session.get(url).text, 'lxml')
    paragraphs = data.find_all('p')
    text = ' '.join(map(lambda paragraph: paragraph.text, paragraphs))
    """Оказалось, что некотрые новости имеют другую html-разметку
    В таким случае получаем текст по ней"""
    if len(text) == 0:
        paragraphs = data.find_all('div', {'class': 'article__text'})
        text = ' '.join(map(lambda paragraph: paragraph.text, paragraphs))

    tags = data.find_all('', {'class': 'article__tags__link'})
    return {'text': text, 'tags': tuple(map(lambda tag: tag.text, tags))}


def calculate_statistic(text):
    """
    Считает статистику для данного текста
    :param text: сам текст
    :return: словарь, в котором по ключу length находитcя распределение длин,
             а по ключу occurrence - распределение встречаемости
    """
    words = re.findall(r'\w+', text)
    lengths = defaultdict(lambda: 0)
    occurrences_per_word = defaultdict(lambda: 0)
    occurrences = defaultdict(lambda: 0)

    for word in words:
        lengths[len(word)] += 1
        occurrences_per_word[word] += 1

    # Cчитаем среднеквадратичное отклонение
    avg_occurrences_num = sum(occurrences_per_word.values())/len(occurrences_per_word)
    deviation = 0
    for word in occurrences_per_word:
        deviation += (avg_occurrences_num - occurrences_per_word[word])**2

    deviation = (deviation/len(occurrences_per_word))**0.5
    print(deviation)
    for word in occurrences_per_word:
        # Учитываем только те слова, значение для которых попадают нужный промежуток частотности
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
    собирает и сохраняет статистику для документа в базу данных
    :param document: документ
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
        print("Возникла проблема с save_document_statistic, url=",
              document.url)


def save_topic_statistic(topic_name):
    """
    Собиорает и сохраняет статистику по данной теме в базу данных
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
        print("Возникла проблема с save_topic_statistic, url =", topic_name)

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
    Парсит все документы для данной темы
    и при необходимости добавляет их в базу данных
    :param topic_name: название темы
    :return: None
    """
    topic = Topic.select().where(Topic.name == topic_name)

    if len(topic) == 0:
        return

    topic_url = topic.get().url
    session = requests.Session()
    session.max_redirects = config.redirects
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
        """Проверям, что в базе данных нет
        документа с таким url или его надо обновить"""
        if len(Document.select().where(
                                Document.url == url and
                                Document.last_update == last_update)) == 0:
            """ Запоминаем, что необходимо пересчитать
            статистику по теме документа"""
            updated_topics.add(topic_name)
            """Удаляем теги, связанные с данным документом,
            ведь они могли измениться"""
            Tag.delete().where(Tag.document == Document.select().
                               where(Document.url == url)).execute()
            # Удаляем предыдущую статистику
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
            # Получаем статистику
            save_document_statistic(new_document)
            # Добавляем необходимые теги
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
