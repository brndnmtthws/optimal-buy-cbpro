FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY optimal-buy-gdax.py .
COPY optimal-buy-gdax.py .

ENTRYPOINT [ "python", "./optimal-buy-gdax.py" ]
