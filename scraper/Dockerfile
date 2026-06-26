# IceSoak scraper image.
# Provides Python + Playwright/Chromium runtime.
# Code is NOT baked in — the repo arrives via the /work volume mount at run time.
# scrape.py lives in scraper/ and writes studios.json/questions.json to the repo root:
#   podman run --rm --shm-size=1g -v /opt/icesoak:/work -w /work <image> python scraper/scrape.py

FROM python:3.11-slim

# Chromium system dependencies (Debian bookworm slim)
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libcairo2 \
        libcups2 \
        libdbus-1-3 \
        libexpat1 \
        libfontconfig1 \
        libgbm1 \
        libglib2.0-0 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libx11-6 \
        libx11-xcb1 \
        libxcb1 \
        libxcomposite1 \
        libxcursor1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxi6 \
        libxrandr2 \
        libxrender1 \
        libxss1 \
        libxtst6 \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install Playwright's Chromium bundle (avoids system Chromium version drift)
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN playwright install chromium

# /work is the runtime mount point; nothing else lives here by default
WORKDIR /work

# Default command matches the n8n / run_scrape.sh invocation
CMD ["python", "scraper/scrape.py"]
