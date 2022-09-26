FROM python:3.10.5-alpine
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

CMD python consumer.py
