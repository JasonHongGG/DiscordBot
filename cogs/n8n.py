"""
API Server Cog - 提供 HTTP API 接口
"""
from email.mime import message
import discord
from discord.ext import commands
import requests
from config import N8N_DISCORD_WEBHOOK_URL, ASSISTANT_CHANNEL_ID, N8N_RAG_WEBHOOK_URL, N8N_RAG_CHAT_WEBHOOK_URL


class N8N(commands.Cog):
    """N8N Cog - 處理 N8N 相關請求"""

    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id == ASSISTANT_CHANNEL_ID and not message.author.bot:
            payload = {
                "username": message.author.name,
                "content": message.content
            }
            requests.post(N8N_DISCORD_WEBHOOK_URL, json=payload)
            print(f"[n8n]✅ 已轉發訊息: {message.content} {N8N_DISCORD_WEBHOOK_URL}")

    @commands.hybrid_command(name="raginfo", description="新增 RAG 資訊")
    @commands.has_permissions(administrator=True)
    async def raginfo(self, ctx: commands.Context, message: str):
        payload = {
            "chatInput": message
        }
        requests.post(N8N_RAG_WEBHOOK_URL, json=payload)
        print(f"[n8n]✅ 已轉發訊息: {message} {N8N_RAG_WEBHOOK_URL}")

    @commands.hybrid_command(name="rag", description="RAG 聊天")
    @commands.has_permissions(administrator=True)
    async def rag(self, ctx: commands.Context, message: str):
        payload = {
            "chatInput": message
        }
        requests.post(N8N_RAG_CHAT_WEBHOOK_URL, json=payload)
        print(f"[n8n]✅ 已轉發訊息: {message} {N8N_RAG_CHAT_WEBHOOK_URL}")


async def setup(bot):
    await bot.add_cog(N8N(bot))
