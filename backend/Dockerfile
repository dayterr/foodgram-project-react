FROM python:3.8.5-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000