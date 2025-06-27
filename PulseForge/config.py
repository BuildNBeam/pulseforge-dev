import os

class Config:
    # Discord Bot Configuration
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')
    
    # Web Dashboard Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'pulseforge.db')
    
    # Music Configuration
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }
    
    # Rate Limiting
    COMMANDS_PER_MINUTE = int(os.getenv('COMMANDS_PER_MINUTE', '10'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'pulseforge.log')
