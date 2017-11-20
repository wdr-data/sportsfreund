FROM python:3.6-alpine

RUN apk --no-cache add musl-dev linux-headers g++ tini

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY sportsfreund /app
WORKDIR /app

EXPOSE 8080

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["gunicorn", "-w 1", "-b :8080", "sportsfreund.wsgi"]
