FROM python:3.10-slim

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install --with-deps chromium

EXPOSE 5050
CMD ["hypercorn", "backend.api.app:app", "--bind", "0.0.0.0:5050", "--workers", "1", "--worker-class", "asyncio"]

