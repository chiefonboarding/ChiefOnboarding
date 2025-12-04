# syntax=docker/dockerfile:1
# debian 13 is called trixie
FROM debian:13-slim AS supervisord
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
      gettext \
      supervisor \
    && rm -rf /var/lib/apt/lists/*

# python images are based off of Debian
FROM python:3.13-slim-trixie AS app
ENV PYTHONUNBUFFERED=1
USER root
RUN mkdir -p /app
COPY ./back/ /app
WORKDIR /app
RUN python -m pip install pipenv 
RUN pipenv install --system
RUN django-admin compilemessages 

# checkov:skip=CKV_DOCKER_7: zero-CVE fresh image every build
FROM nvcr.io/nvidia/distroless/python:3.13-v3.1.1
USER 65532
HEALTHCHECK NONE
RUN mkdir /var/run/supervisord && mkdir /var/log/supervisord
COPY --from=supervisord /usr/bin/supervisord /usr/bin/supervisord
COPY ./back/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY --from=app /app /app

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
