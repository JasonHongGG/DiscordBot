from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence

import discord

from config import Colors


def standard_embed(
    *,
    title: str,
    description: Optional[str] = None,
    color: int = Colors.INFO,
    requester: Optional[discord.abc.User] = None,
    thumbnail: Optional[str] = None,
    image: Optional[str] = None,
) -> discord.Embed:
    """Create a consistent, modern-looking embed with timestamp and optional footer.

    - title: Main title
    - description: Optional text body (supports markdown)
    - color: Embed accent color
    - requester: If provided, footer will show the requester name and avatar
    - thumbnail: Small image on the right
    - image: Large image below description
    """

    embed = discord.Embed(title=title, description=description, color=color)
    embed.timestamp = datetime.utcnow()

    if requester is not None:
        embed.set_footer(text=f"由 {getattr(requester, 'display_name', requester.name)} 發起")
        if getattr(requester, "display_avatar", None):
            embed.set_footer(
                text=f"由 {getattr(requester, 'display_name', requester.name)} 發起",
                icon_url=requester.display_avatar.url,  # type: ignore[attr-defined]
            )

    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if image:
        embed.set_image(url=image)

    return embed


def format_duration(ms: Optional[int]) -> str:
    if not ms or ms <= 0:
        return "0:00"
    seconds = int(ms // 1000)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def progress_bar(current_ms: int, total_ms: Optional[int], width: int = 20) -> str:
    if not total_ms or total_ms <= 0:
        return ""  # Unknown duration; skip progress bar
    current_ms = max(0, current_ms)
    total_ms = max(1, total_ms)
    ratio = min(1.0, current_ms / total_ms)
    pos = int(ratio * (width - 1))
    bar = []
    for i in range(width):
        if i == pos:
            bar.append("🔘")
        else:
            bar.append("▬")
    return "".join(bar)


def build_queue_page_embed(
    *,
    title: str,
    tracks: Sequence,
    page: int,
    per_page: int,
    total_count: int,
    color: int = Colors.INFO,
) -> discord.Embed:
    start = (page - 1) * per_page
    end = min(start + per_page, total_count)
    lines = []
    for idx, track in enumerate(tracks[start:end], start=start + 1):
        t_title = getattr(track, "title", "未知標題")
        t_url = getattr(track, "uri", None) or getattr(track, "url", None) or ""
        t_len = getattr(track, "length", None)
        dur = format_duration(t_len)
        line = f"`{idx}.` {f'[{t_title}]({t_url})' if t_url else t_title} `[{dur}]`"
        lines.append(line)

    embed = discord.Embed(title=title, color=color)
    embed.timestamp = datetime.utcnow()
    embed.description = "\n".join(lines) if lines else "(無)"
    embed.set_footer(text=f"第 {page} / {((total_count - 1) // per_page) + 1} 頁 • 總計 {total_count} 首")
    return embed
