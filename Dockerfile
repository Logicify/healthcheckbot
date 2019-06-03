FROM python:3.6-alpine

MAINTAINER Dmitry Berezovsky <d@logicify.com>

ARG VERSION
ENV CONFIG_FILE "/srv/config/config.yaml"

VOLUME /srv/config
VOLUME /srv/data

CMD healthcheckbot -c "${CONFIG_FILE}" run

ADD contrib-dependencies.txt /srv/contrib-dependencies.txt

RUN : "${VERSION:?Version argument should be set. Use --build-arg=VERSION=0.0.0}" \
    && pip install healthcheckbot==${VERSION} && pip install -r /srv/contrib-dependencies.txt
