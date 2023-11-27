TEMPLATE_SYNC_TABLE = """
input {
{% for entity in entities %}
  jdbc {
    jdbc_driver_library => "/usr/share/logstash/mysql-connector-j.jar"
    jdbc_driver_class => "com.mysql.jdbc.Driver"
    jdbc_connection_string => "jdbc:mysql://sqlserver:3306/aiod"
    jdbc_user => "{{db_user}}"
    jdbc_password => "{{db_pass}}"
    use_column_value => true
    tracking_column => "date_modified"
    tracking_column_type => "timestamp"
    schedule => "*/5 * * * * *"
    statement_filepath => "/usr/share/logstash/sql/sync_{{entity}}.sql"
    type => "{{entity}}"
  }
  jdbc {
    jdbc_driver_library => "/usr/share/logstash/mysql-connector-j.jar"
    jdbc_driver_class => "com.mysql.jdbc.Driver"
    jdbc_connection_string => "jdbc:mysql://sqlserver:3306/aiod"
    jdbc_user => "{{db_user}}"
    jdbc_password => "{{db_pass}}"
    use_column_value => true
    tracking_column => "date_deleted"
    tracking_column_type => "timestamp"
    schedule => "*/5 * * * * *"
    statement_filepath => "/usr/share/logstash/sql/rm_{{entity}}.sql"
    type => "rm_{{entity}}"
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
  if [type] == "rm_{{entity}}" {
    elasticsearch {
        action => "delete"
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
