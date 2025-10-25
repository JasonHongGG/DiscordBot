# Discord 管理機器人

這是一個功能完整、結構化的 Discord 管理機器人，包含多種實用功能。

## 📋 功能特色

### 🛡️ 管理功能
- **成員管理**: 踢出、封禁、解除封禁
- **警告系統**: 警告成員、查看警告記錄、清除警告
- **靜音系統**: 臨時靜音、解除靜音
- **訊息管理**: 清除訊息、慢速模式
- **頻道管理**: 鎖定/解鎖頻道
- **暱稱管理**: 修改成員暱稱

### 👋 歡迎系統
- 成員加入歡迎訊息
- 成員離開通知
- 自動角色分配

### ⬆️ 等級系統
- 發送訊息獲得經驗值
- 等級排行榜
- 升級通知

### 💰 經濟系統
- 虛擬貨幣系統
- 每日簽到獎勵
- 工作賺錢
- 存款/提款系統
- 金幣轉帳
- 財富排行榜

### 🎮 娛樂功能
- 8球預言
- 擲骰子
- 剪刀石頭布
- 翻硬幣
- 隨機選擇
- 隨機數字
- 貓咪/狗狗圖片
- 投票系統

### 🔧 實用工具
- 伺服器資訊
- 用戶資訊
- 角色資訊
- 頭像查看
- Ping 測試
- 機器人資訊

### 🎵 音樂播放（基礎框架）
- 加入/離開語音頻道
- 播放/暫停/繼續
- 音量控制

### 🎭 反應角色
- 設定反應角色
- 自動給予/移除角色

### 🤖 自動管理
- 垃圾訊息檢測
- Discord 邀請連結過濾
- 大量大寫檢測
- 重複訊息檢測

### 📝 日誌記錄
- 訊息刪除/編輯記錄
- 成員加入/離開記錄
- 成員更新記錄（暱稱、角色）
- 頻道創建/刪除記錄

## 🚀 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 設定環境變數

複製 `.env.example` 為 `.env` 並填入你的 Discord Bot Token：

```bash
cp .env.example .env
```

編輯 `.env` 檔案：
```
DISCORD_TOKEN=你的_Discord_Bot_Token
BOT_OWNER_ID=你的_Discord_用戶_ID
```

### 3. 取得 Discord Bot Token

1. 前往 [Discord Developer Portal](https://discord.com/developers/applications)
2. 點擊 "New Application" 創建新應用
3. 進入 "Bot" 頁面，點擊 "Add Bot"
4. 點擊 "Reset Token" 複製 Token
5. 在 "Privileged Gateway Intents" 區域啟用所有 Intents：
   - ✅ Presence Intent
   - ✅ Server Members Intent
   - ✅ Message Content Intent

### 4. 邀請機器人

使用以下 URL 格式邀請機器人（替換 CLIENT_ID）：
```
https://discord.com/api/oauth2/authorize?client_id=CLIENT_ID&permissions=8&scope=bot%20applications.commands
```

CLIENT_ID 在 Developer Portal 的 "General Information" 頁面。

### 5. 啟動機器人

```bash
python DiscordBotApp.py
```

## 📁 專案結構

```
DiscordBot/
├── DiscordBotApp.py        # 主程式
├── config.py               # 配置文件
├── requirements.txt        # 依賴套件
├── .env                    # 環境變數（不要上傳到 Git）
├── .env.example           # 環境變數範例
├── README.md              # 說明文件
├── cogs/                  # 功能模組
│   ├── moderation.py      # 管理功能
│   ├── welcome.py         # 歡迎系統
│   ├── leveling.py        # 等級系統
│   ├── economy.py         # 經濟系統
│   ├── fun.py            # 娛樂功能
│   ├── utility.py        # 實用工具
│   ├── music.py          # 音樂播放
│   ├── reaction_roles.py # 反應角色
│   ├── automod.py        # 自動管理
│   └── logging.py        # 日誌記錄
├── utils/                # 工具模組
│   ├── database.py       # 資料庫管理
│   ├── helpers.py        # 輔助函數
│   └── logger.py         # 日誌系統
├── data/                 # 資料庫文件
│   └── bot_database.db
└── logs/                 # 日誌文件
    └── bot.log
```

## 💡 使用說明

### 基本指令

- `!help` - 查看所有指令
- `!help <指令>` - 查看特定指令的詳細資訊

### 管理指令範例

```
!kick @用戶 [原因]            - 踢出成員
!ban @用戶 [原因]             - 封禁成員
!warn @用戶 [原因]            - 警告成員
!mute @用戶 1h [原因]         - 靜音 1 小時
!clear 10                     - 清除 10 則訊息
!lock                         - 鎖定當前頻道
```

### 設定指令範例

```
!setwelcome #歡迎頻道         - 設定歡迎頻道
!setlog #日誌頻道             - 設定日誌頻道
!setautorole @角色            - 設定自動角色
!automod true                 - 啟用自動管理
```

### 經濟系統範例

```
!balance                      - 查看餘額
!daily                        - 每日簽到
!work                         - 工作賺錢
!deposit 100                  - 存入 100 金幣
!give @用戶 100               - 給予用戶 100 金幣
```

### 反應角色設定

```
!reactionrole 訊息ID 表情 @角色   - 設定反應角色
!listreactionroles                - 列出所有反應角色
```

## ⚙️ 配置

在 `config.py` 中可以自訂：
- 指令前綴
- 經驗值設定
- 經濟系統設定
- 警告系統設定
- 顏色和表情符號

## 🔐 權限需求

機器人需要以下權限才能正常運作：
- 管理員（推薦）或以下特定權限：
  - 管理訊息
  - 踢出成員
  - 封禁成員
  - 管理角色
  - 管理頻道
  - 管理暱稱
  - 查看審計日誌
  - 靜音成員

## 🛠️ 擴展功能

### 添加新功能模組

1. 在 `cogs/` 目錄創建新的 `.py` 文件
2. 創建繼承自 `commands.Cog` 的類別
3. 添加指令和事件監聽器
4. 在 `config.py` 的 `INITIAL_COGS` 列表中添加模組路徑

範例：
```python
from discord.ext import commands

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command()
    async def mycommand(self, ctx):
        await ctx.send("Hello!")

async def setup(bot):
    await bot.add_cog(MyCog(bot))
```

## 🐛 疑難排解

### 機器人無法啟動
- 確認 `.env` 檔案中的 Token 正確
- 確認已安裝所有依賴套件
- 檢查 `logs/bot.log` 查看錯誤訊息

### 斜線指令無法使用
- 確認在 Developer Portal 啟用了所有 Intents
- 等待 Discord 同步指令（可能需要 1-2 小時）
- 重新邀請機器人並確保有 `applications.commands` scope

### 資料庫錯誤
- 刪除 `data/bot_database.db` 讓機器人重新創建
- 確認 `data/` 目錄存在且有寫入權限

## 📝 注意事項

1. **音樂功能**: 需要額外安裝 `yt-dlp` 和 `PyNaCl`，這裡只提供基礎框架
2. **安全性**: 不要將 `.env` 檔案上傳到公開儲存庫
3. **權限**: 確保機器人有足夠的權限執行指令
4. **速率限制**: Discord 有 API 速率限制，避免短時間內大量操作

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

此專案為開源專案，可自由使用和修改。

## 🔗 相關連結

- [Discord.py 文檔](https://discordpy.readthedocs.io/)
- [Discord Developer Portal](https://discord.com/developers/applications)
- [Discord API 文檔](https://discord.com/developers/docs/)

## ✨ 作者

機器人由 GitHub Copilot 協助開發
# DiscordBot
