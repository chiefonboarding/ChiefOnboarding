FROM python:3.9
RUN apt-get update
RUN mkdir /var/run/supervisord
RUN mkdir /var/log/supervisord
RUN apt-get install -y supervisor gettext
RUN python -m pip install pipenv 

ENV PYTHONUNBUFFERED 1
RUN mkdir -p /app
WORKDIR /app
COPY ./back/ .
COPY ./back/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN pipenv install --system
RUN django-admin compilemessages 

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
