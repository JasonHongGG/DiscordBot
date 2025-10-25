"""
API Server Cog - 提供 HTTP API 接口
"""
import discord
from discord.ext import commands
from flask import Flask, request, jsonify
import threading
import io
import asyncio
from config import API_SERVER_HOST, API_SERVER_PORT, ALARM_CHANNEL_ID


class APIServer(commands.Cog):
    """API Server Cog - 處理 HTTP API 請求"""
    
    def __init__(self, bot):
        self.bot = bot
        self.app = Flask(__name__)
        self.setup_routes()
        self.server_thread = None
        
    def setup_routes(self):
        """設置 Flask 路由"""
        
        @self.app.route('/triggerAlarm', methods=['POST'])
        def trigger_alarm():
            # 確保有檔案上傳
            if 'file' not in request.files:
                return jsonify({"error": "No file uploaded"}), 400

            uploaded_file = request.files['file']
            image_data = uploaded_file.read()

            # 獲取 msg 欄位
            msg = request.form.get('msg', '未提供訊息')

            # 將圖片資料傳給 Discord Bot
            async def send_to_channel():
                channel_id = ALARM_CHANNEL_ID  # 從配置文件讀取
                channel = self.bot.get_channel(channel_id)
                if channel:
                    discord_file = discord.File(
                        fp=io.BytesIO(image_data), 
                        filename=uploaded_file.filename
                    )
                    await channel.send(f"🚨 **警報通知**\n{msg}", file=discord_file)

            # 使用 asyncio 在 bot 的事件循環中執行
            asyncio.run_coroutine_threadsafe(send_to_channel(), self.bot.loop)
            return jsonify({"message": "圖片已成功上傳"}), 200
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """健康檢查端點"""
            return jsonify({
                "status": "ok",
                "bot_ready": self.bot.is_ready(),
                "bot_user": str(self.bot.user) if self.bot.user else None
            }), 200
    
    def run_server(self):
        """啟動 Flask 伺服器"""
        self.app.run(host=API_SERVER_HOST, port=API_SERVER_PORT, use_reloader=False)
    
    @commands.Cog.listener()
    async def on_ready(self):
        """當 Bot 準備就緒時啟動 Flask 伺服器"""
        if self.server_thread is None:
            self.server_thread = threading.Thread(target=self.run_server, daemon=True)
            self.server_thread.start()
            print(f"✅ Flask API 伺服器已啟動在 http://{API_SERVER_HOST}:{API_SERVER_PORT}")


async def setup(bot):
    await bot.add_cog(APIServer(bot))
