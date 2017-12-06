FROM python:3.6-alpine

RUN apk --no-cache add musl-dev linux-headers g++ tini postgresql-dev && \
    pip install numpy pipenv # installing beforehand so it can get cached by docker

WORKDIR /worker

COPY Pipfile* /worker/
RUN pipenv install --system

COPY worker /worker
COPY lib /pythonpkg/lib
COPY feeds /pythonpkg/feeds

ENV PYTHONPATH=${PYTHONPATH}:/pythonpkg

ENTRYPOINT ["/bin/sh", "-c"]
CMD ["mrq-worker"]
