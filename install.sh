#!/bin/bash
set -e

# Quip - Frictionless thought capture tool installer
# Usage: curl -sSL https://raw.githubusercontent.com/voglster/quip/main/install.sh | bash
# Options:
#   --autostart    Enable daemon autostart (systemd service)
#   --no-autostart Skip autostart setup
#   --pip-dev      Install as editable pip package (development mode)

echo "🚀 Installing Quip - Frictionless thought capture tool"

# Parse command line arguments
ENABLE_AUTOSTART=false
PIP_DEV_MODE=false

for arg in "$@"; do
    case $arg in
        --autostart)
            ENABLE_AUTOSTART=true
            shift
            ;;
        --no-autostart)
            ENABLE_AUTOSTART=false
            shift
            ;;
        --pip-dev)
            PIP_DEV_MODE=true
            shift
            ;;
        *)
            # Unknown option
            ;;
    esac
done

# Check if running on supported platform
if [[ "$OSTYPE" != "linux-gnu"* ]] && [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Unsupported platform: $OSTYPE"
    echo "Quip currently supports Linux and macOS only"
    exit 1
fi

# If no autostart option specified, ask user
if [[ "$ENABLE_AUTOSTART" == "false" ]] && [[ "$1" != "--no-autostart" ]]; then
    echo ""
    read -p "🔥 Enable daemon autostart on boot? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ENABLE_AUTOSTART=true
    fi
fi

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv (Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env 2>/dev/null || true  # Add to PATH if needed
fi

# Set installation directory
INSTALL_DIR="$HOME/.local/share/quip"
BIN_DIR="$HOME/.local/bin"

# Create directories
mkdir -p "$BIN_DIR"
mkdir -p "$HOME/notes/5. Inbox"

# Download and install Quip
echo "⬇️  Downloading Quip..."
if [ -d "$INSTALL_DIR" ]; then
    echo "🔄 Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    git clone https://github.com/voglster/quip.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Install dependencies
echo "📦 Installing dependencies..."
cd "$INSTALL_DIR/desktop"

if [[ "$PIP_DEV_MODE" == "true" ]]; then
    echo "🔧 Installing as editable pip package..."
    uv sync --group dev
    uv pip install -e .
else
    uv sync
fi

# Create launcher script
echo "🔗 Creating launcher..."
cat > "$BIN_DIR/quip" << 'EOF'
#!/bin/bash
cd "$HOME/.local/share/quip/desktop"
exec uv run quip "$@"
EOF

cat > "$BIN_DIR/quip-daemon" << 'EOF'
#!/bin/bash
cd "$HOME/.local/share/quip/desktop"
exec uv run quip-daemon "$@"
EOF

chmod +x "$BIN_DIR/quip" "$BIN_DIR/quip-daemon"

# Set up autostart if requested
if [[ "$ENABLE_AUTOSTART" == "true" ]]; then
    echo "⚡ Setting up autostart..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Create desktop autostart file for Linux
        AUTOSTART_DIR="$HOME/.config/autostart"
        mkdir -p "$AUTOSTART_DIR"
        
        cat > "$AUTOSTART_DIR/quip-daemon.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Quip Daemon
Comment=Global hotkey handler for thought capture
Exec=$BIN_DIR/quip-daemon start
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF
        
        # Start the daemon immediately if not already running
        if ! pgrep -f "quip-daemon" > /dev/null; then
            echo "🚀 Starting daemon..."
            "$BIN_DIR/quip-daemon" start &
            sleep 1
        else
            echo "🔄 Daemon already running"
        fi
        
        echo "✅ Desktop autostart file created and daemon started"
        echo "🔧 Manage via: System Settings → Startup Applications"
        echo "🎯 Test hotkey: Win+Space"
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS LaunchAgent
        LAUNCHAGENTS_DIR="$HOME/Library/LaunchAgents"
        mkdir -p "$LAUNCHAGENTS_DIR"
        
        cat > "$LAUNCHAGENTS_DIR/com.quip.daemon.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.quip.daemon</string>
    <key>Program</key>
    <string>$BIN_DIR/quip-daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>$BIN_DIR/quip-daemon</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF
        
        # Load the launch agent
        launchctl load "$LAUNCHAGENTS_DIR/com.quip.daemon.plist"
        launchctl start com.quip.daemon
        
        echo "✅ LaunchAgent created and started"
        echo "🔧 Manage with: launchctl {start|stop} com.quip.daemon"
        
    else
        # Fallback: create desktop autostart entry
        AUTOSTART_DIR="$HOME/.config/autostart"
        mkdir -p "$AUTOSTART_DIR"
        
        cat > "$AUTOSTART_DIR/quip-daemon.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Quip Daemon
Comment=Global hotkey handler for thought capture
Exec=$BIN_DIR/quip-daemon start
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF
        
        echo "✅ Desktop autostart entry created"
        echo "🔧 Daemon will start automatically on next login"
    fi
fi

# Add to PATH if needed
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "📝 Adding $HOME/.local/bin to PATH..."
    
    # Add to appropriate shell config
    if [ -n "$ZSH_VERSION" ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
        echo "Run: source ~/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        echo "Run: source ~/.bashrc"
    else
        echo "Add this to your shell config: export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
fi

echo ""
echo "✅ Quip installed successfully!"
echo ""
echo "🎯 Quick start:"
echo "   quip                 # Launch GUI"
echo "   quip-daemon start    # Start background daemon with global hotkey"
echo "   quip-daemon stop     # Stop background daemon"
echo ""
echo "📁 Notes saved to: ~/notes/5. Inbox/Inbox.md"
echo "🔥 Global hotkey: Ctrl+Shift+Space (when daemon is running)"
echo ""
echo "Need help? Check: https://github.com/voglster/quip"