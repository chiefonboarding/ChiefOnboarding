FROM node:14-slim

RUN ls
RUN mkdir -p nuxt

# copy the app, note .dockerignore

RUN cd nuxt
COPY . .
RUN npm install
