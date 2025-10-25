"""
經濟系統模組 - 提供虛擬貨幣功能
"""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta, timezone
import random
import logging

from utils.database import db
from utils.helpers import create_embed, format_number, make_naive
from config import Colors, Emojis, DAILY_REWARD, WORK_COOLDOWN, WORK_REWARD_MIN, WORK_REWARD_MAX

logger = logging.getLogger(__name__)


class Economy(commands.Cog):
    """經濟系統"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # ==================== 查看餘額 ====================
    @commands.hybrid_command(name="balance", aliases=["bal"], description="查看餘額")
    @app_commands.describe(member="要查看的成員")
    async def balance(self, ctx: commands.Context, member: discord.Member = None):
        """查看餘額"""
        member = member or ctx.author
        data = db.get_economy_data(ctx.guild.id, member.id)
        
        total = data['balance'] + data['bank']
        
        embed = create_embed(
            title=f"{Emojis.COIN} {member.display_name} 的錢包",
            color=Colors.INFO,
            thumbnail=member.display_avatar.url
        )
        
        embed.add_field(name="💵 現金", value=f"`{format_number(data['balance'])}` 金幣", inline=True)
        embed.add_field(name="🏦 銀行", value=f"`{format_number(data['bank'])}` 金幣", inline=True)
        embed.add_field(name="💰 總資產", value=f"`{format_number(total)}` 金幣", inline=True)
        
        await ctx.send(embed=embed)
    
    # ==================== 每日簽到 ====================
    @commands.hybrid_command(name="daily", description="每日簽到領取獎勵")
    async def daily(self, ctx: commands.Context):
        """每日簽到"""
        data = db.get_economy_data(ctx.guild.id, ctx.author.id)
        
        now = datetime.now()
        
        if data['last_daily']:
            last_daily = make_naive(datetime.fromisoformat(data['last_daily']))
            time_diff = now - last_daily
            
            if time_diff < timedelta(days=1):
                remaining = timedelta(days=1) - time_diff
                hours, remainder = divmod(remaining.seconds, 3600)
                minutes = remainder // 60
                
                return await ctx.send(
                    embed=create_embed(
                        title=f"{Emojis.ERROR} 已簽到過",
                        description=f"你已經領取過今天的簽到獎勵了！\n\n下次簽到時間: **{hours} 小時 {minutes} 分鐘**後",
                        color=Colors.ERROR
                    )
                )
        
        # 發放獎勵
        new_balance = data['balance'] + DAILY_REWARD
        db.set_economy_data(
            ctx.guild.id,
            ctx.author.id,
            balance=new_balance,
            last_daily=now.isoformat()
        )
        
        embed = create_embed(
            title=f"{Emojis.SUCCESS} 簽到成功!",
            description=f"你獲得了 **{format_number(DAILY_REWARD)}** 金幣！\n\n當前餘額: **{format_number(new_balance)}** 金幣",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} 完成每日簽到，獲得 {DAILY_REWARD} 金幣")
    
    # ==================== 工作賺錢 ====================
    @commands.hybrid_command(name="work", description="工作賺取金幣")
    async def work(self, ctx: commands.Context):
        """工作"""
        data = db.get_economy_data(ctx.guild.id, ctx.author.id)
        
        now = datetime.now()
        
        if data['last_work']:
            last_work = make_naive(datetime.fromisoformat(data['last_work']))
            time_diff = now - last_work
            
            if time_diff.total_seconds() < WORK_COOLDOWN:
                remaining = WORK_COOLDOWN - time_diff.total_seconds()
                minutes, seconds = divmod(int(remaining), 60)
                
                return await ctx.send(
                    embed=create_embed(
                        title=f"{Emojis.ERROR} 工作中...",
                        description=f"你還在工作中！\n\n下次可工作時間: **{minutes} 分鐘 {seconds} 秒**後",
                        color=Colors.ERROR
                    )
                )
        
        # 隨機工作和獎勵
        jobs = [
            "寫程式", "設計圖案", "賣咖啡", "送外賣", "教學生", 
            "修電腦", "做影片", "寫文章", "畫插畫", "做音樂"
        ]
        job = random.choice(jobs)
        reward = random.randint(WORK_REWARD_MIN, WORK_REWARD_MAX)
        
        new_balance = data['balance'] + reward
        db.set_economy_data(
            ctx.guild.id,
            ctx.author.id,
            balance=new_balance,
            last_work=now.isoformat()
        )
        
        embed = create_embed(
            title=f"{Emojis.SUCCESS} 工作完成!",
            description=f"你去 **{job}** 賺了 **{format_number(reward)}** 金幣！\n\n當前餘額: **{format_number(new_balance)}** 金幣",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} 工作獲得 {reward} 金幣")
    
    # ==================== 存款 ====================
    @commands.hybrid_command(name="deposit", aliases=["dep"], description="存款到銀行")
    @app_commands.describe(amount="存款金額 (all 為全部)")
    async def deposit(self, ctx: commands.Context, amount: str):
        """存款"""
        data = db.get_economy_data(ctx.guild.id, ctx.author.id)
        
        if amount.lower() == "all":
            amount = data['balance']
        else:
            try:
                amount = int(amount)
            except ValueError:
                return await ctx.send(
                    embed=create_embed(
                        title=f"{Emojis.ERROR} 錯誤",
                        description="請輸入有效的金額或 'all'",
                        color=Colors.ERROR
                    )
                )
        
        if amount <= 0:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="金額必須大於 0",
                    color=Colors.ERROR
                )
            )
        
        if amount > data['balance']:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 餘額不足",
                    description=f"你的現金只有 **{format_number(data['balance'])}** 金幣",
                    color=Colors.ERROR
                )
            )
        
        new_balance = data['balance'] - amount
        new_bank = data['bank'] + amount
        
        db.set_economy_data(
            ctx.guild.id,
            ctx.author.id,
            balance=new_balance,
            bank=new_bank
        )
        
        embed = create_embed(
            title=f"{Emojis.SUCCESS} 存款成功!",
            description=f"成功存入 **{format_number(amount)}** 金幣到銀行\n\n💵 現金: **{format_number(new_balance)}**\n🏦 銀行: **{format_number(new_bank)}**",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)
    
    # ==================== 提款 ====================
    @commands.hybrid_command(name="withdraw", aliases=["with"], description="從銀行提款")
    @app_commands.describe(amount="提款金額 (all 為全部)")
    async def withdraw(self, ctx: commands.Context, amount: str):
        """提款"""
        data = db.get_economy_data(ctx.guild.id, ctx.author.id)
        
        if amount.lower() == "all":
            amount = data['bank']
        else:
            try:
                amount = int(amount)
            except ValueError:
                return await ctx.send(
                    embed=create_embed(
                        title=f"{Emojis.ERROR} 錯誤",
                        description="請輸入有效的金額或 'all'",
                        color=Colors.ERROR
                    )
                )
        
        if amount <= 0:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="金額必須大於 0",
                    color=Colors.ERROR
                )
            )
        
        if amount > data['bank']:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 銀行餘額不足",
                    description=f"你的銀行只有 **{format_number(data['bank'])}** 金幣",
                    color=Colors.ERROR
                )
            )
        
        new_balance = data['balance'] + amount
        new_bank = data['bank'] - amount
        
        db.set_economy_data(
            ctx.guild.id,
            ctx.author.id,
            balance=new_balance,
            bank=new_bank
        )
        
        embed = create_embed(
            title=f"{Emojis.SUCCESS} 提款成功!",
            description=f"成功從銀行提款 **{format_number(amount)}** 金幣\n\n💵 現金: **{format_number(new_balance)}**\n🏦 銀行: **{format_number(new_bank)}**",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)
    
    # ==================== 給予金幣 ====================
    @commands.hybrid_command(name="give", description="給予金幣給其他成員")
    @app_commands.describe(member="要給予的成員", amount="金額")
    async def give(self, ctx: commands.Context, member: discord.Member, amount: int):
        """給予金幣"""
        if member == ctx.author:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="你不能給自己金幣！",
                    color=Colors.ERROR
                )
            )
        
        if member.bot:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="你不能給機器人金幣！",
                    color=Colors.ERROR
                )
            )
        
        if amount <= 0:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="金額必須大於 0",
                    color=Colors.ERROR
                )
            )
        
        author_data = db.get_economy_data(ctx.guild.id, ctx.author.id)
        
        if amount > author_data['balance']:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 餘額不足",
                    description=f"你的現金只有 **{format_number(author_data['balance'])}** 金幣",
                    color=Colors.ERROR
                )
            )
        
        member_data = db.get_economy_data(ctx.guild.id, member.id)
        
        # 轉帳
        new_author_balance = author_data['balance'] - amount
        new_member_balance = member_data['balance'] + amount
        
        db.set_economy_data(
            ctx.guild.id,
            ctx.author.id,
            balance=new_author_balance
        )
        db.set_economy_data(
            ctx.guild.id,
            member.id,
            balance=new_member_balance
        )
        
        embed = create_embed(
            title=f"{Emojis.SUCCESS} 轉帳成功!",
            description=f"{ctx.author.mention} 給了 {member.mention} **{format_number(amount)}** 金幣\n\n你的餘額: **{format_number(new_author_balance)}** 金幣",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} 給了 {member} {amount} 金幣")
    
    # ==================== 財富排行榜 ====================
    @commands.hybrid_command(name="richest", description="查看財富排行榜")
    async def richest(self, ctx: commands.Context):
        """財富排行榜"""
        top_users = db.get_top_economy(ctx.guild.id, limit=10)
        
        if not top_users:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.INFO} 排行榜",
                    description="目前還沒有排行榜資料",
                    color=Colors.INFO
                )
            )
        
        embed = create_embed(
            title=f"💰 {ctx.guild.name} 財富排行榜",
            description="前 10 名富豪",
            color=Colors.INFO
        )
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, user_data in enumerate(top_users, 1):
            user = ctx.guild.get_member(user_data['user_id'])
            if user:
                total = user_data['balance'] + user_data['bank']
                medal = medals[i-1] if i <= 3 else f"`#{i}`"
                embed.add_field(
                    name=f"{medal} {user.display_name}",
                    value=f"總資產: **{format_number(total)}** 金幣",
                    inline=False
                )
        
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Economy(bot))
