FROM python:3.9-slim-bullseye

RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev

WORKDIR /app

ADD https://github.com/Noethys/Noethysweb/archive/refs/tags/1.2.7.3.tar.gz noethysweb.tar.gz

RUN tar xzvf noethysweb.tar.gz
RUN ln -s Noethysweb-1.2.7.3 noethysweb
# do not install mysqlclient
RUN pip install --no-cache-dir $(grep -v "^mysqlclient" noethysweb/requirements.txt) gunicorn

WORKDIR /app/noethysweb/noethysweb


