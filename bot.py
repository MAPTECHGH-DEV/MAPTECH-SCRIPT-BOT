import os
import tempfile
import time
from datetime import datetime, timedelta
import random
import string
import subprocess
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, Filters

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
TELEGRAM_BOT_TOKEN = "7644583265:AAHn9OCzScFzaYDyr04uftuuPeVvc9SYJPs"  # Your Telegram Bot Token
ADMIN_USER_ID = 5989863155  # Your Telegram ID
BASE_BASH_SCRIPT_COMMAND = os.getenv("BASH_SCRIPT_COMMAND")

# Detect VPS public IP
def get_vps_ip():
    try:
        return subprocess.check_output(["curl", "-s", "ifconfig.me"]).decode("utf-8").strip()
    except subprocess.CalledProcessError:
        return "127.0.0.1"  # Fallback to localhost if IP detection fails

VPS_IP = get_vps_ip()

clients = {}
access_links = {}

# Function to generate a unique file name for each request
def generate_unique_filename():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id in clients and clients[user_id]["status"] == "blocked":
        update.message.reply_text("You are blocked from using this bot.")
        return
    update.message.reply_text("Welcome! Use /generate_link to generate a temporary link to the script.")

def grant_access(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ADMIN_USER_ID:
        update.message.reply_text("You are not authorized for this command.")
        return
    try:
        user_id = int(context.args[0])
        duration = int(context.args[1])
        clients[user_id] = {"status": "active", "access_duration": duration}
        update.message.reply_text(f"Access granted to user {user_id} for {duration} hours.")
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /grant_access <user_id> <duration_in_hours>")

def block_user(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ADMIN_USER_ID:
        update.message.reply_text("You are not authorized for this command.")
        return
    try:
        user_id = int(context.args[0])
        clients[user_id]["status"] = "blocked"
        update.message.reply_text(f"User {user_id} has been blocked.")
    except (IndexError, KeyError):
        update.message.reply_text("Usage: /block_user <user_id>")

def generate_link(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id not in clients or clients[user_id]["status"] == "blocked":
        update.message.reply_text("You are not authorized to generate links.")
        return

    # Generate a unique filename for each client/request
    unique_filename = generate_unique_filename()
    unique_file_path = f"/tmp/{unique_filename}.sh"

    # Create a temporary script file with the command
    with open(unique_file_path, "w") as f:
        f.write(f"{BASE_BASH_SCRIPT_COMMAND}\n")

    # Make the file executable
    os.chmod(unique_file_path, 0o755)

    # Generate the link and passcode
    expiration_time = datetime.now() + timedelta(hours=clients[user_id]["access_duration"])
    link_command = f"wget http://{VPS_IP}/{unique_filename}.sh -O - | bash"
    passcode = os.urandom(4).hex()
    
    access_links[user_id] = {"link": link_command, "expires": expiration_time, "passcode": passcode}

    update.message.reply_text(f"Generated command:\n{link_command}\nPasscode: {passcode}\nExpires in: {clients[user_id]['access_duration']} hours")

def check_status(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    status = clients.get(user_id, {}).get("status", "No access granted.")
    update.message.reply_text(f"Your current status: {status}")

def remove_expired_links(context: CallbackContext):
    current_time = datetime.now()
    for user_id, data in list(access_links.items()):
        if data["expires"] < current_time:
            del access_links[user_id]

def main():
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("grant_access", grant_access, Filters.user(user_id=ADMIN_USER_ID)))
    dispatcher.add_handler(CommandHandler("block_user", block_user, Filters.user(user_id=ADMIN_USER_ID)))
    dispatcher.add_handler(CommandHandler("generate_link", generate_link))
    dispatcher.add_handler(CommandHandler("status", check_status))
    updater.job_queue.run_repeating(remove_expired_links, interval=3600, first=0)
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
