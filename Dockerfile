from bitnami/spark:2.4.4
USER root
RUN mkdir -p /var/lib/apt/lists/partial
RUN apt-get update && apt-get install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget
RUN cd /tmp && wget https://www.python.org/ftp/python/3.7.6/Python-3.7.6.tgz && tar -xf Python-3.7.6.tgz
RUN cd /tmp/Python-3.7.6 && ./configure && sudo make install
RUN rm -f /opt/bitnami/python/bin/python3 && ln -s /usr/local/bin/python3 /opt/bitnami/python/bin/python3
