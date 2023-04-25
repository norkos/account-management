FROM python:3.11
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir pipenv
RUN pipenv install

WORKDIR /app/src
CMD pipenv run python main.py
