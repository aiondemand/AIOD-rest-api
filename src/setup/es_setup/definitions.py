BASE_MAPPING = {
    "mappings": {
        "properties": {
            "date_modified": {"type": "date"},
            "identifier": {"type": "long"},
            "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "platform": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "description_plain": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "description_html": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
        }
    }
}
