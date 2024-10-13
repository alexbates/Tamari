FROM python:3.10-slim

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY app app
COPY rpdocker rpdocker
COPY tamari.py config.py boot.sh ./
RUN chmod a+x boot.sh

ENV FLASK_APP tamari.py

EXPOSE 4888
ENTRYPOINT ["./boot.sh"]
