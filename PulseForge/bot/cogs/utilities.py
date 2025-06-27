import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import platform
import psutil
from bot.database import db
from utils.logger import setup_logger

logger = setup_logger(__name__)

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name="ping")
    async def ping(self, ctx):
        """Check bot latency"""
        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green()
        )
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="Response Time", value="Calculating...", inline=True)
        
        start_time = datetime.utcnow()
        msg = await ctx.send(embed=embed)
        end_time = datetime.utcnow()
        
        response_time = (end_time - start_time).total_seconds() * 1000
        
        embed.set_field_at(1, name="Response Time", value=f"{round(response_time)}ms", inline=True)
        await msg.edit(embed=embed)
    
    @commands.hybrid_command(name="serverinfo")
    async def server_info(self, ctx):
        """Get server information"""
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server!")
            return
        
        guild = ctx.guild
        
        # Calculate member statistics
        total_members = guild.member_count
        online_members = sum(1 for member in guild.members if member.status != discord.Status.offline)
        bot_count = sum(1 for member in guild.members if member.bot)
        human_count = total_members - bot_count
        
        embed = discord.Embed(
            title=f"📊 {guild.name} Server Information",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        # Basic info
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Created", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
        
        # Member statistics
        embed.add_field(name="Total Members", value=f"{total_members:,}", inline=True)
        embed.add_field(name="Humans", value=f"{human_count:,}", inline=True)
        embed.add_field(name="Bots", value=f"{bot_count:,}", inline=True)
        embed.add_field(name="Online", value=f"{online_members:,}", inline=True)
        
        # Server features
        embed.add_field(name="Verification Level", value=guild.verification_level.name.title(), inline=True)
        embed.add_field(name="Boost Level", value=f"Level {guild.premium_tier}", inline=True)
        embed.add_field(name="Boost Count", value=f"{guild.premium_subscription_count}", inline=True)
        
        # Channels and roles
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed.add_field(name="Text Channels", value=text_channels, inline=True)
        embed.add_field(name="Voice Channels", value=voice_channels, inline=True)
        embed.add_field(name="Categories", value=categories, inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Emojis", value=f"{len(guild.emojis)}/{guild.emoji_limit}", inline=True)
        
        # Features
        features = [feature.replace('_', ' ').title() for feature in guild.features]
        if features:
            embed.add_field(name="Features", value="\n".join(features[:10]), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="userinfo")
    @app_commands.describe(member="Member to get information about")
    async def user_info(self, ctx, member: discord.Member = None):
        """Get user information"""
        if not member:
            member = ctx.author
        
        embed = discord.Embed(
            title=f"👤 {member.display_name}",
            color=member.color if member.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Basic info
        embed.add_field(name="Username", value=f"{member.name}#{member.discriminator}", inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Bot", value="✅ Yes" if member.bot else "❌ No", inline=True)
        
        # Dates
        embed.add_field(name="Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        if ctx.guild and member.joined_at:
            embed.add_field(name="Joined", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)
        
        # Status and activity
        embed.add_field(name="Status", value=str(member.status).title(), inline=True)
        
        if member.activity:
            activity_type = member.activity.type.name.title() if hasattr(member.activity, 'type') else "Unknown"
            embed.add_field(name="Activity", value=f"{activity_type}: {member.activity.name}", inline=True)
        
        # Server-specific info
        if ctx.guild:
            # Roles
            roles = [role.mention for role in member.roles[1:]]  # Exclude @everyone
            if roles:
                roles_text = ", ".join(roles) if len(", ".join(roles)) <= 1024 else f"{len(roles)} roles"
                embed.add_field(name=f"Roles ({len(roles)})", value=roles_text, inline=False)
            
            # Permissions
            if member.guild_permissions.administrator:
                embed.add_field(name="Key Permissions", value="Administrator", inline=True)
            else:
                key_perms = []
                perms_to_check = [
                    ("manage_guild", "Manage Server"),
                    ("manage_channels", "Manage Channels"),
                    ("manage_messages", "Manage Messages"),
                    ("kick_members", "Kick Members"),
                    ("ban_members", "Ban Members"),
                    ("manage_roles", "Manage Roles")
                ]
                
                for perm, name in perms_to_check:
                    if getattr(member.guild_permissions, perm):
                        key_perms.append(name)
                
                if key_perms:
                    embed.add_field(name="Key Permissions", value=", ".join(key_perms), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="avatar")
    @app_commands.describe(member="Member to get avatar of")
    async def get_avatar(self, ctx, member: discord.Member = None):
        """Get user's avatar"""
        if not member:
            member = ctx.author
        
        embed = discord.Embed(
            title=f"🖼️ {member.display_name}'s Avatar",
            color=member.color if member.color != discord.Color.default() else discord.Color.blue()
        )
        
        embed.set_image(url=member.display_avatar.url)
        embed.add_field(
            name="Download Links",
            value=f"[PNG]({member.display_avatar.replace(format='png').url}) | "
                  f"[JPG]({member.display_avatar.replace(format='jpg').url}) | "
                  f"[WEBP]({member.display_avatar.replace(format='webp').url})",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="roleinfo")
    @app_commands.describe(role="Role to get information about")
    @commands.has_permissions(manage_roles=True)
    async def role_info(self, ctx, role: discord.Role):
        """Get role information"""
        embed = discord.Embed(
            title=f"🎭 Role: {role.name}",
            color=role.color if role.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Basic info
        embed.add_field(name="ID", value=role.id, inline=True)
        embed.add_field(name="Created", value=f"<t:{int(role.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Position", value=role.position, inline=True)
        embed.add_field(name="Members", value=len(role.members), inline=True)
        embed.add_field(name="Mentionable", value="✅ Yes" if role.mentionable else "❌ No", inline=True)
        embed.add_field(name="Hoisted", value="✅ Yes" if role.hoist else "❌ No", inline=True)
        embed.add_field(name="Managed", value="✅ Yes" if role.managed else "❌ No", inline=True)
        embed.add_field(name="Color", value=str(role.color), inline=True)
        
        # Permissions
        if role.permissions.administrator:
            embed.add_field(name="Permissions", value="Administrator (All Permissions)", inline=False)
        else:
            perms = [perm.replace('_', ' ').title() for perm, value in role.permissions if value]
            if perms:
                perms_text = ", ".join(perms) if len(", ".join(perms)) <= 1024 else f"{len(perms)} permissions"
                embed.add_field(name=f"Permissions ({len(perms)})", value=perms_text, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="botinfo")
    async def info(self, ctx):
        """Get bot information"""
        stats = self.bot.get_stats()
        
        embed = discord.Embed(
            title=f"🤖 {self.bot.user.name} Information",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        # Bot stats
        embed.add_field(name="Servers", value=f"{stats['guilds']:,}", inline=True)
        embed.add_field(name="Users", value=f"{stats['users']:,}", inline=True)
        embed.add_field(name="Commands Used", value=f"{stats['commands_used']:,}", inline=True)
        embed.add_field(name="Uptime", value=stats['uptime'], inline=True)
        embed.add_field(name="Latency", value=f"{stats['latency']}ms", inline=True)
        
        # System info
        embed.add_field(name="Python Version", value=platform.python_version(), inline=True)
        embed.add_field(name="discord.py Version", value=discord.__version__, inline=True)
        
        # Memory usage
        memory = psutil.virtual_memory()
        embed.add_field(
            name="Memory Usage",
            value=f"{memory.percent}% ({memory.used // 1024 // 1024}MB / {memory.total // 1024 // 1024}MB)",
            inline=True
        )
        
        # CPU usage
        cpu_percent = psutil.cpu_percent()
        embed.add_field(name="CPU Usage", value=f"{cpu_percent}%", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="help")
    @app_commands.describe(command="Specific command to get help for")
    async def help_command(self, ctx, command: str = None):
        """Get help for commands"""
        if command:
            # Get specific command help
            cmd = self.bot.get_command(command)
            if not cmd:
                await ctx.send(f"❌ Command `{command}` not found!")
                return
            
            embed = discord.Embed(
                title=f"📖 Help: {cmd.name}",
                description=cmd.help or "No description available",
                color=discord.Color.blue()
            )
            
            if cmd.aliases:
                embed.add_field(name="Aliases", value=", ".join(cmd.aliases), inline=False)
            
            if hasattr(cmd, 'usage') and cmd.usage:
                embed.add_field(name="Usage", value=f"`{ctx.prefix}{cmd.name} {cmd.usage}`", inline=False)
            
            await ctx.send(embed=embed)
        else:
            # General help
            embed = discord.Embed(
                title="📚 PulseForge Bot Commands",
                description="Here are all available commands:",
                color=discord.Color.blue()
            )
            
            # Group commands by cog
            for cog_name, cog in self.bot.cogs.items():
                commands_list = [cmd.name for cmd in cog.get_commands() if not cmd.hidden]
                if commands_list:
                    embed.add_field(
                        name=f"{cog_name}",
                        value=", ".join(commands_list),
                        inline=False
                    )
            
            embed.add_field(
                name="Usage",
                value=f"Use `{ctx.prefix}help <command>` for detailed help on a specific command",
                inline=False
            )
            
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utilities(bot))
