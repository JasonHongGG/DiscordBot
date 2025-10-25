"""
娛樂功能模組 - 提供各種有趣的指令
"""
import discord
from discord.ext import commands
from discord import app_commands
import random
import aiohttp
from typing import Optional

from utils.helpers import create_embed
from config import Colors, Emojis


class Fun(commands.Cog):
    """娛樂功能"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # ==================== 8球預言 ====================
    @commands.hybrid_command(name="8ball", description="問 8 球一個問題")
    @app_commands.describe(question="你的問題")
    async def eightball(self, ctx: commands.Context, *, question: str):
        """8球預言"""
        responses = [
            "當然可以。", "肯定是的。", "毫無疑問。", "是的，絕對的。",
            "你可以依賴它。", "據我所見，是的。", "很有可能。", "前景不錯。",
            "是的。", "跡象指向是的。", "回覆模糊，再試一次。", "稍後再問。",
            "最好現在不要告訴你。", "現在無法預測。", "專注後再問。",
            "不要指望。", "我的回答是不。", "我的消息來源說不。",
            "前景不太好。", "非常可疑。"
        ]
        
        embed = create_embed(
            title="🎱 8球預言",
            description=f"**問題:** {question}\n**答案:** {random.choice(responses)}",
            color=Colors.INFO
        )
        await ctx.send(embed=embed)
    
    # ==================== 擲骰子 ====================
    @commands.hybrid_command(name="roll", description="擲骰子")
    @app_commands.describe(dice="骰子格式 (例如: 2d6)")
    async def roll(self, ctx: commands.Context, dice: str = "1d6"):
        """擲骰子"""
        try:
            rolls, sides = map(int, dice.lower().split('d'))
            
            if rolls < 1 or rolls > 100:
                return await ctx.send(
                    embed=create_embed(
                        title=f"{Emojis.ERROR} 錯誤",
                        description="骰子數量必須在 1-100 之間",
                        color=Colors.ERROR
                    )
                )
            
            if sides < 2 or sides > 1000:
                return await ctx.send(
                    embed=create_embed(
                        title=f"{Emojis.ERROR} 錯誤",
                        description="骰子面數必須在 2-1000 之間",
                        color=Colors.ERROR
                    )
                )
            
            results = [random.randint(1, sides) for _ in range(rolls)]
            total = sum(results)
            
            if len(results) <= 10:
                results_str = ", ".join(map(str, results))
            else:
                results_str = f"{', '.join(map(str, results[:10]))}... (共 {rolls} 個骰子)"
            
            embed = create_embed(
                title="🎲 擲骰子",
                description=f"**骰子:** {dice}\n**結果:** {results_str}\n**總和:** {total}",
                color=Colors.INFO
            )
            await ctx.send(embed=embed)
        except ValueError:
            await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="格式錯誤！請使用如 `2d6` 的格式",
                    color=Colors.ERROR
                )
            )
    
    # ==================== 選擇 ====================
    @commands.hybrid_command(name="choose", description="讓機器人幫你選擇")
    @app_commands.describe(choices="選項 (用空格分隔)")
    async def choose(self, ctx: commands.Context, *, choices: str):
        """選擇"""
        choice_list = choices.split()
        
        if len(choice_list) < 2:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="請提供至少 2 個選項",
                    color=Colors.ERROR
                )
            )
        
        choice = random.choice(choice_list)
        
        embed = create_embed(
            title="🤔 選擇",
            description=f"**選項:** {', '.join(choice_list)}\n**我選擇:** **{choice}**",
            color=Colors.INFO
        )
        await ctx.send(embed=embed)
    
    # ==================== 猜拳 ====================
    @commands.hybrid_command(name="rps", description="剪刀石頭布")
    @app_commands.describe(choice="你的選擇 (石頭/布/剪刀)")
    async def rps(self, ctx: commands.Context, choice: str):
        """剪刀石頭布"""
        choices = {
            "石頭": "🪨",
            "布": "📄",
            "剪刀": "✂️",
            "rock": "🪨",
            "paper": "📄",
            "scissors": "✂️"
        }
        
        if choice.lower() not in choices:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="請選擇: 石頭、布或剪刀",
                    color=Colors.ERROR
                )
            )
        
        user_choice = choice.lower()
        if user_choice in ["rock", "paper", "scissors"]:
            mapping = {"rock": "石頭", "paper": "布", "scissors": "剪刀"}
            user_choice = mapping[user_choice]
        
        bot_choice = random.choice(["石頭", "布", "剪刀"])
        
        # 判斷勝負
        if user_choice == bot_choice:
            result = "平手！ 🤝"
            color = Colors.WARNING
        elif (
            (user_choice == "石頭" and bot_choice == "剪刀") or
            (user_choice == "布" and bot_choice == "石頭") or
            (user_choice == "剪刀" and bot_choice == "布")
        ):
            result = "你贏了！ 🎉"
            color = Colors.SUCCESS
        else:
            result = "你輸了！ 😢"
            color = Colors.ERROR
        
        embed = create_embed(
            title="✊ 剪刀石頭布",
            description=f"你: {choices[user_choice]} {user_choice}\n我: {choices[bot_choice]} {bot_choice}\n\n**{result}**",
            color=color
        )
        await ctx.send(embed=embed)
    
    # ==================== 翻硬幣 ====================
    @commands.hybrid_command(name="coinflip", description="翻硬幣")
    async def coinflip(self, ctx: commands.Context):
        """翻硬幣"""
        result = random.choice(["正面 🪙", "反面 🪙"])
        
        embed = create_embed(
            title="🪙 翻硬幣",
            description=f"結果: **{result}**",
            color=Colors.INFO
        )
        await ctx.send(embed=embed)
    
    # ==================== 隨機數字 ====================
    @commands.hybrid_command(name="random", description="生成隨機數字")
    @app_commands.describe(min_num="最小值", max_num="最大值")
    async def random_num(self, ctx: commands.Context, min_num: int = 1, max_num: int = 100):
        """隨機數字"""
        if min_num >= max_num:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="最小值必須小於最大值",
                    color=Colors.ERROR
                )
            )
        
        number = random.randint(min_num, max_num)
        
        embed = create_embed(
            title="🎲 隨機數字",
            description=f"範圍: **{min_num}** - **{max_num}**\n結果: **{number}**",
            color=Colors.INFO
        )
        await ctx.send(embed=embed)
    
    # ==================== 貓咪圖片 ====================
    @commands.hybrid_command(name="cat", description="隨機貓咪圖片")
    async def cat(self, ctx: commands.Context):
        """貓咪圖片"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("https://api.thecatapi.com/v1/images/search") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        embed = create_embed(
                            title="🐱 隨機貓咪",
                            color=Colors.INFO
                        )
                        embed.set_image(url=data[0]['url'])
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(
                            embed=create_embed(
                                title=f"{Emojis.ERROR} 錯誤",
                                description="無法獲取貓咪圖片",
                                color=Colors.ERROR
                            )
                        )
            except Exception as e:
                await ctx.send(
                    embed=create_embed(
                        title=f"{Emojis.ERROR} 錯誤",
                        description=f"發生錯誤: {str(e)}",
                        color=Colors.ERROR
                    )
                )
    
    # ==================== 狗狗圖片 ====================
    @commands.hybrid_command(name="dog", description="隨機狗狗圖片")
    async def dog(self, ctx: commands.Context):
        """狗狗圖片"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("https://dog.ceo/api/breeds/image/random") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        embed = create_embed(
                            title="🐶 隨機狗狗",
                            color=Colors.INFO
                        )
                        embed.set_image(url=data['message'])
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(
                            embed=create_embed(
                                title=f"{Emojis.ERROR} 錯誤",
                                description="無法獲取狗狗圖片",
                                color=Colors.ERROR
                            )
                        )
            except Exception as e:
                await ctx.send(
                    embed=create_embed(
                        title=f"{Emojis.ERROR} 錯誤",
                        description=f"發生錯誤: {str(e)}",
                        color=Colors.ERROR
                    )
                )
    
    # ==================== 投票 ====================
    @commands.hybrid_command(name="poll", description="創建投票")
    @app_commands.describe(question="問題", options="選項 (用逗號分隔)")
    async def poll(self, ctx: commands.Context, question: str, *, options: str):
        """創建投票"""
        option_list = [opt.strip() for opt in options.split(',')]
        
        if len(option_list) < 2:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="請提供至少 2 個選項",
                    color=Colors.ERROR
                )
            )
        
        if len(option_list) > 10:
            return await ctx.send(
                embed=create_embed(
                    title=f"{Emojis.ERROR} 錯誤",
                    description="最多只能有 10 個選項",
                    color=Colors.ERROR
                )
            )
        
        # 數字表情符號
        numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        description = "\n".join([f"{numbers[i]} {opt}" for i, opt in enumerate(option_list)])
        
        embed = create_embed(
            title=f"📊 {question}",
            description=description,
            color=Colors.INFO,
            footer=f"由 {ctx.author.display_name} 發起"
        )
        
        poll_msg = await ctx.send(embed=embed)
        
        # 添加反應
        for i in range(len(option_list)):
            await poll_msg.add_reaction(numbers[i])


async def setup(bot):
    await bot.add_cog(Fun(bot))
