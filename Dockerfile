#######################################################
# Builder Image
#######################################################
FROM python:3.11 as builder_image

# Activating virtualenv
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy code
COPY poetry.lock pyproject.toml README.md /app/
COPY .env.example /app/.env
COPY expose/ /app/expose/
WORKDIR /app

# Install poetry and requirements
RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev


#######################################################
# Run Image
#######################################################
FROM python:3.11-slim as run_image
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app
COPY --from=builder_image /opt/venv /opt/venv
COPY --from=builder_image /app /app
CMD ["uvicorn", "expose.main:app", "--host=0.0.0.0", "--reload"]