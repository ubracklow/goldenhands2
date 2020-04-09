# pull official base image
FROM python:3.8.1-alpine

# set work directory
WORKDIR /usr/src/goldenhands2

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/goldenhands2/requirements.txt
RUN pip install -r requirements.txt

# copy entrypoint.sh
COPY ./entrypoint.sh /usr/src/goldenhands2/entrypoint.sh
RUN chmod +x /usr/src/goldenhands2/entrypoint.sh

# copy project
COPY . /usr/src/goldenhands2/

# run entrypoint.sh
ENTRYPOINT ["/usr/src/goldenhands2/entrypoint.sh"]
