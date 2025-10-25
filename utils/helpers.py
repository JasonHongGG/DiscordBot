"""
輔助函數模組 - 提供常用的輔助功能
"""
import discord
from discord.ext import commands
from typing import Optional, Union
from datetime import datetime, timedelta, timezone
import re
from config import Colors


def make_naive(dt: datetime) -> datetime:
    """
    移除 datetime 物件的時區資訊，使其成為 naive datetime
    
    Args:
        dt: datetime 物件
    
    Returns:
        沒有時區資訊的 datetime 物件
    """
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def create_embed(
    title: str = None,
    description: str = None,
    color: int = Colors.DEFAULT,
    footer: str = None,
    thumbnail: str = None,
    image: str = None,
    author: dict = None,
    fields: list = None
) -> discord.Embed:
    """
    創建 Embed 訊息
    
    Args:
        title: 標題
        description: 描述
        color: 顏色
        footer: 底部文字
        thumbnail: 縮圖 URL
        image: 圖片 URL
        author: 作者信息 {'name': '', 'icon_url': ''}
        fields: 欄位列表 [{'name': '', 'value': '', 'inline': bool}]
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now()
    )
    
    if footer:
        embed.set_footer(text=footer)
    
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    
    if image:
        embed.set_image(url=image)
    
    if author:
        embed.set_author(name=author.get('name', ''), icon_url=author.get('icon_url', ''))
    
    if fields:
        for field in fields:
            embed.add_field(
                name=field.get('name', ''),
                value=field.get('value', ''),
                inline=field.get('inline', True)
            )
    
    return embed


def parse_time(time_str: str) -> Optional[timedelta]:
    """
    解析時間字串（如 "1d", "2h", "30m", "1w"）
    
    Args:
        time_str: 時間字串
    
    Returns:
        timedelta 物件或 None
    """
    time_regex = re.compile(r"(\d+)([smhdw])")
    matches = time_regex.findall(time_str.lower())
    
    if not matches:
        return None
    
    total_seconds = 0
    for amount, unit in matches:
        amount = int(amount)
        if unit == 's':
            total_seconds += amount
        elif unit == 'm':
            total_seconds += amount * 60
        elif unit == 'h':
            total_seconds += amount * 3600
        elif unit == 'd':
            total_seconds += amount * 86400
        elif unit == 'w':
            total_seconds += amount * 604800
    
    return timedelta(seconds=total_seconds)


def format_time(seconds: int) -> str:
    """
    格式化秒數為可讀時間
    
    Args:
        seconds: 秒數
    
    Returns:
        格式化的時間字串
    """
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}天")
    if hours > 0:
        parts.append(f"{hours}小時")
    if minutes > 0:
        parts.append(f"{minutes}分鐘")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}秒")
    
    return " ".join(parts)


def format_number(number: int) -> str:
    """
    格式化數字（加入千分位逗號）
    
    Args:
        number: 數字
    
    Returns:
        格式化的數字字串
    """
    return f"{number:,}"


async def confirm_action(
    ctx: commands.Context,
    message: str,
    timeout: int = 30
) -> bool:
    """
    確認操作
    
    Args:
        ctx: 指令上下文
        message: 確認訊息
        timeout: 超時時間（秒）
    
    Returns:
        True 如果確認，False 如果取消
    """
    confirm_msg = await ctx.send(message)
    await confirm_msg.add_reaction("✅")
    await confirm_msg.add_reaction("❌")
    
    def check(reaction, user):
        return (
            user == ctx.author and
            str(reaction.emoji) in ["✅", "❌"] and
            reaction.message.id == confirm_msg.id
        )
    
    try:
        reaction, user = await ctx.bot.wait_for('reaction_add', timeout=timeout, check=check)
        await confirm_msg.delete()
        return str(reaction.emoji) == "✅"
    except:
        await confirm_msg.delete()
        return False


def has_permissions(**perms):
    """檢查權限裝飾器"""
    async def predicate(ctx):
        if ctx.author.id == ctx.bot.owner_id:
            return True
        
        permissions = ctx.channel.permissions_for(ctx.author)
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]
        
        if missing:
            raise commands.MissingPermissions(missing)
        return True
    
    return commands.check(predicate)


def calculate_level_xp(level: int) -> int:
    """
    計算達到某等級所需的總經驗值
    
    Args:
        level: 等級
    
    Returns:
        所需經驗值
    """
    from config import LEVEL_UP_BASE, LEVEL_UP_FACTOR
    return int(LEVEL_UP_BASE * (LEVEL_UP_FACTOR ** (level - 1)))


def get_level_from_xp(xp: int) -> int:
    """
    根據經驗值計算等級
    
    Args:
        xp: 經驗值
    
    Returns:
        等級
    """
    level = 0
    total_xp = 0
    
    while total_xp <= xp:
        level += 1
        total_xp += calculate_level_xp(level)
    
    return level - 1
