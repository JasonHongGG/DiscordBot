"""
音樂播放模組 - 提供基本音樂播放功能
注意：需要安裝 yt-dlp 和 PyNaCl
"""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import asyncio

from utils.helpers import create_embed
from config import Colors, Emojis

# 注意：此模組需要額外的依賴：yt-dlp 和 PyNaCl
# 安裝：pip install yt-dlp PyNaCl


class Music(commands.Cog):
    """音樂播放（基礎版本）"""
    
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}  # 播放佇列
    
    # ==================== 加入語音頻道 ====================
    @commands.hybrid_command(name="join", description="加入你的語音頻道")
    async def join(self, ctx: commands.Context):
        """加入語音頻道"""
        if not ctx.author.voice:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="你必須先加入語音頻道！",
                    color=Colors.ERROR
                )
            )
        
        channel = ctx.author.voice.channel
        
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        
        embed = create_embed(
            title=f"{Emojis.SUCCESS} 已加入",
            description=f"已加入 {channel.mention}",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)
    
    # ==================== 離開語音頻道 ====================
    @commands.hybrid_command(name="leave", description="離開語音頻道")
    async def leave(self, ctx: commands.Context):
        """離開語音頻道"""
        if not ctx.voice_client:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="我不在任何語音頻道中",
                    color=Colors.ERROR
                )
            )
        
        await ctx.voice_client.disconnect()
        
        # 清除佇列
        if ctx.guild.id in self.queues:
            self.queues[ctx.guild.id].clear()
        
        embed = create_embed(
            title=f"{Emojis.SUCCESS} 已離開",
            description="已離開語音頻道",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)
    
    # ==================== 播放音樂（簡化版）====================
    @commands.hybrid_command(name="play", description="播放音樂（URL）")
    @app_commands.describe(url="音樂 URL")
    async def play(self, ctx: commands.Context, *, url: str):
        """播放音樂"""
        await ctx.send(
            embed=create_embed(
                title=f"{Emojis.INFO} 音樂功能",
                description="音樂播放功能需要額外配置和依賴（yt-dlp、PyNaCl）\n\n這是一個基礎框架，完整實現請參考 discord.py 音樂機器人教程",
                color=Colors.INFO
            )
        )
    
    # ==================== 暫停 ====================
    @commands.hybrid_command(name="pause", description="暫停播放")
    async def pause(self, ctx: commands.Context):
        """暫停"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            embed = create_embed(
                title=f"{Emojis.SUCCESS} 已暫停",
                description="音樂已暫停",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="目前沒有播放任何音樂",
                    color=Colors.ERROR
                )
            )
    
    # ==================== 繼續播放 ====================
    @commands.hybrid_command(name="resume", description="繼續播放")
    async def resume(self, ctx: commands.Context):
        """繼續播放"""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            embed = create_embed(
                title=f"{Emojis.SUCCESS} 繼續播放",
                description="音樂已繼續",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="音樂沒有暫停",
                    color=Colors.ERROR
                )
            )
    
    # ==================== 停止 ====================
    @commands.hybrid_command(name="stop", description="停止播放")
    async def stop(self, ctx: commands.Context):
        """停止"""
        if ctx.voice_client:
            ctx.voice_client.stop()
            if ctx.guild.id in self.queues:
                self.queues[ctx.guild.id].clear()
            
            embed = create_embed(
                title=f"{Emojis.SUCCESS} 已停止",
                description="音樂已停止",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="目前沒有播放任何音樂",
                    color=Colors.ERROR
                )
            )
    
    # ==================== 音量控制 ====================
    @commands.hybrid_command(name="volume", description="調整音量")
    @app_commands.describe(volume="音量 (0-100)")
    async def volume(self, ctx: commands.Context, volume: int):
        """調整音量"""
        if not ctx.voice_client:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="我不在任何語音頻道中",
                    color=Colors.ERROR
                )
            )
        
        if volume < 0 or volume > 100:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="音量必須在 0-100 之間",
                    color=Colors.ERROR
                )
            )
        
        if ctx.voice_client.source:
            ctx.voice_client.source.volume = volume / 100
        
        embed = create_embed(
            title=f"{Emojis.SUCCESS} 音量已設定",
            description=f"音量設定為 **{volume}%**",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Music(bot))
