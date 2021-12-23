FROM python:3.8-slim
#  https://pythonspeed.com/articles/alpine-docker-python/

RUN apt-get update && apt-get install -y \
    netcat\
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt --ignore-installed

WORKDIR /app


