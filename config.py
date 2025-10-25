"""
配置文件 - 存放所有機器人的配置信息
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Discord Token
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Bot 設定
BOT_PREFIX = "!"  # 指令前綴
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID", "0"))  # 機器人擁有者 ID

# 顏色設定（用於 Embed）
class Colors:
    SUCCESS = 0x00ff00  # 綠色
    ERROR = 0xff0000    # 紅色
    WARNING = 0xffaa00  # 橘色
    INFO = 0x3498db     # 藍色
    DEFAULT = 0x7289da  # Discord 藍

# 表情符號
class Emojis:
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    LOADING = "⏳"
    MUSIC = "🎵"
    LEVEL_UP = "⬆️"
    COIN = "💰"

# 資料庫設定
DATABASE_PATH = "data/bot_database.db"

# 日誌設定
LOG_FILE = "logs/bot.log"
LOG_LEVEL = "INFO"

# 等級系統設定
XP_PER_MESSAGE = 15  # 每則訊息獲得的經驗值
XP_COOLDOWN = 60  # 經驗值獲取冷卻時間（秒）
LEVEL_UP_BASE = 100  # 升級所需基礎經驗值
LEVEL_UP_FACTOR = 1.5  # 等級倍數

# 經濟系統設定
DAILY_REWARD = 1000  # 每日簽到獎勵
WORK_COOLDOWN = 3600  # 工作冷卻時間（秒）
WORK_REWARD_MIN = 50  # 工作最小獎勵
WORK_REWARD_MAX = 200  # 工作最大獎勵

# 警告系統設定
MAX_WARNINGS = 3  # 最大警告次數
AUTO_BAN_ON_MAX_WARNINGS = True  # 達到最大警告次數自動封禁

# 歡迎訊息設定
WELCOME_CHANNEL_NAME = "歡迎"  # 預設歡迎頻道名稱
FAREWELL_CHANNEL_NAME = "歡迎"  # 預設離開頻道名稱

# Cogs 列表（要載入的功能模組）
INITIAL_COGS = [
    "cogs.moderation",      # 管理功能
    "cogs.welcome",         # 歡迎系統
    "cogs.leveling",        # 等級系統
    "cogs.economy",         # 經濟系統
    "cogs.fun",            # 娛樂功能
    "cogs.utility",        # 實用工具
    "cogs.music",          # 音樂播放
    "cogs.reaction_roles", # 反應角色
    "cogs.automod",        # 自動管理
    "cogs.logging",        # 日誌記錄
]
