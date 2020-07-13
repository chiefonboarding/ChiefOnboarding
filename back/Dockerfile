FROM python:latest
ENV PYTHONUNBUFFERED 1
RUN mkdir -p /app
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN python manage.py collectstatic
# RUN python manage.py migrate


