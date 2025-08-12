# https://www.docker.elastic.co/
FROM docker.elastic.co/logstash/logstash:8.11.0

# Download MySQL JDBC driver to connect Logstash to MySQL
RUN curl -Lo "mysql-connector-j-8.2.0.tar.gz" "https://dev.mysql.com/get/Downloads/Connector-J/mysql-connector-j-8.2.0.tar.gz" \
    && tar -xf "mysql-connector-j-8.2.0.tar.gz" "mysql-connector-j-8.2.0/mysql-connector-j-8.2.0.jar" \
    && mv "mysql-connector-j-8.2.0/mysql-connector-j-8.2.0.jar" "mysql-connector-j.jar" \
    && rm -r "mysql-connector-j-8.2.0" "mysql-connector-j-8.2.0.tar.gz"

ENTRYPOINT ["/usr/local/bin/docker-entrypoint"]

# Add your logstash plugins setup here
# Example: RUN logstash-plugin install logstash-filter-json
