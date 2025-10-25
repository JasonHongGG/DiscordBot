"""
JSON 資料管理模組 - 使用 JSON 檔案管理所有資料
"""
import json
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime, timezone
import threading

logger = logging.getLogger(__name__)


class JSONDatabase:
    """JSON 資料庫管理類"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # 資料檔案路徑
        self.files = {
            'warnings': self.data_dir / 'warnings.json',
            'levels': self.data_dir / 'levels.json',
            'economy': self.data_dir / 'economy.json',
            'guild_settings': self.data_dir / 'guild_settings.json',
            'reaction_roles': self.data_dir / 'reaction_roles.json',
            'mutes': self.data_dir / 'mutes.json',
        }
        
        # 執行緒鎖（防止同時寫入）
        self.locks = {key: threading.Lock() for key in self.files.keys()}
        
        # 初始化所有檔案
        self.init_files()
        
        logger.info("JSON 資料庫初始化成功")
    
    def init_files(self):
        """初始化 JSON 檔案"""
        default_data = {
            'warnings': [],
            'levels': {},
            'economy': {},
            'guild_settings': {},
            'reaction_roles': [],
            'mutes': {},
        }
        
        for key, filepath in self.files.items():
            if not filepath.exists():
                self._save_json(filepath, default_data[key])
                logger.info(f"創建資料檔案: {filepath}")
    
    def _load_json(self, filepath: Path) -> Any:
        """載入 JSON 檔案"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"JSON 解析錯誤: {filepath}")
            return [] if filepath.name in ['warnings.json', 'reaction_roles.json'] else {}
        except Exception as e:
            logger.error(f"讀取檔案錯誤 {filepath}: {e}")
            return [] if filepath.name in ['warnings.json', 'reaction_roles.json'] else {}
    
    def _save_json(self, filepath: Path, data: Any):
        """儲存 JSON 檔案"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"儲存檔案錯誤 {filepath}: {e}")
    
    # ==================== 警告系統 ====================
    def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> bool:
        """新增警告"""
        with self.locks['warnings']:
            warnings = self._load_json(self.files['warnings'])
            warning = {
                'id': len(warnings) + 1,
                'guild_id': guild_id,
                'user_id': user_id,
                'moderator_id': moderator_id,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }
            warnings.append(warning)
            self._save_json(self.files['warnings'], warnings)
            return True
    
    def get_warnings(self, guild_id: int, user_id: int) -> List[Dict]:
        """獲取用戶警告"""
        warnings = self._load_json(self.files['warnings'])
        return [w for w in warnings if w['guild_id'] == guild_id and w['user_id'] == user_id]
    
    def count_warnings(self, guild_id: int, user_id: int) -> int:
        """計算警告次數"""
        return len(self.get_warnings(guild_id, user_id))
    
    def clear_warnings(self, guild_id: int, user_id: int) -> bool:
        """清除用戶警告"""
        with self.locks['warnings']:
            warnings = self._load_json(self.files['warnings'])
            warnings = [w for w in warnings if not (w['guild_id'] == guild_id and w['user_id'] == user_id)]
            self._save_json(self.files['warnings'], warnings)
            return True
    
    # ==================== 等級系統 ====================
    def get_level_data(self, guild_id: int, user_id: int) -> Optional[Dict]:
        """獲取等級資料"""
        levels = self._load_json(self.files['levels'])
        key = f"{guild_id}_{user_id}"
        return levels.get(key)
    
    def set_level_data(self, guild_id: int, user_id: int, xp: int, level: int, last_xp_time: str = None):
        """設定等級資料"""
        with self.locks['levels']:
            levels = self._load_json(self.files['levels'])
            key = f"{guild_id}_{user_id}"
            levels[key] = {
                'user_id': user_id,
                'guild_id': guild_id,
                'xp': xp,
                'level': level,
                'last_xp_time': last_xp_time
            }
            self._save_json(self.files['levels'], levels)
    
    def get_top_levels(self, guild_id: int, limit: int = 10) -> List[Dict]:
        """獲取等級排行榜"""
        levels = self._load_json(self.files['levels'])
        guild_levels = [v for v in levels.values() if v['guild_id'] == guild_id]
        return sorted(guild_levels, key=lambda x: x['xp'], reverse=True)[:limit]
    
    def delete_all_levels(self, guild_id: int):
        """刪除伺服器所有等級資料"""
        with self.locks['levels']:
            levels = self._load_json(self.files['levels'])
            levels = {k: v for k, v in levels.items() if v['guild_id'] != guild_id}
            self._save_json(self.files['levels'], levels)
    
    # ==================== 經濟系統 ====================
    def get_economy_data(self, guild_id: int, user_id: int) -> Dict:
        """獲取經濟資料"""
        economy = self._load_json(self.files['economy'])
        key = f"{guild_id}_{user_id}"
        return economy.get(key, {
            'user_id': user_id,
            'guild_id': guild_id,
            'balance': 0,
            'bank': 0,
            'last_daily': None,
            'last_work': None
        })
    
    def set_economy_data(self, guild_id: int, user_id: int, balance: int = None, 
                        bank: int = None, last_daily: str = None, last_work: str = None):
        """設定經濟資料"""
        with self.locks['economy']:
            economy = self._load_json(self.files['economy'])
            key = f"{guild_id}_{user_id}"
            
            if key not in economy:
                economy[key] = {
                    'user_id': user_id,
                    'guild_id': guild_id,
                    'balance': 0,
                    'bank': 0,
                    'last_daily': None,
                    'last_work': None
                }
            
            if balance is not None:
                economy[key]['balance'] = balance
            if bank is not None:
                economy[key]['bank'] = bank
            if last_daily is not None:
                economy[key]['last_daily'] = last_daily
            if last_work is not None:
                economy[key]['last_work'] = last_work
            
            self._save_json(self.files['economy'], economy)
    
    def get_top_economy(self, guild_id: int, limit: int = 10) -> List[Dict]:
        """獲取財富排行榜"""
        economy = self._load_json(self.files['economy'])
        guild_economy = [v for v in economy.values() if v['guild_id'] == guild_id]
        return sorted(guild_economy, key=lambda x: x['balance'] + x['bank'], reverse=True)[:limit]
    
    # ==================== 伺服器設定 ====================
    def get_guild_settings(self, guild_id: int) -> Dict:
        """獲取伺服器設定"""
        settings = self._load_json(self.files['guild_settings'])
        return settings.get(str(guild_id), {
            'guild_id': guild_id,
            'welcome_channel_id': None,
            'farewell_channel_id': None,
            'log_channel_id': None,
            'muted_role_id': None,
            'autorole_id': None,
            'level_up_message': True,
            'automod_enabled': False
        })
    
    def set_guild_settings(self, guild_id: int, **kwargs):
        """設定伺服器設定"""
        with self.locks['guild_settings']:
            settings = self._load_json(self.files['guild_settings'])
            key = str(guild_id)
            
            if key not in settings:
                settings[key] = {
                    'guild_id': guild_id,
                    'welcome_channel_id': None,
                    'farewell_channel_id': None,
                    'log_channel_id': None,
                    'muted_role_id': None,
                    'autorole_id': None,
                    'level_up_message': True,
                    'automod_enabled': False
                }
            
            settings[key].update(kwargs)
            self._save_json(self.files['guild_settings'], settings)
    
    # ==================== 反應角色 ====================
    def add_reaction_role(self, guild_id: int, message_id: int, role_id: int, emoji: str):
        """新增反應角色"""
        with self.locks['reaction_roles']:
            reaction_roles = self._load_json(self.files['reaction_roles'])
            reaction_role = {
                'id': len(reaction_roles) + 1,
                'guild_id': guild_id,
                'message_id': message_id,
                'role_id': role_id,
                'emoji': emoji
            }
            reaction_roles.append(reaction_role)
            self._save_json(self.files['reaction_roles'], reaction_roles)
    
    def get_reaction_role(self, guild_id: int, message_id: int, emoji: str) -> Optional[Dict]:
        """獲取反應角色"""
        reaction_roles = self._load_json(self.files['reaction_roles'])
        for rr in reaction_roles:
            if rr['guild_id'] == guild_id and rr['message_id'] == message_id and rr['emoji'] == emoji:
                return rr
        return None
    
    def get_all_reaction_roles(self, guild_id: int) -> List[Dict]:
        """獲取所有反應角色"""
        reaction_roles = self._load_json(self.files['reaction_roles'])
        return [rr for rr in reaction_roles if rr['guild_id'] == guild_id]
    
    def remove_reaction_role(self, guild_id: int, message_id: int, emoji: str):
        """移除反應角色"""
        with self.locks['reaction_roles']:
            reaction_roles = self._load_json(self.files['reaction_roles'])
            reaction_roles = [
                rr for rr in reaction_roles 
                if not (rr['guild_id'] == guild_id and rr['message_id'] == message_id and rr['emoji'] == emoji)
            ]
            self._save_json(self.files['reaction_roles'], reaction_roles)
    
    # ==================== 靜音記錄 ====================
    def set_mute(self, guild_id: int, user_id: int, muted_until: str, reason: str):
        """設定靜音記錄"""
        with self.locks['mutes']:
            mutes = self._load_json(self.files['mutes'])
            key = f"{guild_id}_{user_id}"
            mutes[key] = {
                'user_id': user_id,
                'guild_id': guild_id,
                'muted_until': muted_until,
                'reason': reason
            }
            self._save_json(self.files['mutes'], mutes)
    
    def remove_mute(self, guild_id: int, user_id: int):
        """移除靜音記錄"""
        with self.locks['mutes']:
            mutes = self._load_json(self.files['mutes'])
            key = f"{guild_id}_{user_id}"
            if key in mutes:
                del mutes[key]
                self._save_json(self.files['mutes'], mutes)


# 全局資料庫實例
db = JSONDatabase()
