"""
歡迎系統模組 - 處理成員加入/離開訊息
"""
import discord
from discord.ext import commands
from discord import app_commands
import logging

from utils.database import db
from utils.helpers import create_embed
from config import Colors, Emojis

logger = logging.getLogger(__name__)


class Welcome(commands.Cog):
    """歡迎系統"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """成員加入事件"""
        # 獲取歡迎頻道
        settings = db.get_guild_settings(member.guild.id)
        
        if settings.get('welcome_channel_id'):
            channel = member.guild.get_channel(settings['welcome_channel_id'])
            if channel:
                embed = create_embed(
                    title=f"{Emojis.SUCCESS} 歡迎加入!",
                    description=f"{member.mention} 歡迎來到 **{member.guild.name}**!\n\n你是第 **{member.guild.member_count}** 位成員",
                    color=Colors.SUCCESS,
                    thumbnail=member.display_avatar.url,
                    footer=f"用戶 ID: {member.id}"
                )
                embed.add_field(
                    name="📅 帳號創建時間",
                    value=f"<t:{int(member.created_at.timestamp())}:R>",
                    inline=True
                )
                await channel.send(embed=embed)
        
        # 自動角色
        if settings.get('autorole_id'):
            role = member.guild.get_role(settings['autorole_id'])
            if role:
                try:
                    await member.add_roles(role, reason="自動角色")
                    logger.info(f"為 {member} 添加了自動角色 {role.name}")
                except Exception as e:
                    logger.error(f"添加自動角色失敗: {e}")
        
        logger.info(f"{member} 加入了 {member.guild.name}")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """成員離開事件"""
        settings = db.get_guild_settings(member.guild.id)
        
        if settings.get('farewell_channel_id'):
            channel = member.guild.get_channel(settings['farewell_channel_id'])
            if channel:
                embed = create_embed(
                    title=f"{Emojis.WARNING} 成員離開",
                    description=f"**{member.display_name}** 離開了伺服器\n\n現在還有 **{member.guild.member_count}** 位成員",
                    color=Colors.WARNING,
                    thumbnail=member.display_avatar.url
                )
                await channel.send(embed=embed)
        
        logger.info(f"{member} 離開了 {member.guild.name}")
    
    # ==================== 設定歡迎頻道 ====================
    @commands.hybrid_command(name="setwelcome", description="設定歡迎頻道")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(channel="歡迎訊息頻道")
    async def setwelcome(self, ctx: commands.Context, channel: discord.TextChannel):
        """設定歡迎頻道"""
        db.set_guild_settings(ctx.guild.id, welcome_channel_id=channel.id)
        
        embed = create_embed(
            title=f"{Emojis.SUCCESS} 歡迎頻道已設定",
            description=f"歡迎訊息將發送到 {channel.mention}",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} 設定歡迎頻道為 {channel}")
    
    # ==================== 設定離開頻道 ====================
    @commands.hybrid_command(name="setfarewell", description="設定離開頻道")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(channel="離開訊息頻道")
    async def setfarewell(self, ctx: commands.Context, channel: discord.TextChannel):
        """設定離開頻道"""
        db.set_guild_settings(ctx.guild.id, farewell_channel_id=channel.id)
        
        embed = create_embed(
            title=f"{Emojis.SUCCESS} 離開頻道已設定",
            description=f"離開訊息將發送到 {channel.mention}",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} 設定離開頻道為 {channel}")
    
    # ==================== 設定自動角色 ====================
    @commands.hybrid_command(name="setautorole", description="設定新成員自動獲得的角色")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(role="要自動給予的角色")
    async def setautorole(self, ctx: commands.Context, role: discord.Role):
        """設定自動角色"""
        db.set_guild_settings(ctx.guild.id, autorole_id=role.id)
        
        embed = create_embed(
            title=f"{Emojis.SUCCESS} 自動角色已設定",
            description=f"新成員將自動獲得 {role.mention} 角色",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} 設定自動角色為 {role}")


async def setup(bot):
    await bot.add_cog(Welcome(bot))
