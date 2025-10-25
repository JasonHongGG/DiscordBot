"""
管理功能模組 - 提供完整的伺服器管理功能
包括: 踢出、封禁、靜音、警告、清除訊息、鎖定頻道等
"""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from datetime import datetime, timedelta, timezone
import logging

from utils.database import db
from utils.helpers import create_embed, parse_time, format_time, confirm_action
from config import Colors, Emojis, MAX_WARNINGS, AUTO_BAN_ON_MAX_WARNINGS

logger = logging.getLogger(__name__)


class Moderation(commands.Cog):
    """管理功能模組"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # ==================== 踢出功能 ====================
    @commands.hybrid_command(name="kick", description="踢出成員")
    @commands.has_permissions(kick_members=True)
    @app_commands.describe(member="要踢出的成員", reason="踢出原因")
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "無原因"):
        """踢出成員"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 權限不足",
                    description="你無法踢出職位比你高或相同的成員",
                    color=Colors.ERROR
                )
            )
        
        if member == ctx.guild.owner:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 操作失敗",
                    description="無法踢出伺服器擁有者",
                    color=Colors.ERROR
                )
            )
        
        try:
            await member.kick(reason=f"{ctx.author} 執行踢出: {reason}")
            embed = create_embed(
                title=f"{Emojis.SUCCESS} 成員已踢出",
                description=f"**成員:** {member.mention}\n**原因:** {reason}\n**執行者:** {ctx.author.mention}",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} 踢出了 {member} (原因: {reason})")
        except Exception as e:
            await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 踢出失敗",
                    description=f"錯誤: {str(e)}",
                    color=Colors.ERROR
                )
            )
    
    # ==================== 封禁功能 ====================
    @commands.hybrid_command(name="ban", description="封禁成員")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(member="要封禁的成員", reason="封禁原因", delete_days="刪除幾天內的訊息")
    async def ban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        delete_days: Optional[int] = 0,
        *,
        reason: str = "無原因"
    ):
        """封禁成員"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 權限不足",
                    description="你無法封禁職位比你高或相同的成員",
                    color=Colors.ERROR
                )
            )
        
        if member == ctx.guild.owner:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 操作失敗",
                    description="無法封禁伺服器擁有者",
                    color=Colors.ERROR
                )
            )
        
        try:
            await member.ban(
                reason=f"{ctx.author} 執行封禁: {reason}",
                delete_message_days=min(delete_days, 7)
            )
            embed = create_embed(
                title=f"{Emojis.SUCCESS} 成員已封禁",
                description=f"**成員:** {member.mention}\n**原因:** {reason}\n**執行者:** {ctx.author.mention}",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} 封禁了 {member} (原因: {reason})")
        except Exception as e:
            await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 封禁失敗",
                    description=f"錯誤: {str(e)}",
                    color=Colors.ERROR
                )
            )
    
    # ==================== 解除封禁功能 ====================
    @commands.hybrid_command(name="unban", description="解除封禁")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(user_id="要解除封禁的用戶 ID")
    async def unban(self, ctx: commands.Context, user_id: str):
        """解除封禁"""
        try:
            user_id = int(user_id)
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            
            embed = create_embed(
                title=f"{Emojis.SUCCESS} 已解除封禁",
                description=f"**用戶:** {user.mention}\n**執行者:** {ctx.author.mention}",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} 解除了 {user} 的封禁")
        except ValueError:
            await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="請提供有效的用戶 ID",
                    color=Colors.ERROR
                )
            )
        except Exception as e:
            await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 解除封禁失敗",
                    description=f"錯誤: {str(e)}",
                    color=Colors.ERROR
                )
            )
    
    # ==================== 警告功能 ====================
    @commands.hybrid_command(name="warn", description="警告成員")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="要警告的成員", reason="警告原因")
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "無原因"):
        """警告成員"""
        # 記錄警告
        db.add_warning(ctx.guild.id, member.id, ctx.author.id, reason)
        
        # 查詢警告次數
        warning_count = db.count_warnings(ctx.guild.id, member.id)
        
        embed = create_embed(
            title=f"{Emojis.WARNING} 成員已被警告",
            description=f"**成員:** {member.mention}\n**原因:** {reason}\n**警告次數:** {warning_count}/{MAX_WARNINGS}\n**執行者:** {ctx.author.mention}",
            color=Colors.WARNING
        )
        await ctx.send(embed=embed)
        
        # 嘗試私訊成員
        try:
            dm_embed = create_embed(
                title=f"{Emojis.WARNING} 你在 {ctx.guild.name} 收到警告",
                description=f"**原因:** {reason}\n**警告次數:** {warning_count}/{MAX_WARNINGS}",
                color=Colors.WARNING
            )
            await member.send(embed=dm_embed)
        except:
            pass
        
        # 檢查是否達到最大警告次數
        if AUTO_BAN_ON_MAX_WARNINGS and warning_count >= MAX_WARNINGS:
            try:
                await member.ban(reason=f"累積 {MAX_WARNINGS} 次警告")
                await ctx.send(
                    embed=create_embed(
                        title=f"{Emojis.ERROR} 自動封禁",
                        description=f"{member.mention} 因累積 {MAX_WARNINGS} 次警告而被自動封禁",
                        color=Colors.ERROR
                    )
                )
            except Exception as e:
                logger.error(f"自動封禁失敗: {e}")
        
        logger.info(f"{ctx.author} 警告了 {member} (原因: {reason})")
    
    # ==================== 查看警告 ====================
    @commands.hybrid_command(name="warnings", description="查看成員的警告記錄")
    @app_commands.describe(member="要查看的成員")
    async def warnings(self, ctx: commands.Context, member: discord.Member):
        """查看警告記錄"""
        warnings = db.get_warnings(ctx.guild.id, member.id)
        
        if not warnings:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.INFO} 無警告記錄",
                    description=f"{member.mention} 沒有任何警告記錄",
                    color=Colors.INFO
                )
            )
        
        embed = create_embed(
            title=f"{Emojis.WARNING} {member.display_name} 的警告記錄",
            description=f"總共 {len(warnings)} 次警告",
            color=Colors.WARNING
        )
        
        for i, warning in enumerate(sorted(warnings, key=lambda x: x['timestamp'], reverse=True)[:10], 1):  # 只顯示最近 10 次
            moderator = ctx.guild.get_member(warning['moderator_id'])
            mod_name = moderator.display_name if moderator else "未知"
            timestamp = datetime.fromisoformat(warning['timestamp']).strftime("%Y-%m-%d %H:%M")
            
            embed.add_field(
                name=f"警告 #{i}",
                value=f"**原因:** {warning['reason']}\n**執行者:** {mod_name}\n**時間:** {timestamp}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    # ==================== 清除警告 ====================
    @commands.hybrid_command(name="clearwarnings", description="清除成員的警告")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(member="要清除警告的成員")
    async def clearwarnings(self, ctx: commands.Context, member: discord.Member):
        """清除警告"""
        db.clear_warnings(ctx.guild.id, member.id)
        
        embed = create_embed(
            title=f"{Emojis.SUCCESS} 警告已清除",
            description=f"已清除 {member.mention} 的所有警告記錄",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} 清除了 {member} 的警告")
    
    # ==================== 靜音功能 ====================
    @commands.hybrid_command(name="mute", description="靜音成員")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(
        member="要靜音的成員",
        duration="靜音時長 (例如: 1h, 30m, 1d)",
        reason="靜音原因"
    )
    async def mute(
        self,
        ctx: commands.Context,
        member: discord.Member,
        duration: str,
        *,
        reason: str = "無原因"
    ):
        """靜音成員"""
        time_delta = parse_time(duration)
        if not time_delta:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="無效的時間格式。請使用如: 1h, 30m, 1d",
                    color=Colors.ERROR
                )
            )
        
        try:
            until = datetime.now() + time_delta
            await member.timeout(until, reason=f"{ctx.author}: {reason}")
            
            # 記錄靜音
            db.set_mute(member.id, ctx.guild.id, until.isoformat(), reason)
            
            embed = create_embed(
                title=f"{Emojis.SUCCESS} 成員已靜音",
                description=f"**成員:** {member.mention}\n**時長:** {format_time(int(time_delta.total_seconds()))}\n**原因:** {reason}\n**執行者:** {ctx.author.mention}",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} 靜音了 {member} {duration} (原因: {reason})")
        except Exception as e:
            await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 靜音失敗",
                    description=f"錯誤: {str(e)}",
                    color=Colors.ERROR
                )
            )
    
    # ==================== 解除靜音 ====================
    @commands.hybrid_command(name="unmute", description="解除靜音")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="要解除靜音的成員")
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        """解除靜音"""
        try:
            await member.timeout(None)
            db.remove_mute(ctx.guild.id, member.id)
            
            embed = create_embed(
                title=f"{Emojis.SUCCESS} 已解除靜音",
                description=f"**成員:** {member.mention}\n**執行者:** {ctx.author.mention}",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} 解除了 {member} 的靜音")
        except Exception as e:
            await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 解除靜音失敗",
                    description=f"錯誤: {str(e)}",
                    color=Colors.ERROR
                )
            )
    
    # ==================== 清除訊息 ====================
    @commands.hybrid_command(name="clear", description="清除訊息")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(amount="要清除的訊息數量", member="只清除特定成員的訊息")
    async def clear(
        self,
        ctx: commands.Context,
        amount: int,
        member: Optional[discord.Member] = None
    ):
        """清除訊息"""
        if amount < 1 or amount > 100:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="請輸入 1-100 之間的數字",
                    color=Colors.ERROR
                ),
                delete_after=5
            )
        
        def check(msg):
            return member is None or msg.author == member
        
        try:
            deleted = await ctx.channel.purge(limit=amount + 1, check=check)
            
            embed = create_embed(
                title=f"{Emojis.SUCCESS} 訊息已清除",
                description=f"已清除 {len(deleted) - 1} 則訊息" + (f" (來自 {member.mention})" if member else ""),
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed, delete_after=5)
            logger.info(f"{ctx.author} 清除了 {len(deleted) - 1} 則訊息")
        except Exception as e:
            await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 清除失敗",
                    description=f"錯誤: {str(e)}",
                    color=Colors.ERROR
                )
            )
    
    # ==================== 鎖定頻道 ====================
    @commands.hybrid_command(name="lock", description="鎖定頻道")
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(channel="要鎖定的頻道")
    async def lock(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """鎖定頻道"""
        channel = channel or ctx.channel
        
        try:
            await channel.set_permissions(
                ctx.guild.default_role,
                send_messages=False,
                reason=f"{ctx.author} 鎖定頻道"
            )
            
            embed = create_embed(
                title=f"{Emojis.SUCCESS} 頻道已鎖定",
                description=f"{channel.mention} 已被鎖定\n**執行者:** {ctx.author.mention}",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} 鎖定了 {channel}")
        except Exception as e:
            await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 鎖定失敗",
                    description=f"錯誤: {str(e)}",
                    color=Colors.ERROR
                )
            )
    
    # ==================== 解鎖頻道 ====================
    @commands.hybrid_command(name="unlock", description="解鎖頻道")
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(channel="要解鎖的頻道")
    async def unlock(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """解鎖頻道"""
        channel = channel or ctx.channel
        
        try:
            await channel.set_permissions(
                ctx.guild.default_role,
                send_messages=None,
                reason=f"{ctx.author} 解鎖頻道"
            )
            
            embed = create_embed(
                title=f"{Emojis.SUCCESS} 頻道已解鎖",
                description=f"{channel.mention} 已被解鎖\n**執行者:** {ctx.author.mention}",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} 解鎖了 {channel}")
        except Exception as e:
            await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 解鎖失敗",
                    description=f"錯誤: {str(e)}",
                    color=Colors.ERROR
                )
            )
    
    # ==================== 慢速模式 ====================
    @commands.hybrid_command(name="slowmode", description="設定慢速模式")
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(seconds="慢速模式秒數 (0 為關閉)")
    async def slowmode(self, ctx: commands.Context, seconds: int):
        """設定慢速模式"""
        if seconds < 0 or seconds > 21600:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="請輸入 0-21600 秒之間的數字",
                    color=Colors.ERROR
                )
            )
        
        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            
            if seconds == 0:
                description = f"{ctx.channel.mention} 的慢速模式已關閉"
            else:
                description = f"{ctx.channel.mention} 的慢速模式已設為 {seconds} 秒"
            
            embed = create_embed(
                title=f"{Emojis.SUCCESS} 慢速模式已設定",
                description=description,
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} 設定 {ctx.channel} 慢速模式為 {seconds} 秒")
        except Exception as e:
            await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 設定失敗",
                    description=f"錯誤: {str(e)}",
                    color=Colors.ERROR
                )
            )
    
    # ==================== 暱稱管理 ====================
    @commands.hybrid_command(name="nick", description="修改成員暱稱")
    @commands.has_permissions(manage_nicknames=True)
    @app_commands.describe(member="要修改暱稱的成員", nickname="新暱稱")
    async def nick(self, ctx: commands.Context, member: discord.Member, *, nickname: str = None):
        """修改暱稱"""
        try:
            old_nick = member.display_name
            await member.edit(nick=nickname)
            
            embed = create_embed(
                title=f"{Emojis.SUCCESS} 暱稱已修改",
                description=f"**成員:** {member.mention}\n**舊暱稱:** {old_nick}\n**新暱稱:** {nickname or '重置為用戶名'}",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} 修改了 {member} 的暱稱")
        except Exception as e:
            await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 修改失敗",
                    description=f"錯誤: {str(e)}",
                    color=Colors.ERROR
                )
            )


async def setup(bot):
    await bot.add_cog(Moderation(bot))
