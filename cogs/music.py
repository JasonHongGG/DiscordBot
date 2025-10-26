"""
音樂播放模組（Lavalink 版本）
依賴：wavelink（Lavalink 客戶端）
說明：使用 Lavalink 播放音樂，避免本地 ffmpeg/yt-dlp 的限制。
"""
import asyncio
import logging
from typing import Dict, List, Optional

import discord
from discord import app_commands
from discord.ext import commands
import wavelink

from utils.helpers import create_embed
from config import Colors, Emojis, LAVALINK_HOST, LAVALINK_PORT, LAVALINK_PASSWORD

logger = logging.getLogger(__name__)


class GuildQueue:
    """每個伺服器的播放佇列與狀態"""

    def __init__(self):
        self.tracks: List[wavelink.Playable] = []
        self.current: Optional[wavelink.Playable] = None
        self.loop: bool = False
        self.volume: int = 60  # 0~100
        self.text_channel_id: Optional[int] = None

    def add(self, track: wavelink.Playable):
        self.tracks.append(track)

    def clear(self):
        self.tracks.clear()
        self.current = None

    def next(self) -> Optional[wavelink.Playable]:
        if self.loop and self.current is not None:
            return self.current
        if not self.tracks:
            self.current = None
            return None
        self.current = self.tracks.pop(0)
        return self.current

    def is_empty(self) -> bool:
        return (not self.tracks) and (self.current is None)


class Music(commands.Cog):
    """音樂播放系統（Lavalink/Wavelink）"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues: Dict[int, GuildQueue] = {}
        # 啟動時連線 Lavalink 節點
        self.bot.loop.create_task(self._connect_node())

    def get_queue(self, guild_id: int) -> GuildQueue:
        if guild_id not in self.queues:
            self.queues[guild_id] = GuildQueue()
        return self.queues[guild_id]

    async def _connect_node(self):
        await self.bot.wait_until_ready()
        try:
            logger.info("正在連線 Lavalink 節點...")
            node = wavelink.Node(
                uri=f"http://{LAVALINK_HOST}:{LAVALINK_PORT}",
                password=LAVALINK_PASSWORD,
            )
            await wavelink.Pool.connect(nodes=[node], client=self.bot)
            logger.info("✓ 已連線至 Lavalink 節點")
        except Exception as e:
            logger.error(f"✗ 無法連線到 Lavalink 節點: {e}")
            logger.error("請確認 Lavalink 伺服器已啟動且設定正確 (config.py 或 .env)")

    async def ensure_player(self, ctx: commands.Context) -> wavelink.Player:
        """確保機器人連到使用者所在語音頻道並取得 wavelink.Player"""
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError("你必須先加入語音頻道！")

        channel = ctx.author.voice.channel

        if ctx.voice_client and isinstance(ctx.voice_client, wavelink.Player):
            player: wavelink.Player = ctx.voice_client
            if player.channel.id != channel.id:
                await player.move_to(channel)
            return player

        player: wavelink.Player = await channel.connect(cls=wavelink.Player)
        queue = self.get_queue(ctx.guild.id)
        try:
            await player.set_volume(queue.volume)
        except Exception:
            pass
        return player

    async def _start_playback(self, ctx: commands.Context):
        player: Optional[wavelink.Player] = ctx.voice_client  # type: ignore
        if not player or not isinstance(player, wavelink.Player):
            return
        queue = self.get_queue(ctx.guild.id)

        track = queue.next()
        if not track:
            # 佇列空 → 3 分鐘後自動離開
            async def auto_leave():
                await asyncio.sleep(180)
                if ctx.voice_client and ctx.guild and self.get_queue(ctx.guild.id).current is None:
                    await ctx.voice_client.disconnect()
                    await ctx.send(embed=create_embed(
                        title=f"{Emojis.INFO} 播放結束",
                        description="佇列已空，已自動離開語音頻道",
                        color=Colors.INFO
                    ))
            self.bot.loop.create_task(auto_leave())
            return

        try:
            await player.play(track)
            await player.set_volume(queue.volume)
        except Exception as e:
            logger.error(f"播放時發生錯誤: {e}", exc_info=True)
            await ctx.send(embed=create_embed(
                title=f"{Emojis.ERROR} 播放錯誤",
                description=f"無法播放音樂\n```{str(e)}```",
                color=Colors.ERROR
            ))
            return

        # 播放訊息
        title = getattr(track, 'title', '未知標題')
        url = getattr(track, 'uri', None) or ''
        duration = getattr(track, 'length', None)  # 毫秒
        
        # 取得縮圖 URL（優先使用 artwork，YouTube 會提供）
        artwork = None
        if hasattr(track, 'artwork') and track.artwork:
            artwork = track.artwork
        elif hasattr(track, 'thumbnail') and track.thumbnail:
            artwork = track.thumbnail
        # YouTube 預設縮圖 fallback
        if not artwork and url and 'youtube.com' in url or 'youtu.be' in url:
            try:
                # 從 YouTube URL 提取 video ID 並建構縮圖 URL
                video_id = None
                if 'v=' in url:
                    video_id = url.split('v=')[1].split('&')[0]
                elif 'youtu.be/' in url:
                    video_id = url.split('youtu.be/')[1].split('?')[0]
                if video_id:
                    # 使用 sddefault.jpg (640x480, 16:9, 保證無黑邊)
                    artwork = f"https://img.youtube.com/vi/{video_id}/sddefault.jpg"
            except Exception:
                pass

        embed = create_embed(
            title=f"{Emojis.MUSIC} 正在播放",
            description=f"**[{title}]({url})**" if url else f"**{title}**",
            color=Colors.SUCCESS
        )
        if duration:
            total_seconds = int(duration // 1000)
            m, s = divmod(total_seconds, 60)
            embed.add_field(name="⏱️ 時長", value=f"{int(m)}:{int(s):02d}", inline=True)
        embed.add_field(name="🔊 音量", value=f"{int(queue.volume)}%", inline=True)
        
        if artwork:
            embed.set_image(url=artwork)
        
        await ctx.send(embed=embed)
    
    # ==================== 加入語音頻道 ====================
    @commands.hybrid_command(name="join", description="加入你的語音頻道")
    async def join(self, ctx: commands.Context):
        """加入語音頻道"""
        try:
            player = await self.ensure_player(ctx)
            embed = create_embed(
                title=f"{Emojis.SUCCESS} 已加入",
                description=f"已加入 {player.channel.mention}",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=create_embed(
                title=f"{Emojis.ERROR} 錯誤",
                description=str(e),
                color=Colors.ERROR
            ))
    
    # ==================== 離開語音頻道 ====================
    @commands.hybrid_command(name="leave", description="離開語音頻道")
    async def leave(self, ctx: commands.Context):
        """離開語音頻道"""
        if not ctx.voice_client:
            return await ctx.send(embed=create_embed(
                title=f"{Emojis.ERROR} 錯誤",
                description="我不在任何語音頻道中",
                color=Colors.ERROR
            ))
        queue = self.get_queue(ctx.guild.id)
        queue.clear()
        await ctx.voice_client.disconnect()
        await ctx.send(embed=create_embed(
            title=f"{Emojis.SUCCESS} 已離開",
            description="已離開語音頻道並清空佇列",
            color=Colors.SUCCESS
        ))
    
    # ==================== 播放音樂 ====================
    @commands.hybrid_command(name="play", description="播放音樂（支援 YouTube URL 或搜尋關鍵字）")
    @app_commands.describe(query="YouTube URL 或搜尋關鍵字")
    async def play(self, ctx: commands.Context, *, query: str):
        """播放音樂（支援 YouTube 連結或關鍵字）"""
        try:
            player = await self.ensure_player(ctx)
        except Exception as e:
            return await ctx.send(embed=create_embed(
                title=f"{Emojis.ERROR} 錯誤",
                description=str(e),
                color=Colors.ERROR
            ))

        # 記住文字頻道，之後自動播放用
        queue = self.get_queue(ctx.guild.id)
        queue.text_channel_id = ctx.channel.id

        processing = await ctx.send(embed=create_embed(
            title=f"{Emojis.INFO} 處理中...",
            description=f"正在搜尋: **{query}**",
            color=Colors.INFO
        ))

        try:
            # 使用 Wavelink 搜尋
            if query.startswith(("http://", "https://")):
                results = await wavelink.Playable.search(query)
            else:
                results = await wavelink.Playable.search(f"ytsearch:{query}")

            if not results:
                return await processing.edit(embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="找不到對應的歌曲",
                    color=Colors.ERROR
                ))

            track = results[0]
            queue.add(track)

            if not player.playing and not player.paused:
                await processing.delete()
                await self._start_playback(ctx)
            else:
                title = getattr(track, 'title', '未知標題')
                url = getattr(track, 'uri', None) or getattr(track, 'url', None) or ''
                duration = getattr(track, 'length', None)
                embed = create_embed(
                    title=f"{Emojis.SUCCESS} 已加入佇列",
                    description=f"**[{title}]({url})**" if url else f"**{title}**",
                    color=Colors.SUCCESS
                )
                embed.add_field(name="📝 佇列位置", value=f"第 {len(queue.tracks)} 首", inline=True)
                if duration:
                    total_seconds = int(duration // 1000)
                    m, s = divmod(total_seconds, 60)
                    embed.add_field(name="⏱️ 時長", value=f"{int(m)}:{int(s):02d}", inline=True)
                await processing.edit(embed=embed)
        except Exception as e:
            logger.error(f"搜尋/加入佇列錯誤: {e}", exc_info=True)
            await processing.edit(embed=create_embed(
                title=f"{Emojis.ERROR} 錯誤",
                description=f"載入音樂時發生錯誤\n```{str(e)}```",
                color=Colors.ERROR
            ))
    
    # ==================== 暫停 ====================
    @commands.hybrid_command(name="pause", description="暫停播放")
    async def pause(self, ctx: commands.Context):
        """暫停"""
        if not ctx.voice_client or not isinstance(ctx.voice_client, wavelink.Player):
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="我不在任何語音頻道中",
                    color=Colors.ERROR
                )
            )
        
        player: wavelink.Player = ctx.voice_client
        
        if player.paused:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.INFO} 提示",
                    description="音樂已經是暫停狀態",
                    color=Colors.INFO
                )
            )
        
        if player.current is None:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="目前沒有播放任何音樂",
                    color=Colors.ERROR
                )
            )
        
        await player.pause(True)
        embed = create_embed(
            title=f"{Emojis.SUCCESS} 已暫停",
            description="音樂已暫停",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)
    
    # ==================== 繼續播放 ====================
    @commands.hybrid_command(name="resume", description="繼續播放")
    async def resume(self, ctx: commands.Context):
        """繼續播放"""
        if ctx.voice_client and isinstance(ctx.voice_client, wavelink.Player):
            player: wavelink.Player = ctx.voice_client

            if player.paused:
                # Attempt to resume playback
                try:
                    await player.set_pause(False)  # Unpause the player
                    embed = create_embed(
                        title=f"{Emojis.SUCCESS} 繼續播放",
                        description="音樂已繼續",
                        color=Colors.SUCCESS
                    )
                    await ctx.send(embed=embed)
                except Exception as e:
                    await ctx.send(
                        embed=create_embed(
                            title=f"{Emojis.ERROR} 錯誤",
                            description=f"無法繼續播放: {str(e)}",
                            color=Colors.ERROR
                        )
                    )
            else:
                await ctx.send(
                    embed=create_embed(
                        title=f"{Emojis.INFO} 提示",
                        description="音樂未處於暫停狀態",
                        color=Colors.INFO
                    )
                )
        else:
            await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="目前沒有播放任何音樂",
                    color=Colors.ERROR
                )
            )
    
    # ==================== 跳過 ====================
    @commands.hybrid_command(name="skip", description="跳過當前歌曲")
    async def skip(self, ctx: commands.Context):
        """跳過"""
        if (not ctx.voice_client 
            or not isinstance(ctx.voice_client, wavelink.Player) 
            or ctx.voice_client.current is None):
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="目前沒有播放任何音樂",
                    color=Colors.ERROR
                )
            )
        await ctx.voice_client.stop()
        await ctx.send(
            embed=create_embed(
                title=f"{Emojis.SUCCESS} 已跳過",
                description="已跳過當前歌曲",
                color=Colors.SUCCESS
            )
        )
    
    # ==================== 停止 ====================
    @commands.hybrid_command(name="stop", description="停止播放並清空佇列")
    async def stop(self, ctx: commands.Context):
        """停止"""
        if (not ctx.voice_client 
            or not isinstance(ctx.voice_client, wavelink.Player)
            or ctx.voice_client.current is None):
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="目前沒有播放任何音樂",
                    color=Colors.ERROR
                )
            )
        
        queue = self.get_queue(ctx.guild.id)
        queue.clear()
        
        if ctx.voice_client.current is not None:
            await ctx.voice_client.stop()
        
        embed = create_embed(
            title=f"{Emojis.SUCCESS} 已停止",
            description="音樂已停止並清空佇列",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)
    
    # ==================== 佇列 ====================
    @commands.hybrid_command(name="queue", description="查看播放佇列")
    async def queue_cmd(self, ctx: commands.Context):
        """查看佇列"""
        queue = self.get_queue(ctx.guild.id)
        
        if queue.is_empty():
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.INFO} 佇列為空",
                    description="目前沒有任何歌曲在佇列中",
                    color=Colors.INFO
                )
            )
        
        embed = create_embed(
            title=f"{Emojis.MUSIC} 播放佇列",
            color=Colors.INFO
        )
        
        # 當前播放
        if queue.current:
            cur_title = getattr(queue.current, 'title', '未知標題')
            cur_url = getattr(queue.current, 'uri', None) or getattr(queue.current, 'url', None) or ''
            value = f"[{cur_title}]({cur_url})" if cur_url else cur_title
            embed.add_field(name="🎵 正在播放", value=value, inline=False)
        
        # 佇列中的歌曲
        if queue.tracks:
            queue_list = []
            for i, track in enumerate(queue.tracks[:10], 1):  # 只顯示前 10 首
                t_title = getattr(track, 'title', '未知標題')
                t_url = getattr(track, 'uri', None) or getattr(track, 'url', None) or ''
                t_len = getattr(track, 'length', None)
                duration = ""
                if t_len:
                    total_seconds = int(t_len // 1000)
                    m, s = divmod(total_seconds, 60)
                    duration = f" `[{int(m)}:{int(s):02d}]`"
                if t_url:
                    queue_list.append(f"`{i}.` [{t_title}]({t_url}){duration}")
                else:
                    queue_list.append(f"`{i}.` {t_title}{duration}")
            
            embed.add_field(
                name=f"📝 接下來 ({len(queue.tracks)} 首)",
                value="\n".join(queue_list),
                inline=False
            )
            
            if len(queue.tracks) > 10:
                embed.set_footer(text=f"還有 {len(queue.tracks) - 10} 首歌曲...")
        
        await ctx.send(embed=embed)
    
    # ==================== 正在播放 ====================
    @commands.hybrid_command(name="nowplaying", aliases=["np"], description="查看正在播放的歌曲")
    async def nowplaying(self, ctx: commands.Context):
        """正在播放"""
        queue = self.get_queue(ctx.guild.id)
        
        if (not ctx.voice_client 
            or not isinstance(ctx.voice_client, wavelink.Player)
            or ctx.voice_client.current is None):
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="目前沒有播放任何音樂",
                    color=Colors.ERROR
                )
            )
        
        source = queue.current
        
        # 取得標題與連結
        title = getattr(source, 'title', '未知標題')
        url = getattr(source, 'uri', None) or ''
        
        embed = create_embed(
            title=f"{Emojis.MUSIC} 正在播放",
            description=f"**[{title}]({url})**" if url else f"**{title}**",
            color=Colors.SUCCESS
        )
        
        if hasattr(source, 'length') and source.length:
            m, s = divmod(int(source.length // 1000), 60)
            embed.add_field(name="⏱️ 時長", value=f"{int(m)}:{int(s):02d}", inline=True)
        embed.add_field(name="🔊 音量", value=f"{int(queue.volume)}%", inline=True)
        
        if queue.loop:
            embed.add_field(name="🔁 循環", value="開啟", inline=True)
        
        # 取得縮圖
        artwork = None
        # if hasattr(source, 'artwork') and source.artwork:
        #     artwork = source.artwork
        # elif hasattr(source, 'thumbnail') and source.thumbnail:
        #     artwork = source.thumbnail

        # if not artwork:
        #     artwork = getattr(source, 'artwork', None)
        # YouTube 預設縮圖 fallback
        if not artwork and url and ('youtube.com' in url or 'youtu.be' in url):
            try:
                video_id = None
                if 'v=' in url:
                    video_id = url.split('v=')[1].split('&')[0]
                elif 'youtu.be/' in url:
                    video_id = url.split('youtu.be/')[1].split('?')[0]
                if video_id:
                    artwork = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            except Exception:
                pass
        
        if artwork:
            embed.set_image(url=artwork)
        
        await ctx.send(embed=embed)
    
    # ==================== 音量控制 ====================
    @commands.hybrid_command(name="volume", description="調整音量")
    @app_commands.describe(volume="音量 (0-100)")
    async def volume(self, ctx: commands.Context, volume: int):
        """調整音量"""
        if not ctx.voice_client or not isinstance(ctx.voice_client, wavelink.Player):
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
        
        queue = self.get_queue(ctx.guild.id)
        queue.volume = volume
        try:
            await ctx.voice_client.set_volume(volume)  # type: ignore
        except Exception:
            pass
        
        embed = create_embed(
            title=f"{Emojis.SUCCESS} 音量已設定",
            description=f"音量設定為 **{volume}%**",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)
    
    # ==================== 循環播放 ====================
    @commands.hybrid_command(name="loop", description="開啟/關閉循環播放")
    async def loop(self, ctx: commands.Context):
        """循環播放"""
        queue = self.get_queue(ctx.guild.id)
        queue.loop = not queue.loop
        
        status = "開啟" if queue.loop else "關閉"
        emoji = "🔁" if queue.loop else "⏹️"
        
        embed = create_embed(
            title=f"{emoji} 循環播放",
            description=f"循環播放已{status}",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)
    
    # ==================== 清空佇列 ====================
    @commands.hybrid_command(name="clearqueue", description="清空播放佇列")
    async def clearqueue(self, ctx: commands.Context):
        """清空佇列"""
        queue = self.get_queue(ctx.guild.id)
        
        if queue.is_empty():
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.INFO} 佇列為空",
                    description="佇列中沒有任何歌曲",
                    color=Colors.INFO
                )
            )
        cleared_count = len(queue.tracks)
        queue.tracks.clear()
        
        embed = create_embed(
            title=f"{Emojis.SUCCESS} 已清空佇列",
            description=f"已移除 {cleared_count} 首歌曲",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)

    # ==================== 事件：歌曲結束自動播放下一首 ====================
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        try:
            guild = payload.player.guild
        except Exception:
            return

        if guild is None:
            return

        queue = self.get_queue(guild.id)

        # 構建簡易 ctx 以便重用 _start_playback 流程
        channel = None
        if queue.text_channel_id:
            channel = guild.get_channel(queue.text_channel_id)
        if channel is None:
            channel = next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)

        class _Ctx:
            def __init__(self, g, vc, ch):
                self.guild = g
                self.voice_client = vc
                self.channel = ch
            async def send(self, *, embed=None):
                try:
                    if self.channel and embed:
                        await self.channel.send(embed=embed)
                except Exception:
                    pass

        fake_ctx = _Ctx(guild, guild.voice_client, channel)
        await self._start_playback(fake_ctx)

    # 事件：歌曲開始
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        try:
            guild = payload.player.guild
        except Exception:
            return
        if not guild:
            return
        queue = self.get_queue(guild.id)
        # 確保 current 與實際播放一致
        try:
            queue.current = payload.track  # type: ignore[attr-defined]
        except Exception:
            pass

    # 事件：播放異常
    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload):
        try:
            guild = payload.player.guild
        except Exception:
            return
        if not guild:
            return
        queue = self.get_queue(guild.id)
        channel = None
        if queue.text_channel_id:
            channel = guild.get_channel(queue.text_channel_id)
        if channel is None:
            channel = next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)

        message = str(getattr(payload, 'exception', '未知錯誤'))
        embed = create_embed(
            title=f"{Emojis.ERROR} 播放失敗",
            description=f"播放此曲目時發生錯誤\n```{message}```\n若是 YouTube 來源，請確認 Lavalink 已安裝 YouTube 插件。",
            color=Colors.ERROR
        )
        try:
            if channel:
                await channel.send(embed=embed)
        except Exception:
            pass


async def setup(bot):
    await bot.add_cog(Music(bot))


