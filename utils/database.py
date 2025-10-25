"""
資料庫管理模組 - 處理所有資料庫操作
"""
import sqlite3
import logging
from typing import Optional, List, Tuple, Any
from config import DATABASE_PATH

logger = logging.getLogger(__name__)


class Database:
    """資料庫管理類"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """獲取資料庫連接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """初始化資料庫表格"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 警告系統表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    reason TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 等級系統表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS levels (
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 0,
                    last_xp_time DATETIME,
                    PRIMARY KEY (user_id, guild_id)
                )
            """)
            
            # 經濟系統表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS economy (
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    balance INTEGER DEFAULT 0,
                    bank INTEGER DEFAULT 0,
                    last_daily DATETIME,
                    last_work DATETIME,
                    PRIMARY KEY (user_id, guild_id)
                )
            """)
            
            # 伺服器設定表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    welcome_channel_id INTEGER,
                    farewell_channel_id INTEGER,
                    log_channel_id INTEGER,
                    muted_role_id INTEGER,
                    autorole_id INTEGER,
                    level_up_message BOOLEAN DEFAULT 1,
                    automod_enabled BOOLEAN DEFAULT 0
                )
            """)
            
            # 反應角色表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reaction_roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    emoji TEXT NOT NULL
                )
            """)
            
            # 自訂指令表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS custom_commands (
                    guild_id INTEGER NOT NULL,
                    command_name TEXT NOT NULL,
                    response TEXT NOT NULL,
                    created_by INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, command_name)
                )
            """)
            
            # 靜音記錄表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mutes (
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    muted_until DATETIME,
                    reason TEXT,
                    PRIMARY KEY (user_id, guild_id)
                )
            """)
            
            conn.commit()
            logger.info("資料庫初始化成功")
        except Exception as e:
            logger.error(f"資料庫初始化失敗: {e}")
        finally:
            conn.close()
    
    def execute(self, query: str, params: Tuple = ()) -> Optional[List[sqlite3.Row]]:
        """執行 SQL 查詢"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"SQL 執行錯誤: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> bool:
        """批量執行 SQL"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.executemany(query, params_list)
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"批量 SQL 執行錯誤: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()


# 全局資料庫實例
db = Database()
