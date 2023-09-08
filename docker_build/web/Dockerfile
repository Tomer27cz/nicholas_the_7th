FROM python:3.11
LABEL authors="Tomer27cz"

WORKDIR /web

ADD . /web

RUN pip install -r requirements.txt

EXPOSE 5420
EXPOSE 5421
EXPOSE 5422

CMD uwsgi app.ini