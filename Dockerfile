FROM python:3.12

WORKDIR /application

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .
