# https://www.docker.elastic.co/
FROM docker.elastic.co/logstash/logstash:7.13.0

# Download MySQL JDBC driver to connect Logstash to MySQL
RUN curl -Lo "mysql-connector-java-8.0.22.tar.gz" "https://dev.mysql.com/get/Downloads/Connector-J/mysql-connector-java-8.0.22.tar.gz" \
    && tar -xf "mysql-connector-java-8.0.22.tar.gz" "mysql-connector-java-8.0.22/mysql-connector-java-8.0.22.jar" \
    && mv "mysql-connector-java-8.0.22/mysql-connector-java-8.0.22.jar" "mysql-connector-java-8.0.22.jar" \
    && rm -r "mysql-connector-java-8.0.22" "mysql-connector-java-8.0.22.tar.gz"

ENTRYPOINT ["/usr/local/bin/docker-entrypoint"]

# Add your logstash plugins setup here
# Example: RUN logstash-plugin install logstash-filter-json
