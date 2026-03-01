FROM python:3.11-slim

# System deps: curl (healthcheck) + chromium runtime libs
# Note: ttf-unifont/ttf-ubuntu-font-family renamed in Debian Trixie → fonts-unifont/fonts-ubuntu
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        procps \
        fonts-unifont \
        fonts-liberation \
        libasound2t64 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libcairo2 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libglib2.0-0 \
        libnspr4 \
        libnss3 \
        libpango-1.0-0 \
        libx11-6 \
        libxcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxkbcommon0 \
        libxrandr2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && playwright install chromium

COPY . .

HEALTHCHECK --interval=60s --timeout=10s --start-period=60s --retries=3 \
  CMD pgrep -f "python main.py" || exit 1

CMD ["python", "main.py"]
