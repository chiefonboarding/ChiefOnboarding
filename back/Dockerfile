FROM python:3.11
RUN apt-get update
RUN mkdir /var/run/supervisord
RUN mkdir /var/log/supervisord
RUN apt-get install -y supervisor gettext
RUN python -m pip install pipenv 

ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY ./back/ .
# COPY ./back/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN cp /app/supervisord.conf /etc/supervisor/conf.d/supervisord.conf \
    && pipenv install --system && pip install --no-cache-dir ldap3 passlib PyYAML ms_active_directory \
    && django-admin compilemessages 

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
