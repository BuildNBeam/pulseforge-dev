import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from bot.database import db
from utils.logger import setup_logger
from config import Config

logger = setup_logger(__name__)

class PulseForgeBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        # intents.message_content = True  # Privileged intent - disabled for now
        intents.voice_states = True
        intents.guilds = True
        # intents.members = True  # Privileged intent - disabled for now
        
        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            help_command=None
        )
        
        # Rate limiting
        self.command_cooldowns = defaultdict(lambda: defaultdict(list))
        
        # Bot statistics
        self.start_time = None
        self.commands_used = 0
        
        # Load cogs
        self.load_cogs()
    
    async def get_prefix(self, message):
        """Get command prefix for guild"""
        if not message.guild:
            return Config.COMMAND_PREFIX
        
        settings = db.get_server_settings(message.guild.id)
        if settings:
            return settings.get('prefix', Config.COMMAND_PREFIX)
        return Config.COMMAND_PREFIX
    
    def load_cogs(self):
        """Load all bot cogs"""
        cogs = [
            'bot.cogs.moderation',
            'bot.cogs.music',
            'bot.cogs.utilities',
            'bot.cogs.gaming'
        ]
        
        for cog in cogs:
            try:
                asyncio.create_task(self.load_extension(cog))
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")
    
    async def on_ready(self):
        """Bot ready event"""
        self.start_time = datetime.utcnow()
        logger.info(f"{self.user} has connected to Discord!")
        logger.info(f"Bot is in {len(self.guilds)} guilds")
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="over the server | /help"
            )
        )
    
    async def on_guild_join(self, guild):
        """Bot joined a new guild"""
        logger.info(f"Joined guild: {guild.name} ({guild.id})")
        
        # Initialize server settings
        db.update_server_settings(guild.id, prefix=Config.COMMAND_PREFIX)
    
    async def on_guild_remove(self, guild):
        """Bot left a guild"""
        logger.info(f"Left guild: {guild.name} ({guild.id})")
    
    async def on_command(self, ctx):
        """Command used event"""
        self.commands_used += 1
        
        # Log command usage
        if ctx.guild:
            db.log_command_usage(ctx.guild.id, ctx.author.id, ctx.command.name)
        
        logger.info(f"Command used: {ctx.command.name} by {ctx.author} in {ctx.guild}")
    
    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
            return
        
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: `{error.param.name}`")
            return
        
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command on cooldown. Try again in {error.retry_after:.1f}s")
            return
        
        logger.error(f"Command error in {ctx.command}: {error}")
        await ctx.send("❌ An error occurred while processing the command.")
    
    def check_rate_limit(self, user_id, guild_id=None):
        """Check if user is rate limited"""
        now = datetime.utcnow()
        key = f"{user_id}_{guild_id}" if guild_id else str(user_id)
        
        # Clean old entries
        self.command_cooldowns[key] = [
            timestamp for timestamp in self.command_cooldowns[key]
            if now - timestamp < timedelta(minutes=1)
        ]
        
        # Check rate limit
        if len(self.command_cooldowns[key]) >= Config.COMMANDS_PER_MINUTE:
            return False
        
        # Add current timestamp
        self.command_cooldowns[key].append(now)
        return True
    
    def get_uptime(self):
        """Get bot uptime"""
        if not self.start_time:
            return "Not started"
        
        uptime = datetime.utcnow() - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{hours}h {minutes}m {seconds}s"
    
    def get_stats(self):
        """Get bot statistics"""
        return {
            'guilds': len(self.guilds),
            'users': sum(guild.member_count for guild in self.guilds),
            'commands_used': self.commands_used,
            'uptime': self.get_uptime(),
            'latency': round(self.latency * 1000, 2)
        }
