FROM python:3.11-slim@sha256:6f31d6e9ba2b0a787a3f81c37b004155b87b9efa1b771182bd550c1615745be5

WORKDIR /app

COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock

RUN useradd --create-home --uid 10001 app
COPY --chown=app:app . .

EXPOSE 8000

USER app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
