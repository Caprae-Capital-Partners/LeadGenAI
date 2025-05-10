FROM python:3.10-slim

# System dependencies for Playwright
RUN apt-get update && apt-get install -y \
    curl wget unzip \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxkbcommon0 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libx11-xcb1 \
    libxcursor1 \
    libgtk-3-0 \
    libpangocairo-1.0-0 \
    libcairo-gobject2 \
    libgdk-pixbuf-2.0-0 \
    libdrm2 \
    libwayland-client0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ✅ Explicitly copy only the needed files
COPY phase_1/requirements.txt /app/requirements.txt
COPY phase_1/api.py /app/api.py
COPY phase_1/backend /app/backend  
RUN pip install -r requirements.txt
RUN pip install playwright && playwright install chromium

EXPOSE 5050
CMD ["hypercorn", "api:app", "--bind", "0.0.0.0:5050", "--workers", "1", "--worker-class", "asyncio"]
