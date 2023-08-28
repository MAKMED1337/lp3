FROM python:3.11

WORKDIR /lp3

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .
