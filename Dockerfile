FROM python:3.12
LABEL authors="Tomer27cz"

ADD ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r /app/requirements.txt

RUN apt update && apt-get install -y --no-install-recommends ffmpeg

EXPOSE 5421
EXPOSE 5422

# Command is changed at runtime by docker-compose.yml
# nohup python3 -u main.py &>> log/activity.log &
CMD python -u main.py >> /bot/logs/bot.log 2>&1
