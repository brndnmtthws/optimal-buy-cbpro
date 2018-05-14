FROM python:3

WORKDIR /appsrc

COPY . .
RUN pip install -r requirements.txt \
  && python setup.py install \
  && rm -rf /appsrc

CMD "optimal-buy-gdax.py"
