FROM python:3.6

RUN apt-get update && apt-get install -yq \
    g++ gcc postgresql-server-dev-all libxslt-dev libxml2-dev locales \
    && pip install numpy lxml pipenv # installing beforehand so it can get cached by docker

RUN echo 'en_US.UTF-8 UTF-8\nde_DE.UTF-8 UTF-8' >> /etc/locale.gen && \
    locale-gen && \
    update-locale LANG=de_DE.UTF-8

ENV LANG=de_DE.UTF-8
ENV LC_ALL=de_DE.UTF-8

WORKDIR /worker

COPY Pipfile* /worker/
RUN pipenv install --system

COPY worker /worker
COPY lib /pythonpkg/lib
COPY feeds /pythonpkg/feeds
COPY app/backend /pythonpkg/backend
COPY app/bot /pythonpkg/bot
COPY app/main /pythonpkg/main

ENV PYTHONPATH=${PYTHONPATH}:/pythonpkg

ENTRYPOINT ["/bin/sh", "-c"]
CMD ["mrq-worker"]
