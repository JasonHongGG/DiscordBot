"""
實用工具模組 - 提供各種實用功能
"""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import platform
import psutil
from typing import Optional

from utils.helpers import create_embed, format_time
from config import Colors, Emojis


class Utility(commands.Cog):
    """實用工具"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # ==================== 伺服器資訊 ====================
    @commands.hybrid_command(name="serverinfo", description="顯示伺服器資訊")
    async def serverinfo(self, ctx: commands.Context):
        """伺服器資訊"""
        guild = ctx.guild
        
        # 計算成員統計
        total_members = guild.member_count
        humans = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])
        online = len([m for m in guild.members if m.status != discord.Status.offline])
        
        # 頻道統計
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        # 角色和表情符號
        roles = len(guild.roles)
        emojis = len(guild.emojis)
        
        embed = create_embed(
            title=f"📊 {guild.name} 伺服器資訊",
            color=Colors.INFO,
            thumbnail=guild.icon.url if guild.icon else None
        )
        
        embed.add_field(
            name="👑 擁有者",
            value=guild.owner.mention if guild.owner else "未知",
            inline=True
        )
        embed.add_field(
            name="🆔 ID",
            value=f"`{guild.id}`",
            inline=True
        )
        embed.add_field(
            name="📅 創建時間",
            value=f"<t:{int(guild.created_at.timestamp())}:R>",
            inline=True
        )
        embed.add_field(
            name=f"👥 成員 ({total_members})",
            value=f"👤 人類: {humans}\n🤖 機器人: {bots}\n🟢 在線: {online}",
            inline=True
        )
        embed.add_field(
            name=f"📝 頻道 ({text_channels + voice_channels})",
            value=f"💬 文字: {text_channels}\n🔊 語音: {voice_channels}\n📁 分類: {categories}",
            inline=True
        )
        embed.add_field(
            name="其他",
            value=f"🎭 角色: {roles}\n😀 表情符號: {emojis}\n🚀 加成等級: {guild.premium_tier}",
            inline=True
        )
        
        if guild.description:
            embed.add_field(
                name="📄 描述",
                value=guild.description,
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    # ==================== 用戶資訊 ====================
    @commands.hybrid_command(name="userinfo", description="顯示用戶資訊")
    @app_commands.describe(member="要查看的成員")
    async def userinfo(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """用戶資訊"""
        member = member or ctx.author
        
        embed = create_embed(
            title=f"👤 {member.display_name} 的資訊",
            color=member.color if member.color != discord.Color.default() else Colors.INFO,
            thumbnail=member.display_avatar.url
        )
        
        embed.add_field(
            name="🏷️ 用戶名",
            value=f"{member.name}#{member.discriminator}",
            inline=True
        )
        embed.add_field(
            name="🆔 ID",
            value=f"`{member.id}`",
            inline=True
        )
        embed.add_field(
            name="🤖 機器人",
            value="是" if member.bot else "否",
            inline=True
        )
        embed.add_field(
            name="📅 帳號創建",
            value=f"<t:{int(member.created_at.timestamp())}:R>",
            inline=True
        )
        embed.add_field(
            name="📥 加入時間",
            value=f"<t:{int(member.joined_at.timestamp())}:R>",
            inline=True
        )
        embed.add_field(
            name="🎭 角色數量",
            value=str(len(member.roles) - 1),
            inline=True
        )
        
        # 最高角色
        if member.top_role.name != "@everyone":
            embed.add_field(
                name="👑 最高角色",
                value=member.top_role.mention,
                inline=True
            )
        
        # 狀態
        status_emoji = {
            discord.Status.online: "🟢 在線",
            discord.Status.idle: "🟡 閒置",
            discord.Status.dnd: "🔴 勿擾",
            discord.Status.offline: "⚫ 離線"
        }
        
        # 顯示總體狀態
        status_text = status_emoji.get(member.status, "❓ 未知")
        
        # 添加平台詳細狀態
        platforms = []
        if member.desktop_status != discord.Status.offline:
            platforms.append(f"💻 桌面: {status_emoji.get(member.desktop_status, '❓')}")
        if member.mobile_status != discord.Status.offline:
            platforms.append(f"📱 手機: {status_emoji.get(member.mobile_status, '❓')}")
        if member.web_status != discord.Status.offline:
            platforms.append(f"🌐 網頁: {status_emoji.get(member.web_status, '❓')}")
        
        if platforms:
            status_text += "\n" + "\n".join(platforms)
        
        embed.add_field(
            name="📡 狀態",
            value=status_text,
            inline=False
        )
        
        # 活動資訊
        if member.activities:
            activities = []
            for activity in member.activities:
                if isinstance(activity, discord.Streaming):
                    activities.append(f"🎥 直播: {activity.name}")
                elif isinstance(activity, discord.Game):
                    activities.append(f"🎮 遊戲: {activity.name}")
                elif isinstance(activity, discord.Spotify):
                    activities.append(f"🎵 Spotify: {activity.title} - {activity.artist}")
                elif isinstance(activity, discord.CustomActivity):
                    if activity.name:
                        activities.append(f"💬 自訂狀態: {activity.name}")
                elif isinstance(activity, discord.Activity):
                    activities.append(f"📝 活動: {activity.name}")
            
            if activities:
                embed.add_field(
                    name="🎯 當前活動",
                    value="\n".join(activities),
                    inline=False
                )
        
        await ctx.send(embed=embed)
    
    # ==================== 頭像 ====================
    @commands.hybrid_command(name="avatar", description="顯示用戶頭像")
    @app_commands.describe(member="要查看的成員")
    async def avatar(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """頭像"""
        member = member or ctx.author
        
        embed = create_embed(
            title=f"{member.display_name} 的頭像",
            color=Colors.INFO
        )
        embed.set_image(url=member.display_avatar.url)
        embed.add_field(
            name="下載連結",
            value=f"[點擊下載]({member.display_avatar.url})",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    # ==================== Ping ====================
    @commands.hybrid_command(name="ping", description="查看機器人延遲")
    async def ping(self, ctx: commands.Context):
        """Ping"""
        latency = round(self.bot.latency * 1000)
        
        if latency < 100:
            color = Colors.SUCCESS
            emoji = "🟢"
        elif latency < 200:
            color = Colors.WARNING
            emoji = "🟡"
        else:
            color = Colors.ERROR
            emoji = "🔴"
        
        embed = create_embed(
            title=f"{emoji} Pong!",
            description=f"延遲: **{latency}ms**",
            color=color
        )
        await ctx.send(embed=embed)
    
    # ==================== 機器人資訊 ====================
    @commands.hybrid_command(name="botinfo", description="顯示機器人資訊")
    async def botinfo(self, ctx: commands.Context):
        """機器人資訊"""
        # 系統資訊
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # 機器人統計
        total_guilds = len(self.bot.guilds)
        total_members = sum(g.member_count for g in self.bot.guilds)
        total_channels = sum(len(g.channels) for g in self.bot.guilds)
        
        # 運行時間
        if hasattr(self.bot, 'start_time'):
            # 計算運行時間
            uptime_seconds = int((datetime.now() - self.bot.start_time).total_seconds())
            uptime = format_time(uptime_seconds)
        else:
            uptime = "未知"
        
        embed = create_embed(
            title=f"🤖 {self.bot.user.name} 資訊",
            color=Colors.INFO,
            thumbnail=self.bot.user.display_avatar.url
        )
        
        embed.add_field(
            name="📊 統計",
            value=f"🏠 伺服器: {total_guilds}\n👥 用戶: {total_members}\n📝 頻道: {total_channels}",
            inline=True
        )
        embed.add_field(
            name="⚙️ 系統",
            value=f"💻 CPU: {cpu_usage}%\n🧠 記憶體: {memory_usage}%\n🐍 Python: {platform.python_version()}",
            inline=True
        )
        embed.add_field(
            name="⏱️ 運行時間",
            value=uptime,
            inline=True
        )
        embed.add_field(
            name="📡 延遲",
            value=f"{round(self.bot.latency * 1000)}ms",
            inline=True
        )
        embed.add_field(
            name="🆔 ID",
            value=f"`{self.bot.user.id}`",
            inline=True
        )
        embed.add_field(
            name="📅 創建時間",
            value=f"<t:{int(self.bot.user.created_at.timestamp())}:R>",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    # ==================== 角色資訊 ====================
    @commands.hybrid_command(name="roleinfo", description="顯示角色資訊")
    @app_commands.describe(role="要查看的角色")
    async def roleinfo(self, ctx: commands.Context, role: discord.Role):
        """角色資訊"""
        embed = create_embed(
            title=f"🎭 {role.name} 角色資訊",
            color=role.color if role.color != discord.Color.default() else Colors.INFO
        )
        
        embed.add_field(
            name="🆔 ID",
            value=f"`{role.id}`",
            inline=True
        )
        embed.add_field(
            name="👥 成員數",
            value=str(len(role.members)),
            inline=True
        )
        embed.add_field(
            name="📅 創建時間",
            value=f"<t:{int(role.created_at.timestamp())}:R>",
            inline=True
        )
        embed.add_field(
            name="🎨 顏色",
            value=f"`{role.color}`",
            inline=True
        )
        embed.add_field(
            name="📍 位置",
            value=f"`{role.position}`",
            inline=True
        )
        embed.add_field(
            name="📌 單獨顯示",
            value="是" if role.hoist else "否",
            inline=True
        )
        embed.add_field(
            name="🔔 可提及",
            value="是" if role.mentionable else "否",
            inline=True
        )
        embed.add_field(
            name="🤖 由機器人管理",
            value="是" if role.managed else "否",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    # ==================== 清除 DM ====================
    @commands.command(name="cleardm", description="清除機器人的私訊")
    async def cleardm(self, ctx: commands.Context, amount: int = 10):
        """清除 DM"""
        if not isinstance(ctx.channel, discord.DMChannel):
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="此指令只能在私訊中使用",
                    color=Colors.ERROR
                )
            )
        
        deleted = 0
        async for message in ctx.channel.history(limit=amount):
            if message.author == self.bot.user:
                try:
                    await message.delete()
                    deleted += 1
                except:
                    pass
        
        await ctx.send(
            embed=create_embed(
                title=f"{Emojis.SUCCESS} 清除完成",
                description=f"已清除 {deleted} 則訊息",
                color=Colors.SUCCESS
            ),
            delete_after=5
        )


async def setup(bot):
    await bot.add_cog(Utility(bot))
