from flask import Flask, request, jsonify
import discord
from discord.ext import commands
import threading
import io
from DiscordBotApp import DiscordBotAppStart, bot
import asyncio


# Flask 設定
app = Flask(__name__)

# Flask API 路由
@app.route('/triggerAlarm', methods=['POST'])
def upload_image():
    # 確保有檔案上傳
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded_file = request.files['file']
    image_data = uploaded_file.read()
    msg = request.form.get('msg', '')

    # 將圖片資料傳給 Discord Bot
    async def send_to_channel():
        # 替換為你的目標頻道 ID
        channel_id = 1431725636359164025  # 替換為目標頻道的 ID
        channel = bot.get_channel(channel_id)
        if channel:
            discord_file = discord.File(fp=io.BytesIO(image_data), filename=uploaded_file.filename)
            await channel.send(f"這是透過 API 上傳的圖片：\n {msg}", file=discord_file)

    bot.loop.create_task(send_to_channel())
    return jsonify({"message": "圖片已成功上傳"}), 200

# 啟動 Flask 和 Discord Bot
def run_flask():
    app.run(host="0.0.0.0", port=6000)

def run_discord_bot():
    DiscordBotAppStart()

# 使用多執行緒啟動 Flask 和 Discord Bot
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(run_discord_bot())