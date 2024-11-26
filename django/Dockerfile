FROM python:3.9-slim-bullseye

RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev

WORKDIR /app

ADD https://github.com/Noethys/Noethysweb/archive/refs/tags/1.2.7.3.tar.gz noethysweb.tar.gz

RUN tar xzvf noethysweb.tar.gz
RUN ln -s Noethysweb-1.2.7.3 noethysweb
# do not install mysqlclient
RUN pip install --no-cache-dir $(grep -v "^mysqlclient" noethysweb/requirements.txt) gunicorn
# fix for Django 4
RUN sed -i s/ugettext_lazy/gettext_lazy/ /usr/local/lib/python3.9/site-packages/upload_form/forms.py

WORKDIR /app/noethysweb/noethysweb


