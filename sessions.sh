#!/bin/bash
# Monitor and manage podcast transcription tmux sessions

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"

list_sessions() {
    echo "=== Active Podcast Transcription Sessions ==="
    tmux list-sessions 2>/dev/null | grep "podcast_trans_" || echo "No active sessions"
    echo ""
    echo "=== Recent Logs ==="
    ls -lt "$LOG_DIR"/tmux_podcast_trans_*.log 2>/dev/null | head -5 || echo "No logs found"
}

tail_log() {
    PID="$1"
    if [ -z "$PID" ]; then
        echo "Usage: $0 log <pid>"
        return 1
    fi
    LOG_FILE="$LOG_DIR/tmux_podcast_trans_$PID.log"
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "Log file not found: $LOG_FILE"
        echo "Available logs:"
        ls -1 "$LOG_DIR"/tmux_podcast_trans_*.log 2>/dev/null || echo "  (none)"
    fi
}

stop_session() {
    PID="$1"
    if [ -z "$PID" ]; then
        echo "Usage: $0 stop <pid>"
        return 1
    fi
    tmux kill-session -t "podcast_trans_$PID" 2>/dev/null && \
        echo "Session podcast_trans_$PID stopped" || \
        echo "Session podcast_trans_$PID not found or already stopped"
}

case "$1" in
    list)
        list_sessions
        ;;
    log)
        tail_log "$2"
        ;;
    stop)
        stop_session "$2"
        ;;
    help|--help|-h)
        echo "Podcast Transcription Session Manager"
        echo ""
        echo "Usage: $0 <command> [pid]"
        echo ""
        echo "Commands:"
        echo "  list          List active sessions and recent logs"
        echo "  log <pid>     Tail log file (pid from list command)"
        echo "  stop <pid>    Stop a running session"
        echo ""
        echo "Examples:"
        echo "  $0 list"
        echo "  $0 log 12345"
        echo "  $0 stop 12345"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Run '$0 help' for usage information"
        ;;
esac
