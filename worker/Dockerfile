FROM python:3.6-alpine

RUN apk --no-cache add musl-dev linux-headers g++ gcc tini postgresql-dev libxslt-dev libxml2-dev \
    && pip install numpy lxml pipenv # installing beforehand so it can get cached by docker

WORKDIR /worker

COPY Pipfile* /worker/
RUN pipenv install --system

COPY worker /worker
COPY lib /pythonpkg/lib
COPY feeds /pythonpkg/feeds

ENV PYTHONPATH=${PYTHONPATH}:/pythonpkg

ENTRYPOINT ["/bin/sh", "-c"]
CMD ["mrq-worker"]
