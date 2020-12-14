FROM python:latest
ENV PYTHONUNBUFFERED 1
RUN mkdir -p /app
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
# RUN sed -i 's/raise RuntimeError("populate() isn.*/self.app_configs = {}/'  /usr/local/lib/python3.8/site-packages/django/apps/registry.py
# RUN python manage.py migrate


