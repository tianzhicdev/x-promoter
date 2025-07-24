FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Copy cron file
COPY crontab /etc/cron.d/x-promoter-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/x-promoter-cron

# Apply cron job
RUN crontab /etc/cron.d/x-promoter-cron

# Create the log file to be able to run tail
RUN touch /app/logs/cron.log

# Start cron and tail the log file
CMD cron && tail -f /app/logs/cron.log