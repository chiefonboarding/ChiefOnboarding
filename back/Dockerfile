# syntax=docker/dockerfile:1
FROM python:3.13@sha256:960d76d578ab63e55620ebea4918b9b9fc8a4ef4c817cf2dd44aa65aa121bbe0 AS base
USER root
RUN mkdir /var/run/supervisord && mkdir /var/log/supervisord
RUN apt-get update && apt-get install -y --no-install-recommends \
      gettext \
      supervisor \
    && rm -rf /var/lib/apt/lists/*
RUN python -m pip install pipenv 

FROM base AS build
ENV PYTHONUNBUFFERED=1
USER root
RUN mkdir -p /app
COPY ./back/ /app
COPY ./back/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
WORKDIR /app
RUN pipenv install --system
RUN django-admin compilemessages 

# checkov:skip=CKV_DOCKER_7: zero-CVE fresh image every build
FROM cgr.dev/chainguard/python:latest@sha256:136aad7020e00a98f617f3d3343cc7601b7823405eb2bc581eae5f5a8c21e8d0
USER 65532
HEALTHCHECK NONE
COPY --from=build /app /app

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]