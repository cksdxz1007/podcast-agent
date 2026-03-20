#!/bin/bash
# tmux wrapper for podcast transcription
# Usage: ./run_in_tmux.sh "url" "name"
# Creates a tmux session, runs transcription, then cleans up

set -e

SESSION_NAME="podcast_trans_$$"
URL="$1"
NAME="${2:-podcast}"

if [ -z "$URL" ]; then
    echo "Usage: run_in_tmux.sh <url> [name]"
    exit 1
fi

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
LOG_FILE="$SCRIPT_DIR/logs/tmux_${SESSION_NAME}.log"

# Ensure logs directory exists
mkdir -p "$SCRIPT_DIR/logs"

# Create detached tmux session running the script
tmux new-session -d -s "$SESSION_NAME" \
    "cd '$SCRIPT_DIR' && $PYTHON_BIN -m podcast_agent.main \"$URL\" \"$NAME\" > '$LOG_FILE' 2>&1"

echo "Started transcription in tmux session: $SESSION_NAME"
echo "URL: $URL"
echo "Name: $NAME"
echo "Log: $LOG_FILE"
echo ""
echo "Commands:"
echo "  View progress: tail -f $LOG_FILE"
echo "  Attach:        tmux attach -t $SESSION_NAME"
echo "  Stop:          tmux kill-session -t $SESSION_NAME"
