#!/bin/bash

echo "========================================"
echo "   Job Tracker - Quick Start"
echo "========================================"
echo ""
echo "Starting Backend and Frontend servers..."
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect OS
OS="$(uname -s)"

start_backend() {
    cd "$SCRIPT_DIR/logic"
    source venv/bin/activate
    python -m uvicorn app.main:app
}

start_frontend() {
    cd "$SCRIPT_DIR/view"
    echo "Starting Frontend Development Server..."
    npm run dev
}

if [[ "$OS" == "Darwin" ]]; then
    # macOS
    osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR/logic' && source venv/bin/activate && python -m uvicorn app.main:app\""

    sleep 3

    osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR/view' && echo 'Starting Frontend Development Server...' && npm run dev\""

elif [[ "$OS" == "Linux" ]]; then
    # Linux - try different terminal emulators
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal --title="Job Tracker Backend" -- bash -c "cd '$SCRIPT_DIR/logic' && source venv/bin/activate && python -m uvicorn app.main:app; exec bash"
        sleep 3
        gnome-terminal --title="Job Tracker Frontend" -- bash -c "cd '$SCRIPT_DIR/view' && echo 'Starting Frontend Development Server...' && npm run dev; exec bash"
    elif command -v konsole &> /dev/null; then
        konsole --new-tab -e bash -c "cd '$SCRIPT_DIR/logic' && source venv/bin/activate && python -m uvicorn app.main:app; exec bash" &
        sleep 3
        konsole --new-tab -e bash -c "cd '$SCRIPT_DIR/view' && echo 'Starting Frontend Development Server...' && npm run dev; exec bash" &
    elif command -v xfce4-terminal &> /dev/null; then
        xfce4-terminal --title="Job Tracker Backend" -e "bash -c 'cd \"$SCRIPT_DIR/logic\" && source venv/bin/activate && python -m uvicorn app.main:app; exec bash'" &
        sleep 3
        xfce4-terminal --title="Job Tracker Frontend" -e "bash -c 'cd \"$SCRIPT_DIR/view\" && echo \"Starting Frontend Development Server...\" && npm run dev; exec bash'" &
    elif command -v xterm &> /dev/null; then
        xterm -title "Job Tracker Backend" -e "bash -c 'cd \"$SCRIPT_DIR/logic\" && source venv/bin/activate && python -m uvicorn app.main:app; exec bash'" &
        sleep 3
        xterm -title "Job Tracker Frontend" -e "bash -c 'cd \"$SCRIPT_DIR/view\" && echo \"Starting Frontend Development Server...\" && npm run dev; exec bash'" &
    else
        echo "No supported terminal emulator found."
        echo "Please install gnome-terminal, konsole, xfce4-terminal, or xterm."
        exit 1
    fi
else
    echo "Unsupported operating system: $OS"
    exit 1
fi

echo ""
echo "========================================"
echo "Both servers are starting!"
echo "========================================"
echo ""
echo "Backend will be available at: http://localhost:8000"
echo "Frontend will be available at: http://localhost:5173"
echo ""
echo "Two new terminal windows have been opened."
