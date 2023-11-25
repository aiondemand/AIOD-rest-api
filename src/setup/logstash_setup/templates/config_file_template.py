CONFIG_FILE_TEMPLATE = """http.host: "0.0.0.0"
xpack.monitoring.elasticsearch.hosts: [ "http://elasticsearch:9200" ]
xpack.monitoring.enabled: true
xpack.monitoring.elasticsearch.username: {{es_user}}
xpack.monitoring.elasticsearch.password: {{es_pass}}
"""
