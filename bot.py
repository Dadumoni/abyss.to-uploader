#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import time
import requests
from telethon import TelegramClient, events, Button
from datetime import datetime

# Configure logging
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    # Telegram API configuration
    API_ID = int(os.environ.get("API_ID", "20845715"))
    API_HASH = os.environ.get("API_HASH", "72b3a12322c4edeb6c35fe91376aae84")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "7826545314:AAFUcSKseRG1e_lDMxQ-FIKmd_A585hV7Xk")

# Initialize the client
bot = TelegramClient('abyss_bot', api_id=Config.API_ID, api_hash=Config.API_HASH).start(bot_token=Config.BOT_TOKEN)

def humanbytes(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

async def upload_to_abyss(file_path):
    try:
        # Get file information for proper upload
        file_name = os.path.basename(file_path)
        file_type = 'application/octet-stream'  # Default mime type
        
        # Prepare the file for upload to Hydrax
        files = {'file': (file_name, open(file_path, 'rb'), file_type)}
        
        # Upload to Hydrax endpoint
        response = requests.post('http://up.hydrax.net/1c7beabe036322d38c466f7c3dca9818', files=files)
        
        if response.status_code != 200:
            return None, f"Upload failed with status code: {response.status_code}"
        
        try:
            result = response.json()
            if isinstance(result, dict) and result.get("url"):
                return result["url"], None
            elif isinstance(result, str) and "http" in result:
                return result.strip(), None
            else:
                return None, "Upload failed: Invalid response format"
        except Exception as e:
            return None, f"Failed to parse response: {str(e)}"
            
    except Exception as e:
        return None, str(e)

@bot.on(events.NewMessage(pattern='^/start'))
async def start(event):
    await event.reply(
        "Welcome to Abyss.to Upload Bot! 📁\n\n"
        "Send me any file to upload it to Abyss.to\n"
        "I will give you a direct download link! 🔗"
    )

@bot.on(events.NewMessage(func=lambda e: e.is_private))
async def handle_files(event):
    try:
        # Check if message contains a file
        if not event.message.file:
            if not event.message.text.startswith('/'):
                await event.reply("Please send me a file to upload! 📁")
            return
        


        # Send initial status message
        status_msg = await event.reply("📥 Downloading your file...")
        
        # Get file information
        file_name = event.message.file.name or "unnamed_file"
        file_size = event.message.file.size
        
        # Download the file
        start_time = time.time()
        file_path = await event.message.download_media(file="downloads/" + file_name)
        
        await status_msg.edit(f"⚡ Uploading to Abyss.to...\n\n"
                             f"File: {file_name}\n"
                             f"Size: {humanbytes(file_size)}")
        
        # Upload to Abyss.to
        download_link, error = await upload_to_abyss(file_path)
        
        if error:
            await status_msg.edit(f"❌ Upload failed!\n\nError: {error}")
            if os.path.exists(file_path):
                os.remove(file_path)
            return
        
        # Calculate upload time
        upload_time = time.time() - start_time
        
        # Send success message
        await status_msg.edit(
            f"✅ File uploaded successfully!\n\n"
            f"📁 File: {file_name}\n"
            f"📦 Size: {humanbytes(file_size)}\n"
            f"⚡ Time: {round(upload_time, 2)} seconds",
            buttons=[
                [Button.url("📥 Download", download_link)],
                [Button.url("🌐 Visit Abyss.to", "https://abyss.to")]
            ]
        )
        

        
        # Clean up downloaded file
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        await event.reply(f"An error occurred: {str(e)}")
        logger.error(str(e))

def main():
    """Start the bot."""
    # Create downloads directory if it doesn't exist
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
        
    logger.info("Bot started...")
    bot.run_until_disconnected()

if __name__ == '__main__':
    main()