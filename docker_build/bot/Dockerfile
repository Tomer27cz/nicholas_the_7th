FROM python:3.11
LABEL authors="Tomer27cz"

WORKDIR /bot

ADD . /bot

RUN apt update && apt-get install -y --no-install-recommends ffmpeg

RUN pip install -r requirements.txt

EXPOSE 5420
EXPOSE 5421
EXPOSE 5422

# nohup python3 -u main.py &>> log/activity.log &
CMD python -u main.py >> /bot/db/log/activity.log 2>&1
