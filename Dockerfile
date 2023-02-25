# Dockerfile for A_plus_tsukuba service container

# Download python image
# Python version is same as the production.
FROM python:3.8.10-buster

# Cast a spell
ENV PYTHONUNBUFFERED 1

# MySQL Connector
RUN apt-get update
RUN apt-get -y install default-mysql-client

RUN mkdir /a_plus_tsukuba

# Install poerty
ENV POETRY_HOME=/opt/poetry
RUN curl -sSL https://install.python-poetry.org | python - && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false
    # venv is not used in the container

# Copy poetry files
COPY ./pyproject.toml* ./poetry.lock* ./

# Install Dependencies
RUN poetry install --no-root
# Cast a spell "--no-root" cf. https://github.com/python-poetry/poetry/issues/689 

COPY ./init /a_plus_tsukuba/init
COPY ./manage.py /a_plus_tsukuba/
COPY ./pytest.ini /a_plus_tsukuba/

COPY ./A_plus_Tsukuba /a_plus_tsukuba/A_plus_Tsukuba
COPY ./board /a_plus_tsukuba/board

# Copy .env for local
COPY ./.env_local /a_plus_tsukuba/.env
