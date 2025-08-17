# Dockerfile for A_plus_tsukuba service container

# Download python image
# Python version is same as the production.
FROM python:3.8.20-bullseye

# Cast a spell
ENV PYTHONUNBUFFERED 1

# MySQL Connector
RUN apt-get update
RUN apt-get -y install default-mysql-client

RUN mkdir /a_plus_tsukuba

# Install poerty
RUN pip install poetry==1.8.2
RUN poetry config virtualenvs.create false

# Set working dir
WORKDIR /a_plus_tsukuba

# Copy poetry files
COPY ./pyproject.toml* ./poetry.lock* ./

# Install Dependencies
RUN poetry install --no-root
# Cast a spell "--no-root" cf. https://github.com/python-poetry/poetry/issues/689 

# Copy .env for local
COPY ./.env_local ./.env

# Copy files
COPY ./manage.py ./
COPY ./pytest.ini ./

# NOTICE
# ./A_plus_Tsukuba and ./board are synchronized by volume configs in docker-compose.yml
