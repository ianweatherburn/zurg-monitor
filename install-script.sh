#!/bin/bash
# ============================================================================
# Zurg Monitor Installation Script
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default installation directory
INSTALL_DIR="/opt/zurg-monitor"
CONFIG_DIR="/etc/zurg-monitor"

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║        Zurg Broken Torrent Monitor - Installation Script            ║${NC}"
echo -e "${CYAN}║                    Python Edition v3.0.0                             ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════╝${NC}"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}This script should be run as root for system-wide installation.${NC}"
    echo -e "${YELLOW}If you want a user installation, please run manually.${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Python version
echo -e "${CYAN}Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
    else
        echo -e "${RED}✗ Python 3.10+ required (found $PYTHON_VERSION)${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Python 3 not found${NC}"
    echo -e "${YELLOW}Please install Python 3.10 or higher${NC}"
    exit 1
fi

# Ask for installation type
echo
echo -e "${CYAN}Installation Options:${NC}"
echo "1. System-wide installation (${INSTALL_DIR})"
echo "2. User installation (~/.local/bin)"
echo "3. Custom path"
read -p "Select option [1-3]: " INSTALL_OPTION

case $INSTALL_OPTION in
    1)
        INSTALL_DIR="/opt/zurg-monitor"
        CONFIG_DIR="/etc/zurg-monitor"
        SYSTEMD_INSTALL=true
        ;;
    2)
        INSTALL_DIR="$HOME/.local/share/zurg-monitor"
        CONFIG_DIR="$HOME/.config/zurg-monitor"
        SYSTEMD_INSTALL=false
        ;;
    3)
        read -p "Enter installation path: " CUSTOM_PATH
        INSTALL_DIR="$CUSTOM_PATH"
        CONFIG_DIR="$INSTALL_DIR"
        SYSTEMD_INSTALL=false
        ;;
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

# Create directories
echo
echo -e "${CYAN}Creating directories...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
echo -e "${GREEN}✓ Directories created${NC}"

# Check if files exist in current directory
if [ ! -f "zurg-monitor.py" ]; then
    echo -e "${RED}✗ zurg-monitor.py not found in current directory${NC}"
    exit 1
fi

# Copy files
echo -e "${CYAN}Installing files...${NC}"
cp zurg-monitor.py "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/zurg-monitor.py"
echo -e "${GREEN}✓ Copied zurg-monitor.py${NC}"

if [ -f "zurg-monitor.conf" ]; then
    if [ -f "$CONFIG_DIR/zurg-monitor.conf" ]; then
        echo -e "${YELLOW}⚠ Config file already exists, creating backup${NC}"
        cp "$CONFIG_DIR/zurg-monitor.conf" "$CONFIG_DIR/zurg-monitor.conf.bak"
        echo -e "${GREEN}✓ Backup created: zurg-monitor.conf.bak${NC}"
    fi
    cp zurg-monitor.conf "$CONFIG_DIR/"
    echo -e "${GREEN}✓ Copied zurg-monitor.conf${NC}"
else
    echo -e "${YELLOW}⚠ zurg-monitor.conf not found, you'll need to create it${NC}"
fi

# Create symlink for easy access
if [ "$EUID" -eq 0 ] && [ "$INSTALL_OPTION" = "1" ]; then
    echo -e "${CYAN}Creating symlink in /usr/local/bin...${NC}"
    ln -sf "$INSTALL_DIR/zurg-monitor.py" /usr/local/bin/zurg-monitor
    echo -e "${GREEN}✓ Symlink created${NC}"
fi

# Install systemd service
if [ "$SYSTEMD_INSTALL" = true ] && [ "$EUID" -eq 0 ]; then
    echo
    read -p "Install systemd service? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f "zurg-monitor.service" ]; then
            # Update paths in service file
            sed -e "s|WorkingDirectory=.*|WorkingDirectory=$INSTALL_DIR|" \
                -e "s|ExecStart=.*|ExecStart=/usr/bin/python3 $INSTALL_DIR/zurg-monitor.py --config $CONFIG_DIR/zurg-monitor.conf|" \
                zurg-monitor.service > /tmp/zurg-monitor.service
            
            cp /tmp/zurg-monitor.service /etc/systemd/system/
            rm /tmp/zurg-monitor.service
            
            systemctl daemon-reload
            echo -e "${GREEN}✓ Systemd service installed${NC}"
            echo
            echo -e "${CYAN}To enable and start the service:${NC}"
            echo "  sudo systemctl enable zurg-monitor"
            echo "  sudo systemctl start zurg-monitor"
            echo "  sudo systemctl status zurg-monitor"
        else
            echo -e "${YELLOW}⚠ zurg-monitor.service not found${NC}"
        fi
    fi
fi

# Configuration
echo
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo
echo -e "${CYAN}Installation Details:${NC}"
echo "  Script:  $INSTALL_DIR/zurg-monitor.py"
echo "  Config:  $CONFIG_DIR/zurg-monitor.conf"
if [ "$SYSTEMD_INSTALL" = true ]; then
    echo "  Service: /etc/systemd/system/zurg-monitor.service"
fi
echo

echo -e "${CYAN}Next Steps:${NC}"
echo "1. Edit the configuration file:"
echo "   nano $CONFIG_DIR/zurg-monitor.conf"
echo
echo "2. Test the installation:"
if [ "$EUID" -eq 0 ] && [ "$INSTALL_OPTION" = "1" ]; then
    echo "   zurg-monitor --run-once --debug"
else
    echo "   python3 $INSTALL_DIR/zurg-monitor.py --run-once --debug"
fi
echo
echo "3. Run continuously:"
if [ "$EUID" -eq 0 ] && [ "$INSTALL_OPTION" = "1" ]; then
    echo "   zurg-monitor"
else
    echo "   python3 $INSTALL_DIR/zurg-monitor.py"
fi

if [ "$SYSTEMD_INSTALL" = true ]; then
    echo
    echo "4. Or install as a service:"
    echo "   sudo systemctl enable zurg-monitor"
    echo "   sudo systemctl start zurg-monitor"
    echo "   sudo systemctl status zurg-monitor"
fi

echo
echo -e "${CYAN}For help and documentation:${NC}"
if [ "$EUID" -eq 0 ] && [ "$INSTALL_OPTION" = "1" ]; then
    echo "   zurg-monitor --help"
else
    echo "   python3 $INSTALL_DIR/zurg-monitor.py --help"
fi
echo

echo -e "${GREEN}Happy monitoring!${NC}"
echo