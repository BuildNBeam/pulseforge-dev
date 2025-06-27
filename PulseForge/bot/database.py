import sqlite3
import asyncio
import threading
from datetime import datetime
from utils.logger import setup_logger
from config import Config

logger = setup_logger(__name__)

class Database:
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self.lock = threading.Lock()
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Server settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS server_settings (
                    guild_id INTEGER PRIMARY KEY,
                    prefix TEXT DEFAULT '!',
                    mod_channel_id INTEGER,
                    log_channel_id INTEGER,
                    welcome_channel_id INTEGER,
                    welcome_message TEXT,
                    auto_role_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # User warnings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    moderator_id INTEGER,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Command usage statistics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS command_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    command_name TEXT,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Music queue history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS music_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    title TEXT,
                    url TEXT,
                    duration INTEGER,
                    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if query.strip().upper().startswith('SELECT'):
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
                else:
                    conn.commit()
                    return cursor.rowcount
            except Exception as e:
                logger.error(f"Database error: {e}")
                conn.rollback()
                raise
            finally:
                conn.close()
    
    def get_server_settings(self, guild_id):
        """Get server settings"""
        query = "SELECT * FROM server_settings WHERE guild_id = ?"
        results = self.execute_query(query, (guild_id,))
        return results[0] if results else None
    
    def update_server_settings(self, guild_id, **settings):
        """Update server settings"""
        if not self.get_server_settings(guild_id):
            # Insert new record
            query = "INSERT INTO server_settings (guild_id) VALUES (?)"
            self.execute_query(query, (guild_id,))
        
        # Update settings
        set_clause = ", ".join([f"{key} = ?" for key in settings.keys()])
        query = f"UPDATE server_settings SET {set_clause} WHERE guild_id = ?"
        params = list(settings.values()) + [guild_id]
        self.execute_query(query, params)
    
    def add_warning(self, guild_id, user_id, moderator_id, reason):
        """Add a warning to the database"""
        query = '''
            INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
            VALUES (?, ?, ?, ?)
        '''
        self.execute_query(query, (guild_id, user_id, moderator_id, reason))
    
    def get_warnings(self, guild_id, user_id=None):
        """Get warnings for a user or all warnings in a guild"""
        if user_id:
            query = "SELECT * FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY created_at DESC"
            return self.execute_query(query, (guild_id, user_id))
        else:
            query = "SELECT * FROM warnings WHERE guild_id = ? ORDER BY created_at DESC LIMIT 50"
            return self.execute_query(query, (guild_id,))
    
    def log_command_usage(self, guild_id, user_id, command_name):
        """Log command usage for statistics"""
        query = '''
            INSERT INTO command_stats (guild_id, user_id, command_name)
            VALUES (?, ?, ?)
        '''
        self.execute_query(query, (guild_id, user_id, command_name))
    
    def get_command_stats(self, guild_id=None, days=7):
        """Get command usage statistics"""
        if guild_id:
            query = '''
                SELECT command_name, COUNT(*) as usage_count
                FROM command_stats
                WHERE guild_id = ? AND used_at >= datetime('now', '-{} days')
                GROUP BY command_name
                ORDER BY usage_count DESC
            '''.format(days)
            return self.execute_query(query, (guild_id,))
        else:
            query = '''
                SELECT command_name, COUNT(*) as usage_count
                FROM command_stats
                WHERE used_at >= datetime('now', '-{} days')
                GROUP BY command_name
                ORDER BY usage_count DESC
            '''.format(days)
            return self.execute_query(query)
    
    def add_music_history(self, guild_id, user_id, title, url, duration=0):
        """Add music play history"""
        query = '''
            INSERT INTO music_history (guild_id, user_id, title, url, duration)
            VALUES (?, ?, ?, ?, ?)
        '''
        self.execute_query(query, (guild_id, user_id, title, url, duration))
    
    def get_music_history(self, guild_id, limit=20):
        """Get music play history"""
        query = '''
            SELECT * FROM music_history
            WHERE guild_id = ?
            ORDER BY played_at DESC
            LIMIT ?
        '''
        return self.execute_query(query, (guild_id, limit))

# Global database instance
db = Database()
