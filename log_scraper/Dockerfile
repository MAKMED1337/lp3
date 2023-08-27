FROM python:3.11

WORKDIR /log_scraper

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD python3.11 -u -m log_scraper.main
