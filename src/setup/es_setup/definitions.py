BASE_MAPPING = {
    "mappings": {
        "properties": {
            "date_modified": {"type": "date"},
            "identifier": {"type": "long"},
            "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "plain": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "html": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
        }
    }
}
