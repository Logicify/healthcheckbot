FROM python:3.6-alpine

MAINTAINER Dmitry Berezovsky <d@logicify.com>

ARG app_version
ARG release_date
ARG is_beta=False

ENV CONFIG_FILE "/srv/config/config.yaml"

VOLUME /srv/config
VOLUME /srv/data

CMD healthcheckbot -c "${CONFIG_FILE}" run

ADD contrib-dependencies.txt /srv/contrib-dependencies.txt

RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev

RUN : "${app_version:?Version argument should be set. Use --build-arg=VERSION=0.0.0}" \
    && pip install healthcheckbot==${app_version} && pip install -r /srv/contrib-dependencies.txt

LABEL x.healthcheckbot.version="${app_version}" \
      x.healthcheckbot.release-date="${release_date}" \
      x.healthcheckbot.is-beta="${is_beta}"