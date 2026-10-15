TEMPLATE_SYNC_TABLE = """
input {
{% for entity in entities %}
  jdbc {
    jdbc_driver_library => "/usr/share/logstash/mysql-connector-j.jar"
    jdbc_driver_class => "com.mysql.jdbc.Driver"
    jdbc_connection_string => "jdbc:mysql://aiod-metadata-catalogue-mysql-svc:3306/aiod"
    jdbc_user => "{{db_user}}"
    jdbc_password => "{{db_pass}}"
    use_column_value => true
    tracking_column => "date_modified"
    tracking_column_type => "timestamp"
    schedule => "*/5 * * * * *"
    statement_filepath => "/usr/share/logstash/sql/sync_{{entity}}.sql"
    type => "{{entity}}"
    # Add these for better handling
    jdbc_paging_enabled => true
    jdbc_page_size => 1000
    last_run_metadata_path => "/usr/share/logstash/sync_{{entity}}_last_run"
    jdbc_default_timezone => "UTC"
  }
  jdbc {
    jdbc_driver_library => "/usr/share/logstash/mysql-connector-j.jar"
    jdbc_driver_class => "com.mysql.jdbc.Driver"
    jdbc_connection_string => "jdbc:mysql://aiod-metadata-catalogue-mysql-svc:3306/aiod"
    jdbc_user => "{{db_user}}"
    jdbc_password => "{{db_pass}}"
    use_column_value => true
    tracking_column => "date_deleted"
    tracking_column_type => "timestamp"
    schedule => "*/5 * * * * *"
    statement_filepath => "/usr/share/logstash/sql/rm_{{entity}}.sql"
    type => "rm_{{entity}}"
    # Add these for better handling
    jdbc_paging_enabled => true
    jdbc_page_size => 1000
    last_run_metadata_path => "/usr/share/logstash/rm_{{entity}}_last_run"
    jdbc_default_timezone => "UTC"
  }
{% endfor %}
}
filter {
  # Handle NULL tracking columns
  if [date_modified] == "" or ![date_modified] {
    mutate {
      add_field => { "date_modified" => "1970-01-01T00:00:00.000Z" }
    }
  }
  if [date_deleted] == "" or ![date_deleted] {
    mutate {
      add_field => { "date_deleted" => "1970-01-01T00:00:00.000Z" }
    }
  }
  
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