FROM python:3.8

WORKDIR /home

ENV TELEGRAM_API_TOKEN=""

RUN pip install -U pip aiogram aiofiles && apt-get update && apt-get install -y sqlite3
COPY *.py ./
COPY createdb.sql ./

ENTRYPOINT ["python", "server.py"]
