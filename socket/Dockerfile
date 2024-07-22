FROM python:3.12
LABEL authors="Tomer27cz"

ADD ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r /app/requirements.txt

EXPOSE 5001

# Command is changed at runtime by docker-compose.yml
# nohup python3 -u main.py &>> log/activity.log &
CMD python -u socket/socketapp.py >> /bot/logs/socket.log 2>&1
