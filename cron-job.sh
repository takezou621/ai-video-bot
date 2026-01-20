#!/bin/bash
# Daily AI Video Generation Script
# Runs every morning at 7:00 AM JST

set -e

# Script directory
SCRIPT_DIR="/home/kawai/dev/ai-video-bot"
cd "$SCRIPT_DIR" || exit 1

# Log file
LOG_FILE="logs/daily_video_$(date +%Y%m%d_%H%M%S).log"
mkdir -p logs

# Run video generation
echo "=== Starting Daily Video Generation at $(date) ===" | tee -a "$LOG_FILE"

docker compose run --rm -e GOOGLE_APPLICATION_CREDENTIALS=/app/youtube_service_account.json ai-video-bot python advanced_video_pipeline.py 2>&1 | tee -a "$LOG_FILE"

# Check exit status
if [ $? -eq 0 ]; then
    echo "=== Video generation completed successfully at $(date) ===" | tee -a "$LOG_FILE"
else
    echo "=== Video generation failed at $(date) ===" | tee -a "$LOG_FILE"
    exit 1
fi
