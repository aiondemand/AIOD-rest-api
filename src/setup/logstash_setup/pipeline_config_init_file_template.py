PIPELINE_CONFIG_INIT_FILE_TEMPLATE = """
input {
{% for entity in entities %}
  jdbc {
    jdbc_driver_library => "/usr/share/logstash/mysql-connector-j.jar"
    jdbc_driver_class => "com.mysql.jdbc.Driver"
    jdbc_connection_string => "jdbc:mysql://sqlserver:3306/aiod"
    jdbc_user => "{{db_user}}"
    jdbc_password => "{{db_pass}}"
    clean_run => true
    record_last_run => false
    statement_filepath => "/usr/share/logstash/sql/init_{{entity}}.sql"
    type => "{{entity}}"
  }
{% endfor %}
}
filter {
  mutate {
    remove_field => ["@version", "@timestamp"]
  }
}
output {
{% for entity in entities %}
  if [type] == "{{entity}}" {
    elasticsearch {
        hosts => "elasticsearch:9200"
        user => "{{es_user}}"
        password => "{{es_pass}}"
        ecs_compatibility => disabled
        index => "{{entity}}"
        document_id => "{{entity}}_%{identifier}"
    }
  }
{% endfor %}
}
"""
