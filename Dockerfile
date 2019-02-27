FROM python:3.6-alpine

MAINTAINER Dmitry Berezovsky <d@logicify.com>

ARG VERSION
ENV CONFIG_FILE "/srv/config/config.yaml"

VOLUME /srv/config
VOLUME /srv/data

CMD healthcheckbot -c "${CONFIG_FILE}" run

RUN : "${VERSION:?Version argument should be set. Use --build-arg=VERSION=0.0.0}" \
    && pip install healthcheckbot==${VERSION}
