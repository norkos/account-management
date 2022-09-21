FROM python:3.10
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

WORKDIR /app/src

CMD uvicorn main:app --host 0.0.0.0 --port $PORT
