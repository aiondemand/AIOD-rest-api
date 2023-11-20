import os

from elasticsearch import Elasticsearch


class ElasticsearchSingleton:
    """
    Making sure the Elasticsearch client is created only once, and easy to patch for
    unittests.
    """

    __monostate = None

    def __init__(self):
        if not ElasticsearchSingleton.__monostate:
            ElasticsearchSingleton.__monostate = self.__dict__
            user = os.getenv("ES_USER", "")
            pw = os.getenv("ES_PASSWORD", "")
            self.client = Elasticsearch("http://elasticsearch:9200", basic_auth=(user, pw))
        else:
            self.__dict__ = ElasticsearchSingleton.__monostate

    def patch(self, elasticsearch: Elasticsearch):
        self.__monostate["client"] = elasticsearch  # type:ignore
