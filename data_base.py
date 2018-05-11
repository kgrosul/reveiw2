import peewee


data_base = peewee.SqliteDatabase('data_base.db')


class Topic(peewee.Model):
    name = peewee.CharField(unique=True, primary_key=True)
    url = peewee.CharField()
    description = peewee.CharField()

    class Meta:
        database = data_base


class Document(peewee.Model):
    topic = peewee.ForeignKeyField(Topic)
    title = peewee.CharField()
    url = peewee.CharField()
    text = peewee.TextField()
    last_update = peewee.DateTimeField()

    class Meta:
        database = data_base


class Tag(peewee.Model):
    document = peewee.ForeignKeyField(Document)
    name = peewee.CharField()

    class Meta:
        database = data_base


class DocumentStatistic(peewee.Model):
    document = peewee.ForeignKeyField(Document)
    length_distribution = peewee.CharField()
    occurrences_distribution = peewee.CharField()

    class Meta:
        database = data_base


class TopicStatistic(peewee.Model):
    topic = peewee.ForeignKeyField(Topic)
    avg_document_len = peewee.IntegerField()
    documents_number = peewee.IntegerField()
    length_distribution = peewee.CharField()
    occurrences_distribution = peewee.CharField()

    class Meta:
        database = data_base
