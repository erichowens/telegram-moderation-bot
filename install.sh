#!/bin/bash

# Telegram Moderation Bot - Installation Script for Mac/Linux
# This script sets up the bot on Unix-like systems

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
    PYTHON_CMD="python3"
    INSTALL_CMD="brew"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
    PYTHON_CMD="python3"
    if command -v apt-get &> /dev/null; then
        INSTALL_CMD="apt-get"
    elif command -v yum &> /dev/null; then
        INSTALL_CMD="yum"
    elif command -v dnf &> /dev/null; then
        INSTALL_CMD="dnf"
    else
        INSTALL_CMD="unknown"
    fi
else
    echo -e "${RED}Unsupported OS: $OSTYPE${NC}"
    exit 1
fi

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}    Telegram Moderation Bot Installer for $OS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Function to install Python
install_python() {
    echo -e "${YELLOW}Installing Python...${NC}"
    
    if [[ "$OS" == "macOS" ]]; then
        if ! command_exists brew; then
            echo -e "${YELLOW}Installing Homebrew first...${NC}"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install python@3.12
    else
        if [[ "$INSTALL_CMD" == "apt-get" ]]; then
            sudo apt-get update
            sudo apt-get install -y python3.12 python3-pip python3-venv
        elif [[ "$INSTALL_CMD" == "yum" ]] || [[ "$INSTALL_CMD" == "dnf" ]]; then
            sudo $INSTALL_CMD install -y python3.12 python3-pip
        else
            echo -e "${RED}Please install Python 3.8+ manually${NC}"
            exit 1
        fi
    fi
}

# Function to install Docker
install_docker() {
    echo -e "${YELLOW}Installing Docker...${NC}"
    
    if [[ "$OS" == "macOS" ]]; then
        if ! command_exists brew; then
            echo -e "${YELLOW}Installing Homebrew first...${NC}"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install --cask docker
        echo -e "${YELLOW}Please start Docker Desktop from Applications${NC}"
        echo -e "${YELLOW}Press Enter when Docker is running...${NC}"
        read
    else
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        echo -e "${YELLOW}Please log out and back in for Docker permissions${NC}"
    fi
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
        echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
    else
        echo -e "${YELLOW}Python $PYTHON_VERSION found, but 3.8+ required${NC}"
        read -p "Install Python 3.12? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_python
        fi
    fi
else
    echo -e "${RED}Python not found${NC}"
    read -p "Install Python? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_python
    else
        echo -e "${RED}Python is required. Exiting.${NC}"
        exit 1
    fi
fi

# Check Git
if ! command_exists git; then
    echo -e "${YELLOW}Installing Git...${NC}"
    if [[ "$OS" == "macOS" ]]; then
        brew install git
    else
        sudo $INSTALL_CMD install -y git
    fi
fi
echo -e "${GREEN}✓ Git found${NC}"

# Ask about Docker
echo
read -p "Do you want to use Docker? (recommended) (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command_exists docker; then
        echo -e "${GREEN}✓ Docker found${NC}"
    else
        install_docker
    fi
    USE_DOCKER=true
else
    USE_DOCKER=false
fi

# Create virtual environment
echo
echo -e "${YELLOW}Setting up Python environment...${NC}"

if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install requirements
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create necessary directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p config logs models
echo -e "${GREEN}✓ Directories created${NC}"

# Create example configuration
if [ ! -f "config/config.yaml" ]; then
    echo -e "${YELLOW}Creating example configuration...${NC}"
    cat > config/config.example.yaml << 'EOF'
telegram:
  # Get your token from @BotFather on Telegram
  # token: "YOUR_BOT_TOKEN_HERE"
  
moderation:
  thresholds:
    spam: 0.7
    toxicity: 0.8
    harassment: 0.6
    
policies:
  - type: "spam"
    threshold: 0.8
    action: "delete"
  - type: "harassment"
    threshold: 0.7
    action: "warn"
  - type: "nsfw"
    threshold: 0.9
    action: "delete"
EOF
    echo -e "${GREEN}✓ Example configuration created${NC}"
fi

# Create .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating environment file...${NC}"
    cat > .env.example << 'EOF'
# Telegram Bot Token from @BotFather
TELEGRAM_BOT_TOKEN=your-bot-token-here

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Performance settings
MAX_WORKERS=2
CACHE_SIZE=1000
RATE_LIMIT=10
EOF
    echo -e "${GREEN}✓ Example .env file created${NC}"
    echo -e "${YELLOW}Please edit .env.example and rename to .env with your bot token${NC}"
fi

# Create start script
echo -e "${YELLOW}Creating start script...${NC}"
cat > start_bot.sh << 'EOF'
#!/bin/bash

# Telegram Bot Starter Script

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if .env exists
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}No .env file found. Creating from example...${NC}"
        cp .env.example .env
        echo -e "${RED}Please edit .env file with your bot token!${NC}"
        exit 1
    fi
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check for bot token
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" == "your-bot-token-here" ]; then
    echo -e "${RED}Please set your bot token in .env file!${NC}"
    echo -e "${YELLOW}Get a token from @BotFather on Telegram${NC}"
    exit 1
fi

# Ask user preference
echo -e "${GREEN}How would you like to run the bot?${NC}"
echo "1) Docker (recommended)"
echo "2) Python directly"
echo "3) Web Dashboard"
echo "4) Preview Dashboard (Demo Mode)"
read -p "Choose [1-4]: " choice

case $choice in
    1)
        if command -v docker &> /dev/null; then
            echo -e "${GREEN}Starting bot with Docker...${NC}"
            docker-compose up -d
            echo -e "${GREEN}Bot started! View logs with: docker-compose logs -f${NC}"
        else
            echo -e "${RED}Docker not found. Please install Docker first.${NC}"
            exit 1
        fi
        ;;
    2)
        echo -e "${GREEN}Starting bot with Python...${NC}"
        source venv/bin/activate
        python src/bot.py
        ;;
    3)
        echo -e "${GREEN}Starting Web Dashboard...${NC}"
        source venv/bin/activate
        python src/web_dashboard.py
        ;;
    4)
        echo -e "${GREEN}Starting Dashboard Preview (Demo Mode)...${NC}"
        source venv/bin/activate
        python preview_dashboard.py
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac
EOF

chmod +x start_bot.sh
echo -e "${GREEN}✓ Start script created${NC}"

# Create stop script
cat > stop_bot.sh << 'EOF'
#!/bin/bash

# Stop the bot

if [ -f ".bot.pid" ]; then
    PID=$(cat .bot.pid)
    kill $PID 2>/dev/null && echo "Bot stopped (PID: $PID)" || echo "Bot not running"
    rm .bot.pid
fi

# Stop Docker if running
docker-compose down 2>/dev/null
EOF

chmod +x stop_bot.sh
echo -e "${GREEN}✓ Stop script created${NC}"

# Create update script
cat > update_bot.sh << 'EOF'
#!/bin/bash

# Update the bot

echo "Updating Telegram Moderation Bot..."

# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt

echo "Update complete! Restart the bot to apply changes."
EOF

chmod +x update_bot.sh
echo -e "${GREEN}✓ Update script created${NC}"

# Installation complete
echo
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}    Installation Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Get a bot token from @BotFather on Telegram"
echo -e "2. Edit .env file with your token"
echo -e "3. Run: ${GREEN}./start_bot.sh${NC}"
echo
echo -e "${BLUE}Quick Commands:${NC}"
echo -e "  Start bot:  ${GREEN}./start_bot.sh${NC}"
echo -e "  Stop bot:   ${GREEN}./stop_bot.sh${NC}"
echo -e "  Update bot: ${GREEN}./update_bot.sh${NC}"
echo -e "  View logs:  ${GREEN}docker-compose logs -f${NC} (if using Docker)"
echo
echo -e "${YELLOW}For detailed instructions, see docs/DEPLOYMENT_GUIDE.md${NC}"