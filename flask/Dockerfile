FROM python:3.11-bullseye

WORKDIR /api

ENV PIP_ROOT_USER_ACTION=ignore

# Pin Poetry version for reproducibility and security
ENV POETRY_VERSION=1.7.1
ENV POETRY_HOME=/opt/poetry
ENV PATH="$POETRY_HOME/bin:$PATH"

# Upgrade pip and install Poetry securely
# Download installer first instead of piping curl directly to shell
RUN python -m pip install --upgrade pip && \
    curl --proto =https -sSL https://install.python-poetry.org -o /tmp/install-poetry.py && \
    python /tmp/install-poetry.py --version ${POETRY_VERSION} && \
    rm /tmp/install-poetry.py && \
    poetry config virtualenvs.create false && \
    poetry --version

COPY ./flask/pyproject.toml ./flask/poetry.lock ./

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root ; fi"

COPY ./flask /api

COPY ./common /api/common

ENV PYTHONPATH /api

# Create non-root user for security and set permissions
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser && \
    chown -R appuser:appgroup /api && \
    chmod +x /api/docker-entrypoint.sh

# Switch to non-root user
USER appuser

# Run app.py when the container launches
ENV FLASK_APP app.py

ENTRYPOINT ["./docker-entrypoint.sh"]
