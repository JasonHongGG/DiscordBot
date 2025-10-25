"""
等級系統模組 - 提供經驗值和等級功能
"""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta, timezone
import logging

from utils.database import db
from utils.helpers import create_embed, calculate_level_xp, get_level_from_xp, format_number, make_naive
from config import Colors, Emojis, XP_PER_MESSAGE, XP_COOLDOWN

logger = logging.getLogger(__name__)


class Leveling(commands.Cog):
    """等級系統"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """訊息事件 - 給予經驗值"""
        # 忽略機器人和 DM
        if message.author.bot or not message.guild:
            return
        
        # 檢查冷卻時間
        user_data = db.get_level_data(message.guild.id, message.author.id)
        
        now = datetime.now()
        
        if user_data:
            if user_data['last_xp_time']:
                last_xp_time = make_naive(datetime.fromisoformat(user_data['last_xp_time']))
                if (now - last_xp_time).total_seconds() < XP_COOLDOWN:
                    return
            
            # 更新經驗值
            new_xp = user_data['xp'] + XP_PER_MESSAGE
            new_level = get_level_from_xp(new_xp)
            old_level = user_data['level']
            
            db.set_level_data(
                message.guild.id,
                message.author.id,
                new_xp,
                new_level,
                now.isoformat()
            )
            
            # 檢查是否升級
            if new_level > old_level:
                # 檢查是否啟用升級訊息
                settings = db.get_guild_settings(message.guild.id)
                
                if settings.get('level_up_message', True):
                    embed = create_embed(
                        title=f"{Emojis.LEVEL_UP} 恭喜升級!",
                        description=f"{message.author.mention} 升到了 **等級 {new_level}**!",
                        color=Colors.SUCCESS
                    )
                    await message.channel.send(embed=embed, delete_after=10)
                
                logger.info(f"{message.author} 升級到等級 {new_level}")
        else:
            # 創建新記錄
            db.set_level_data(
                message.guild.id,
                message.author.id,
                XP_PER_MESSAGE,
                0,
                now.isoformat()
            )
    
    # ==================== 查看等級 ====================
    @commands.hybrid_command(name="rank", description="查看等級資訊")
    @app_commands.describe(member="要查看的成員")
    async def rank(self, ctx: commands.Context, member: discord.Member = None):
        """查看等級"""
        member = member or ctx.author
        
        user_data = db.get_level_data(ctx.guild.id, member.id)
        
        if not user_data:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.INFO} 無等級資料",
                    description=f"{member.mention} 還沒有等級資料",
                    color=Colors.INFO
                )
            )
        
        current_xp = user_data['xp']
        current_level = user_data['level']
        
        # 計算下一級所需經驗
        xp_for_next = calculate_level_xp(current_level + 1)
        xp_for_current = calculate_level_xp(current_level) if current_level > 0 else 0
        xp_progress = current_xp - xp_for_current
        xp_needed = xp_for_next - xp_for_current
        
        # 計算排名
        all_users = db.get_top_levels(ctx.guild.id, limit=999999)
        rank = next((i for i, u in enumerate(all_users, 1) if u['user_id'] == member.id), 0)
        
        embed = create_embed(
            title=f"📊 {member.display_name} 的等級資訊",
            color=Colors.INFO,
            thumbnail=member.display_avatar.url
        )
        
        embed.add_field(name="等級", value=f"`{current_level}`", inline=True)
        embed.add_field(name="排名", value=f"`#{rank}`", inline=True)
        embed.add_field(name="總經驗", value=f"`{format_number(current_xp)}`", inline=True)
        embed.add_field(
            name="升級進度",
            value=f"`{format_number(xp_progress)} / {format_number(xp_needed)}` XP\n{'█' * int(xp_progress / xp_needed * 10)}{'░' * (10 - int(xp_progress / xp_needed * 10))} {int(xp_progress / xp_needed * 100)}%",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    # ==================== 排行榜 ====================
    @commands.hybrid_command(name="leaderboard", description="查看等級排行榜")
    async def leaderboard(self, ctx: commands.Context):
        """等級排行榜"""
        top_users = db.get_top_levels(ctx.guild.id, limit=10)
        
        if not top_users:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.INFO} 排行榜",
                    description="目前還沒有排行榜資料",
                    color=Colors.INFO
                )
            )
        
        embed = create_embed(
            title=f"🏆 {ctx.guild.name} 等級排行榜",
            description="前 10 名成員",
            color=Colors.INFO
        )
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, user_data in enumerate(top_users, 1):
            user = ctx.guild.get_member(user_data['user_id'])
            if user:
                medal = medals[i-1] if i <= 3 else f"`#{i}`"
                embed.add_field(
                    name=f"{medal} {user.display_name}",
                    value=f"等級: **{user_data['level']}** | 經驗: **{format_number(user_data['xp'])}**",
                    inline=False
                )
        
        await ctx.send(embed=embed)
    
    # ==================== 重置等級 ====================
    @commands.hybrid_command(name="resetlevels", description="重置伺服器所有等級資料")
    @commands.has_permissions(administrator=True)
    async def resetlevels(self, ctx: commands.Context):
        """重置等級"""
        from utils.helpers import confirm_action
        
        confirmed = await confirm_action(
            ctx,
            f"{Emojis.WARNING} 確定要重置伺服器所有等級資料嗎？此操作無法復原！(30秒內反應 ✅ 確認或 ❌ 取消)"
        )
        
        if confirmed:
            db.delete_all_levels(ctx.guild.id)
            embed = create_embed(
                title=f"{Emojis.SUCCESS} 等級已重置",
                description="已清除伺服器所有等級資料",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} 重置了伺服器等級資料")
        else:
            await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.INFO} 已取消",
                    description="等級重置已取消",
                    color=Colors.INFO
                )
            )


async def setup(bot):
    await bot.add_cog(Leveling(bot))
