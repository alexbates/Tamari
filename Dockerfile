FROM python:3.10-slim

# Install weasyprint dependencies
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libpangocairo-1.0-0 \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY app app
COPY rpdocker rpdocker
COPY tamari.py config.py version.py boot.sh ./
RUN chmod a+x boot.sh

ENV FLASK_APP tamari.py

EXPOSE 4888
ENTRYPOINT ["./boot.sh"]
