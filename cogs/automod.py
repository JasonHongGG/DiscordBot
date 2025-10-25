"""
自動管理模組 - 自動處理不當行為
包括: 垃圾訊息檢測、連結過濾、大寫檢測等
"""
import discord
from discord.ext import commands
from discord import app_commands
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import logging

from utils.database import db
from utils.helpers import create_embed
from config import Colors, Emojis

logger = logging.getLogger(__name__)


class AutoMod(commands.Cog):
    """自動管理系統"""
    
    def __init__(self, bot):
        self.bot = bot
        self.spam_tracker = defaultdict(list)  # 追蹤垃圾訊息
        self.link_pattern = re.compile(r'https?://\S+')
        self.invite_pattern = re.compile(r'discord\.gg/\w+|discordapp\.com/invite/\w+')
    
    def is_automod_enabled(self, guild_id: int) -> bool:
        """檢查是否啟用自動管理"""
        settings = db.get_guild_settings(guild_id)
        return settings.get('automod_enabled', False)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """訊息監控"""
        # 忽略機器人和管理員
        if message.author.bot or not message.guild:
            return
        
        if message.author.guild_permissions.administrator:
            return
        
        # 檢查是否啟用自動管理
        if not self.is_automod_enabled(message.guild.id):
            return
        
        # 垃圾訊息檢測
        await self.check_spam(message)
        
        # Discord 邀請連結檢測
        await self.check_invite_links(message)
        
        # 大量大寫檢測
        await self.check_caps(message)
        
        # 重複訊息檢測
        await self.check_duplicate(message)
    
    async def check_spam(self, message: discord.Message):
        """檢測垃圾訊息（短時間內大量訊息）"""
        user_id = message.author.id
        now = datetime.now()
        
        # 初始化用戶記錄
        self.spam_tracker[user_id] = [
            msg_time for msg_time in self.spam_tracker[user_id]
            if (now - msg_time).total_seconds() < 5
        ]
        
        # 添加當前訊息時間
        self.spam_tracker[user_id].append(now)
        
        # 如果 5 秒內超過 5 則訊息
        if len(self.spam_tracker[user_id]) >= 5:
            try:
                await message.author.timeout(
                    timedelta(minutes=5),
                    reason="自動管理：垃圾訊息"
                )
                await message.channel.send(
                    embed=create_embed(
                        title=f"{Emojis.WARNING} 自動管理",
                        description=f"{message.author.mention} 因發送垃圾訊息被靜音 5 分鐘",
                        color=Colors.WARNING
                    ),
                    delete_after=10
                )
                logger.info(f"自動管理: {message.author} 因垃圾訊息被靜音")
                self.spam_tracker[user_id].clear()
            except:
                pass
    
    async def check_invite_links(self, message: discord.Message):
        """檢測 Discord 邀請連結"""
        if self.invite_pattern.search(message.content):
            try:
                await message.delete()
                await message.channel.send(
                    embed=create_embed(
                        title=f"{Emojis.WARNING} 自動管理",
                        description=f"{message.author.mention} 不允許發送 Discord 邀請連結",
                        color=Colors.WARNING
                    ),
                    delete_after=5
                )
                logger.info(f"自動管理: 刪除了 {message.author} 的邀請連結")
            except:
                pass
    
    async def check_caps(self, message: discord.Message):
        """檢測大量大寫"""
        if len(message.content) < 10:
            return
        
        caps_count = sum(1 for c in message.content if c.isupper())
        caps_percentage = caps_count / len(message.content)
        
        # 如果超過 70% 是大寫
        if caps_percentage > 0.7:
            try:
                await message.delete()
                await message.channel.send(
                    embed=create_embed(
                        title=f"{Emojis.WARNING} 自動管理",
                        description=f"{message.author.mention} 請不要使用過多大寫字母",
                        color=Colors.WARNING
                    ),
                    delete_after=5
                )
                logger.info(f"自動管理: 刪除了 {message.author} 的大寫訊息")
            except:
                pass
    
    async def check_duplicate(self, message: discord.Message):
        """檢測重複訊息"""
        # 獲取最近的訊息
        recent_messages = []
        async for msg in message.channel.history(limit=5, before=message):
            if msg.author == message.author:
                recent_messages.append(msg.content)
        
        # 如果有 3 則相同訊息
        if recent_messages.count(message.content) >= 2:
            try:
                await message.delete()
                await message.channel.send(
                    embed=create_embed(
                        title=f"{Emojis.WARNING} 自動管理",
                        description=f"{message.author.mention} 請不要重複發送相同訊息",
                        color=Colors.WARNING
                    ),
                    delete_after=5
                )
                logger.info(f"自動管理: 刪除了 {message.author} 的重複訊息")
            except:
                pass
    
    # ==================== 啟用自動管理 ====================
    @commands.hybrid_command(name="automod", description="啟用/停用自動管理")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(enabled="是否啟用")
    async def automod(self, ctx: commands.Context, enabled: bool):
        """切換自動管理"""
        db.set_guild_settings(ctx.guild.id, automod_enabled=enabled)
        
        status = "啟用" if enabled else "停用"
        embed = create_embed(
            title=f"{Emojis.SUCCESS} 自動管理已{status}",
            description=f"自動管理系統已{status}\n\n功能包括:\n• 垃圾訊息檢測\n• Discord 邀請連結過濾\n• 大量大寫檢測\n• 重複訊息檢測",
            color=Colors.SUCCESS if enabled else Colors.WARNING
        )
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} {status}了自動管理")


async def setup(bot):
    await bot.add_cog(AutoMod(bot))
