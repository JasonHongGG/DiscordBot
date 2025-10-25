"""
日誌記錄模組 - 記錄伺服器事件
包括: 訊息刪除、成員加入/離開、角色變更等
"""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import logging

from utils.database import db
from utils.helpers import create_embed
from config import Colors, Emojis

logger = logging.getLogger(__name__)


class Logging(commands.Cog):
    """日誌記錄系統"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def get_log_channel(self, guild_id: int):
        """獲取日誌頻道"""
        result = db.execute(
            "SELECT log_channel_id FROM guild_settings WHERE guild_id = ?",
            (guild_id,)
        )
        
        if result and result[0]['log_channel_id']:
            guild = self.bot.get_guild(guild_id)
            return guild.get_channel(result[0]['log_channel_id'])
        return None
    
    # ==================== 訊息刪除 ====================
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """訊息刪除事件"""
        if message.author.bot or not message.guild:
            return
        
        log_channel = self.get_log_channel(message.guild.id)
        if not log_channel:
            return
        
        embed = create_embed(
            title="🗑️ 訊息已刪除",
            color=Colors.ERROR
        )
        embed.add_field(name="作者", value=message.author.mention, inline=True)
        embed.add_field(name="頻道", value=message.channel.mention, inline=True)
        embed.add_field(name="內容", value=message.content[:1024] if message.content else "*無文字內容*", inline=False)
        embed.set_footer(text=f"用戶 ID: {message.author.id}")
        
        try:
            await log_channel.send(embed=embed)
        except:
            pass
    
    # ==================== 訊息編輯 ====================
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """訊息編輯事件"""
        if before.author.bot or not before.guild or before.content == after.content:
            return
        
        log_channel = self.get_log_channel(before.guild.id)
        if not log_channel:
            return
        
        embed = create_embed(
            title="✏️ 訊息已編輯",
            color=Colors.WARNING
        )
        embed.add_field(name="作者", value=before.author.mention, inline=True)
        embed.add_field(name="頻道", value=before.channel.mention, inline=True)
        embed.add_field(name="編輯前", value=before.content[:1024] if before.content else "*無內容*", inline=False)
        embed.add_field(name="編輯後", value=after.content[:1024] if after.content else "*無內容*", inline=False)
        embed.add_field(name="跳轉", value=f"[點擊查看]({after.jump_url})", inline=False)
        embed.set_footer(text=f"用戶 ID: {before.author.id}")
        
        try:
            await log_channel.send(embed=embed)
        except:
            pass
    
    # ==================== 成員加入 ====================
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """成員加入事件"""
        log_channel = self.get_log_channel(member.guild.id)
        if not log_channel:
            return
        
        embed = create_embed(
            title="📥 成員加入",
            description=f"{member.mention} 加入了伺服器",
            color=Colors.SUCCESS,
            thumbnail=member.display_avatar.url
        )
        embed.add_field(name="帳號創建", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="成員數", value=str(member.guild.member_count), inline=True)
        embed.set_footer(text=f"用戶 ID: {member.id}")
        
        try:
            await log_channel.send(embed=embed)
        except:
            pass
    
    # ==================== 成員離開 ====================
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """成員離開事件"""
        log_channel = self.get_log_channel(member.guild.id)
        if not log_channel:
            return
        
        embed = create_embed(
            title="📤 成員離開",
            description=f"**{member.display_name}** ({member.mention}) 離開了伺服器",
            color=Colors.ERROR,
            thumbnail=member.display_avatar.url
        )
        embed.add_field(name="加入時間", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)
        embed.add_field(name="成員數", value=str(member.guild.member_count), inline=True)
        
        # 顯示角色
        if len(member.roles) > 1:
            roles = ", ".join([r.mention for r in member.roles[1:6]])  # 最多顯示 5 個
            if len(member.roles) > 6:
                roles += f" +{len(member.roles) - 6} 個"
            embed.add_field(name="角色", value=roles, inline=False)
        
        embed.set_footer(text=f"用戶 ID: {member.id}")
        
        try:
            await log_channel.send(embed=embed)
        except:
            pass
    
    # ==================== 成員更新 ====================
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """成員更新事件"""
        log_channel = self.get_log_channel(before.guild.id)
        if not log_channel:
            return
        
        # 檢測暱稱變更
        if before.nick != after.nick:
            embed = create_embed(
                title="✏️ 暱稱變更",
                color=Colors.INFO
            )
            embed.add_field(name="成員", value=after.mention, inline=True)
            embed.add_field(name="舊暱稱", value=before.nick or "*無*", inline=True)
            embed.add_field(name="新暱稱", value=after.nick or "*無*", inline=True)
            embed.set_footer(text=f"用戶 ID: {after.id}")
            
            try:
                await log_channel.send(embed=embed)
            except:
                pass
        
        # 檢測角色變更
        if before.roles != after.roles:
            added_roles = set(after.roles) - set(before.roles)
            removed_roles = set(before.roles) - set(after.roles)
            
            if added_roles or removed_roles:
                embed = create_embed(
                    title="🎭 角色變更",
                    color=Colors.INFO
                )
                embed.add_field(name="成員", value=after.mention, inline=False)
                
                if added_roles:
                    roles_str = ", ".join([r.mention for r in added_roles])
                    embed.add_field(name="➕ 新增角色", value=roles_str, inline=False)
                
                if removed_roles:
                    roles_str = ", ".join([r.mention for r in removed_roles])
                    embed.add_field(name="➖ 移除角色", value=roles_str, inline=False)
                
                embed.set_footer(text=f"用戶 ID: {after.id}")
                
                try:
                    await log_channel.send(embed=embed)
                except:
                    pass
    
    # ==================== 頻道創建 ====================
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """頻道創建事件"""
        log_channel = self.get_log_channel(channel.guild.id)
        if not log_channel:
            return
        
        channel_type = "文字" if isinstance(channel, discord.TextChannel) else "語音" if isinstance(channel, discord.VoiceChannel) else "其他"
        
        embed = create_embed(
            title="➕ 頻道已創建",
            description=f"**{channel.mention}** ({channel_type}頻道)",
            color=Colors.SUCCESS
        )
        embed.set_footer(text=f"頻道 ID: {channel.id}")
        
        try:
            await log_channel.send(embed=embed)
        except:
            pass
    
    # ==================== 頻道刪除 ====================
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """頻道刪除事件"""
        log_channel = self.get_log_channel(channel.guild.id)
        if not log_channel:
            return
        
        channel_type = "文字" if isinstance(channel, discord.TextChannel) else "語音" if isinstance(channel, discord.VoiceChannel) else "其他"
        
        embed = create_embed(
            title="➖ 頻道已刪除",
            description=f"**{channel.name}** ({channel_type}頻道)",
            color=Colors.ERROR
        )
        embed.set_footer(text=f"頻道 ID: {channel.id}")
        
        try:
            await log_channel.send(embed=embed)
        except:
            pass
    
    # ==================== 設定日誌頻道 ====================
    @commands.hybrid_command(name="setlog", description="設定日誌頻道")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(channel="日誌頻道")
    async def setlog(self, ctx: commands.Context, channel: discord.TextChannel):
        """設定日誌頻道"""
        db.execute(
            "INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)",
            (ctx.guild.id,)
        )
        db.execute(
            "UPDATE guild_settings SET log_channel_id = ? WHERE guild_id = ?",
            (channel.id, ctx.guild.id)
        )
        
        embed = create_embed(
            title=f"{Emojis.SUCCESS} 日誌頻道已設定",
            description=f"日誌將發送到 {channel.mention}",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} 設定日誌頻道為 {channel}")


async def setup(bot):
    await bot.add_cog(Logging(bot))
