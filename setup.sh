#!/bin/bash

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit
fi

# Update and install required packages
echo "Updating and installing required packages..."
apt-get update -y && apt-get upgrade -y
apt-get install -y python3 python3-pip python3-venv curl wget git

# Clone the bot repository from GitHub
echo "Cloning the bot repository..."
git clone https://github.com/MAPTECHGH-DEV/SSH-VPS-MANAGER.git
cd SSH-VPS-MANAGER

# Set up virtual environment
echo "Setting up virtual environment..."
python3 -m venv botenv
source botenv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install python-telegram-bot python-dotenv

# Create the .env file
echo "Configuring environment variables..."
cat > .env <<EOL
TELEGRAM_BOT_TOKEN="7644583265:AAHn9OCzScFzaYDyr04uftuuPeVvc9SYJPs"
ADMIN_USER_ID="5989863155"
BASH_SCRIPT_COMMAND="apt-get update -y; apt-get upgrade -y; wget https://raw.githubusercontent.com/MAPTECHGH-DEV/SSH-VPS-MANAGER/main/hehe; chmod 777 hehe; ./hehe"
EOL

# Create a systemd service for the bot
echo "Setting up systemd service..."
cat > /etc/systemd/system/telegram_bot.service <<EOL
[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
User=root
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/botenv/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Enable and start the bot service
echo "Enabling and starting the Telegram bot service..."
systemctl daemon-reload
systemctl enable telegram_bot.service
systemctl start telegram_bot.service

# Display service status
echo "Setup complete. Checking the status of the bot service..."
systemctl status telegram_bot.service
