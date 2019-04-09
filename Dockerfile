FROM python:3

WORKDIR /appsrc

COPY . .
RUN pip install . \
  && rm -rf /appsrc

ENTRYPOINT ["optimal-buy-cbpro"]
