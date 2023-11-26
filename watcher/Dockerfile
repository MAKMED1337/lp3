FROM python:3.11

WORKDIR /watcher

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD python3.11 -u -m watcher.main
