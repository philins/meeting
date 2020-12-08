FROM python:3.8

WORKDIR /home

ENV TELEGRAM_API_TOKEN="1430994393:AAGrMtIDTrF7kwm13niaVIjtBgB0beFTpBI"

RUN pip install -U pip aiogram && apt-get update && apt-get install -y sqlite3
COPY *.py ./
COPY createdb.sql ./

ENTRYPOINT ["python", "server.py"]