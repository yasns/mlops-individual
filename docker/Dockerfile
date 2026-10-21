FROM python:3.12-slim-trixie
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

RUN useradd --create-home --uid 1000 mluser
WORKDIR /app
RUN chown mluser:mluser /app

COPY docker/requirements-train.txt .
RUN pip install --no-cache-dir --no-compile -r requirements-train.txt

COPY --chown=mluser:mluser params.yaml ./
COPY --chown=mluser:mluser src/ src/

USER mluser
CMD ["python", "src/train.py"]
