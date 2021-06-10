FROM python:latest
RUN apt-get update
RUN mkdir /var/run/supervisord
RUN mkdir /var/log/supervisord
RUN apt-get install -y supervisor
ENV PYTHONUNBUFFERED 1
RUN mkdir -p /app
WORKDIR /app
COPY ./back/ .
COPY ./back/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN pip install -r requirements.txt

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
