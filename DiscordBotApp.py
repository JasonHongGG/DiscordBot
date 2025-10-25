"""
Discord 管理機器人主程式
功能包括：管理、歡迎、等級、經濟、娛樂、實用工具、音樂、反應角色、自動管理、日誌記錄
"""
import discord
from discord.ext import commands
import asyncio
import logging
from datetime import datetime, timezone

# 導入配置和工具
from config import DISCORD_TOKEN, BOT_PREFIX, INITIAL_COGS, Colors
from utils.logger import setup_logger
from utils.database import db
from utils.helpers import create_embed

# 設定日誌
logger = setup_logger()


class DiscordBot(commands.Bot):
    """自訂 Bot 類別"""
    
    def __init__(self):
        # 設定 Intents（權限）
        intents = discord.Intents.all()
        
        super().__init__(
            command_prefix=BOT_PREFIX,
            intents=intents,
            help_command=None,  # 使用自訂 help 指令
            case_insensitive=True
        )
        
        self.start_time = datetime.now()
    
    async def setup_hook(self):
        """機器人啟動時的設置"""
        logger.info("正在載入 Cogs...")
        
        # 載入所有 Cogs
        for cog in INITIAL_COGS:
            try:
                await self.load_extension(cog)
                logger.info(f"✓ 已載入: {cog}")
            except Exception as e:
                logger.error(f"✗ 載入失敗: {cog} - {e}")
        
        # 同步斜線指令
        try:
            logger.info("正在同步斜線指令...")
            synced = await self.tree.sync()
            logger.info(f"✓ 已同步 {len(synced)} 個斜線指令")
        except Exception as e:
            logger.error(f"✗ 同步斜線指令失敗: {e}")
    
    async def on_ready(self):
        """機器人就緒事件"""
        logger.info("=" * 50)
        logger.info(f"機器人已登入為: {self.user.name} (ID: {self.user.id})")
        logger.info(f"Discord.py 版本: {discord.__version__}")
        logger.info(f"伺服器數量: {len(self.guilds)}")
        logger.info(f"用戶數量: {sum(g.member_count for g in self.guilds)}")
        logger.info("=" * 50)
        
        # 設定狀態
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.guilds)} 個伺服器 | {BOT_PREFIX}help"
            )
        )
    
    async def on_guild_join(self, guild: discord.Guild):
        """加入新伺服器事件"""
        logger.info(f"加入了新伺服器: {guild.name} (ID: {guild.id})")
        
        # 更新狀態
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.guilds)} 個伺服器 | {BOT_PREFIX}help"
            )
        )
    
    async def on_guild_remove(self, guild: discord.Guild):
        """離開伺服器事件"""
        logger.info(f"離開了伺服器: {guild.name} (ID: {guild.id})")
        
        # 更新狀態
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.guilds)} 個伺服器 | {BOT_PREFIX}help"
            )
        )
    
    async def on_command_error(self, ctx: commands.Context, error):
        """指令錯誤處理"""
        if isinstance(error, commands.CommandNotFound):
            return  # 忽略未知指令
        
        elif isinstance(error, commands.MissingPermissions):
            embed = create_embed(
                title="❌ 權限不足",
                description=f"你沒有權限使用此指令\n需要權限: {', '.join(error.missing_permissions)}",
                color=Colors.ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
        
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = create_embed(
                title="❌ 參數錯誤",
                description=f"缺少必要參數: `{error.param.name}`\n請使用 `{BOT_PREFIX}help {ctx.command}` 查看用法",
                color=Colors.ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
        
        elif isinstance(error, commands.BadArgument):
            embed = create_embed(
                title="❌ 參數錯誤",
                description=f"參數格式錯誤\n請使用 `{BOT_PREFIX}help {ctx.command}` 查看用法",
                color=Colors.ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
        
        elif isinstance(error, commands.CommandOnCooldown):
            embed = create_embed(
                title="⏳ 冷卻中",
                description=f"此指令還在冷卻中\n請等待 {error.retry_after:.1f} 秒",
                color=Colors.WARNING
            )
            await ctx.send(embed=embed, delete_after=10)
        
        elif isinstance(error, commands.BotMissingPermissions):
            embed = create_embed(
                title="❌ 機器人權限不足",
                description=f"機器人缺少必要權限: {', '.join(error.missing_permissions)}",
                color=Colors.ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
        
        else:
            # 記錄未處理的錯誤
            logger.error(f"未處理的錯誤: {type(error).__name__}: {error}")
            embed = create_embed(
                title="❌ 發生錯誤",
                description=f"執行指令時發生錯誤\n錯誤類型: `{type(error).__name__}`",
                color=Colors.ERROR
            )
            await ctx.send(embed=embed, delete_after=10)


# 創建 Bot 實例
bot = DiscordBot()


# ==================== 自訂 Help 指令 ====================
@bot.hybrid_command(name="help", description="顯示幫助訊息")
async def help_command(ctx: commands.Context, command: str = None):
    """幫助指令"""
    if command:
        # 顯示特定指令的幫助
        cmd = bot.get_command(command)
        if cmd:
            embed = create_embed(
                title=f"📖 指令: {cmd.name}",
                description=cmd.description or "無描述",
                color=Colors.INFO
            )
            
            if cmd.aliases:
                embed.add_field(name="別名", value=", ".join(f"`{alias}`" for alias in cmd.aliases), inline=False)
            
            if cmd.usage:
                embed.add_field(name="用法", value=f"`{BOT_PREFIX}{cmd.name} {cmd.usage}`", inline=False)
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(
                embed=create_embed(
                    title="❌ 錯誤",
                    description=f"找不到指令: `{command}`",
                    color=Colors.ERROR
                )
            )
        return
    
    # 顯示所有指令分類
    embed = create_embed(
        title="📚 指令列表",
        description=f"使用 `{BOT_PREFIX}help <指令>` 查看詳細資訊\n或使用斜線指令 `/` 開頭",
        color=Colors.INFO
    )
    
    # 按 Cog 分組指令
    cogs_dict = {
        "管理功能": ["kick", "ban", "unban", "warn", "warnings", "clearwarnings", "mute", "unmute", "clear", "lock", "unlock", "slowmode", "nick"],
        "歡迎系統": ["setwelcome", "setfarewell", "setautorole"],
        "等級系統": ["rank", "leaderboard", "resetlevels"],
        "經濟系統": ["balance", "daily", "work", "deposit", "withdraw", "give", "richest"],
        "娛樂功能": ["8ball", "roll", "choose", "rps", "coinflip", "random", "cat", "dog", "poll"],
        "實用工具": ["serverinfo", "userinfo", "avatar", "ping", "botinfo", "roleinfo"],
        "音樂播放": ["join", "leave", "play", "pause", "resume", "stop", "volume"],
        "反應角色": ["reactionrole", "removereactionrole", "listreactionroles"],
        "自動管理": ["automod"],
        "日誌記錄": ["setlog"]
    }
    
    for category, commands_list in cogs_dict.items():
        commands_str = ", ".join(f"`{cmd}`" for cmd in commands_list)
        embed.add_field(name=f"**{category}**", value=commands_str, inline=False)
    
    embed.set_footer(text=f"共 {len(bot.commands)} 個指令")
    
    await ctx.send(embed=embed)


# ==================== 管理指令 ====================
@bot.command(name="reload", hidden=True)
@commands.is_owner()
async def reload_cog(ctx: commands.Context, cog: str):
    """重新載入 Cog"""
    try:
        await bot.reload_extension(f"cogs.{cog}")
        await ctx.send(f"✓ 已重新載入: cogs.{cog}")
        logger.info(f"{ctx.author} 重新載入了 cogs.{cog}")
    except Exception as e:
        await ctx.send(f"✗ 重新載入失敗: {e}")


@bot.command(name="load", hidden=True)
@commands.is_owner()
async def load_cog(ctx: commands.Context, cog: str):
    """載入 Cog"""
    try:
        await bot.load_extension(f"cogs.{cog}")
        await ctx.send(f"✓ 已載入: cogs.{cog}")
        logger.info(f"{ctx.author} 載入了 cogs.{cog}")
    except Exception as e:
        await ctx.send(f"✗ 載入失敗: {e}")


@bot.command(name="unload", hidden=True)
@commands.is_owner()
async def unload_cog(ctx: commands.Context, cog: str):
    """卸載 Cog"""
    try:
        await bot.unload_extension(f"cogs.{cog}")
        await ctx.send(f"✓ 已卸載: cogs.{cog}")
        logger.info(f"{ctx.author} 卸載了 cogs.{cog}")
    except Exception as e:
        await ctx.send(f"✗ 卸載失敗: {e}")


@bot.command(name="shutdown", hidden=True)
@commands.is_owner()
async def shutdown(ctx: commands.Context):
    """關閉機器人"""
    await ctx.send("👋 機器人正在關閉...")
    logger.info(f"{ctx.author} 關閉了機器人")
    await bot.close()


# ==================== 主程式 ====================
def main():
    """主函數"""
    if not DISCORD_TOKEN:
        logger.error("錯誤: 未找到 DISCORD_TOKEN")
        logger.error("請在 .env 檔案中設定 DISCORD_TOKEN")
        return
    
    try:
        logger.info("正在啟動機器人...")
        bot.run(DISCORD_TOKEN, log_handler=None)
    except KeyboardInterrupt:
        logger.info("收到中斷信號，正在關閉...")
    except Exception as e:
        logger.error(f"啟動失敗: {e}")


if __name__ == "__main__":
    main()