#!/bin/bash
# Daily AI Video Generation Script
# Runs at 6:00 AM every day

# Set up environment
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
cd /Users/kawai/dev/ai-video-bot

# Create log directory if it doesn't exist
mkdir -p logs

# Log file with date
LOG_FILE="logs/daily-video-$(date +%Y-%m-%d).log"

# Start logging
echo "================================================" >> "$LOG_FILE"
echo "Daily Video Generation - $(date)" >> "$LOG_FILE"
echo "================================================" >> "$LOG_FILE"

# Run the video generation pipeline
/usr/local/bin/docker compose run --rm ai-video-bot python advanced_video_pipeline.py >> "$LOG_FILE" 2>&1

# Log completion
echo "------------------------------------------------" >> "$LOG_FILE"
echo "Completed at $(date)" >> "$LOG_FILE"
echo "Exit code: $?" >> "$LOG_FILE"
echo "================================================" >> "$LOG_FILE"

# Keep only last 30 days of logs
find logs -name "daily-video-*.log" -mtime +30 -delete
