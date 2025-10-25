"""
反應角色模組 - 讓用戶透過反應獲得角色
"""
import discord
from discord.ext import commands
from discord import app_commands
import logging

from utils.database import db
from utils.helpers import create_embed
from config import Colors, Emojis

logger = logging.getLogger(__name__)


class ReactionRoles(commands.Cog):
    """反應角色系統"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """處理反應添加"""
        if payload.member.bot:
            return
        
        # 查詢是否為反應角色
        result = db.execute(
            "SELECT role_id FROM reaction_roles WHERE guild_id = ? AND message_id = ? AND emoji = ?",
            (payload.guild_id, payload.message_id, str(payload.emoji))
        )
        
        if result:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(result[0]['role_id'])
            
            if role:
                try:
                    await payload.member.add_roles(role, reason="反應角色")
                    logger.info(f"{payload.member} 通過反應獲得了角色 {role.name}")
                except Exception as e:
                    logger.error(f"添加反應角色失敗: {e}")
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """處理反應移除"""
        # 查詢是否為反應角色
        result = db.execute(
            "SELECT role_id FROM reaction_roles WHERE guild_id = ? AND message_id = ? AND emoji = ?",
            (payload.guild_id, payload.message_id, str(payload.emoji))
        )
        
        if result:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(result[0]['role_id'])
            member = guild.get_member(payload.user_id)
            
            if role and member:
                try:
                    await member.remove_roles(role, reason="移除反應角色")
                    logger.info(f"{member} 移除了反應角色 {role.name}")
                except Exception as e:
                    logger.error(f"移除反應角色失敗: {e}")
    
    # ==================== 創建反應角色 ====================
    @commands.hybrid_command(name="reactionrole", description="設定反應角色")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        message_id="訊息 ID",
        emoji="表情符號",
        role="要給予的角色"
    )
    async def reactionrole(
        self,
        ctx: commands.Context,
        message_id: str,
        emoji: str,
        role: discord.Role
    ):
        """設定反應角色"""
        try:
            message_id = int(message_id)
            message = await ctx.channel.fetch_message(message_id)
        except:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="無法找到該訊息，請確認訊息 ID 是否正確",
                    color=Colors.ERROR
                )
            )
        
        # 添加反應
        try:
            await message.add_reaction(emoji)
        except:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="無效的表情符號",
                    color=Colors.ERROR
                )
            )
        
        # 儲存到資料庫
        db.execute(
            "INSERT INTO reaction_roles (guild_id, message_id, role_id, emoji) VALUES (?, ?, ?, ?)",
            (ctx.guild.id, message_id, role.id, str(emoji))
        )
        
        embed = create_embed(
            title=f"{Emojis.SUCCESS} 反應角色已設定",
            description=f"對訊息反應 {emoji} 即可獲得 {role.mention} 角色",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} 設定了反應角色: {emoji} -> {role.name}")
    
    # ==================== 移除反應角色 ====================
    @commands.hybrid_command(name="removereactionrole", description="移除反應角色設定")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        message_id="訊息 ID",
        emoji="表情符號"
    )
    async def removereactionrole(self, ctx: commands.Context, message_id: str, emoji: str):
        """移除反應角色"""
        try:
            message_id = int(message_id)
        except:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="無效的訊息 ID",
                    color=Colors.ERROR
                )
            )
        
        result = db.execute(
            "DELETE FROM reaction_roles WHERE guild_id = ? AND message_id = ? AND emoji = ?",
            (ctx.guild.id, message_id, str(emoji))
        )
        
        embed = create_embed(
            title=f"{Emojis.SUCCESS} 反應角色已移除",
            description=f"已移除 {emoji} 的反應角色設定",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} 移除了反應角色: {emoji}")
    
    # ==================== 列出反應角色 ====================
    @commands.hybrid_command(name="listreactionroles", description="列出所有反應角色")
    async def listreactionroles(self, ctx: commands.Context):
        """列出反應角色"""
        result = db.execute(
            "SELECT * FROM reaction_roles WHERE guild_id = ?",
            (ctx.guild.id,)
        )
        
        if not result:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.INFO} 反應角色列表",
                    description="目前沒有設定任何反應角色",
                    color=Colors.INFO
                )
            )
        
        embed = create_embed(
            title=f"📋 反應角色列表",
            description=f"共 {len(result)} 個反應角色",
            color=Colors.INFO
        )
        
        for rr in result[:25]:  # 最多顯示 25 個
            role = ctx.guild.get_role(rr['role_id'])
            if role:
                embed.add_field(
                    name=f"{rr['emoji']} {role.name}",
                    value=f"訊息 ID: `{rr['message_id']}`",
                    inline=False
                )
        
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
