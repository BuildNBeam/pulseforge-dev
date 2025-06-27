import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from bot.database import db
from utils.logger import setup_logger

logger = setup_logger(__name__)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_check(self, ctx):
        """Check if user has moderation permissions"""
        if not ctx.guild:
            return False
        return ctx.author.guild_permissions.manage_messages
    
    @commands.hybrid_command(name="ban")
    @app_commands.describe(
        member="Member to ban",
        reason="Reason for ban",
        delete_days="Days of messages to delete (0-7)"
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_member(self, ctx, member: discord.Member, delete_days: int = 1, *, reason: str = "No reason provided"):
        """Ban a member from the server"""
        if member == ctx.author:
            await ctx.send("❌ You cannot ban yourself!")
            return
        
        if member.top_role >= ctx.author.top_role:
            await ctx.send("❌ You cannot ban someone with equal or higher role!")
            return
        
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send("❌ I cannot ban someone with equal or higher role than me!")
            return
        
        # Clamp delete_days between 0 and 7
        delete_days = max(0, min(7, delete_days))
        
        try:
            # Send DM before banning
            try:
                embed = discord.Embed(
                    title="🔨 You have been banned",
                    description=f"**Server:** {ctx.guild.name}\n**Reason:** {reason}",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                await member.send(embed=embed)
            except:
                pass  # Ignore if DM fails
            
            # Ban the member
            await member.ban(reason=f"{ctx.author}: {reason}", delete_message_days=delete_days)
            
            # Log the ban
            embed = discord.Embed(
                title="🔨 Member Banned",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Moderator", value=f"{ctx.author} ({ctx.author.id})", inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Messages Deleted", value=f"{delete_days} days", inline=True)
            
            await ctx.send(embed=embed)
            
            # Log to moderation channel if set
            settings = db.get_server_settings(ctx.guild.id)
            if settings and settings.get('mod_channel_id'):
                mod_channel = self.bot.get_channel(settings['mod_channel_id'])
                if mod_channel:
                    await mod_channel.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to ban this member!")
        except Exception as e:
            logger.error(f"Ban command error: {e}")
            await ctx.send("❌ An error occurred while banning the member.")
    
    @commands.hybrid_command(name="kick")
    @app_commands.describe(member="Member to kick", reason="Reason for kick")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick_member(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member from the server"""
        if member == ctx.author:
            await ctx.send("❌ You cannot kick yourself!")
            return
        
        if member.top_role >= ctx.author.top_role:
            await ctx.send("❌ You cannot kick someone with equal or higher role!")
            return
        
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send("❌ I cannot kick someone with equal or higher role than me!")
            return
        
        try:
            # Send DM before kicking
            try:
                embed = discord.Embed(
                    title="👢 You have been kicked",
                    description=f"**Server:** {ctx.guild.name}\n**Reason:** {reason}",
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow()
                )
                await member.send(embed=embed)
            except:
                pass
            
            # Kick the member
            await member.kick(reason=f"{ctx.author}: {reason}")
            
            # Log the kick
            embed = discord.Embed(
                title="👢 Member Kicked",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Moderator", value=f"{ctx.author} ({ctx.author.id})", inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to kick this member!")
        except Exception as e:
            logger.error(f"Kick command error: {e}")
            await ctx.send("❌ An error occurred while kicking the member.")
    
    @commands.hybrid_command(name="mute")
    @app_commands.describe(
        member="Member to mute",
        duration="Duration in minutes",
        reason="Reason for mute"
    )
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def mute_member(self, ctx, member: discord.Member, duration: int = 60, *, reason: str = "No reason provided"):
        """Mute a member for a specified duration"""
        if member == ctx.author:
            await ctx.send("❌ You cannot mute yourself!")
            return
        
        if member.top_role >= ctx.author.top_role:
            await ctx.send("❌ You cannot mute someone with equal or higher role!")
            return
        
        # Convert duration to timedelta
        mute_duration = timedelta(minutes=duration)
        until = datetime.utcnow() + mute_duration
        
        try:
            # Timeout the member
            await member.timeout(until, reason=f"{ctx.author}: {reason}")
            
            embed = discord.Embed(
                title="🔇 Member Muted",
                color=discord.Color.yellow(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Moderator", value=f"{ctx.author} ({ctx.author.id})", inline=False)
            embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
            embed.add_field(name="Until", value=f"<t:{int(until.timestamp())}:R>", inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to mute this member!")
        except Exception as e:
            logger.error(f"Mute command error: {e}")
            await ctx.send("❌ An error occurred while muting the member.")
    
    @commands.hybrid_command(name="unmute")
    @app_commands.describe(member="Member to unmute")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def unmute_member(self, ctx, member: discord.Member):
        """Unmute a member"""
        try:
            await member.timeout(None, reason=f"Unmuted by {ctx.author}")
            
            embed = discord.Embed(
                title="🔊 Member Unmuted",
                description=f"{member.mention} has been unmuted by {ctx.author.mention}",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to unmute this member!")
        except Exception as e:
            logger.error(f"Unmute command error: {e}")
            await ctx.send("❌ An error occurred while unmuting the member.")
    
    @commands.hybrid_command(name="warn")
    @app_commands.describe(member="Member to warn", reason="Reason for warning")
    @commands.has_permissions(manage_messages=True)
    async def warn_member(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Warn a member"""
        if member == ctx.author:
            await ctx.send("❌ You cannot warn yourself!")
            return
        
        # Add warning to database
        db.add_warning(ctx.guild.id, member.id, ctx.author.id, reason)
        
        # Get warning count
        warnings = db.get_warnings(ctx.guild.id, member.id)
        warning_count = len(warnings)
        
        embed = discord.Embed(
            title="⚠️ Member Warned",
            color=discord.Color.yellow(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Moderator", value=f"{ctx.author} ({ctx.author.id})", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Total Warnings", value=f"{warning_count}", inline=True)
        
        await ctx.send(embed=embed)
        
        # Send DM to member
        try:
            dm_embed = discord.Embed(
                title="⚠️ You have been warned",
                description=f"**Server:** {ctx.guild.name}\n**Reason:** {reason}",
                color=discord.Color.yellow(),
                timestamp=datetime.utcnow()
            )
            dm_embed.add_field(name="Total Warnings", value=f"{warning_count}", inline=True)
            await member.send(embed=dm_embed)
        except:
            pass
    
    @commands.hybrid_command(name="warnings")
    @app_commands.describe(member="Member to check warnings for")
    @commands.has_permissions(manage_messages=True)
    async def check_warnings(self, ctx, member: discord.Member = None):
        """Check warnings for a member"""
        if not member:
            member = ctx.author
        
        warnings = db.get_warnings(ctx.guild.id, member.id)
        
        if not warnings:
            await ctx.send(f"✅ {member.mention} has no warnings.")
            return
        
        embed = discord.Embed(
            title=f"⚠️ Warnings for {member.display_name}",
            color=discord.Color.yellow(),
            timestamp=datetime.utcnow()
        )
        
        for i, warning in enumerate(warnings[:10]):  # Show last 10 warnings
            moderator = self.bot.get_user(warning['moderator_id'])
            mod_name = moderator.display_name if moderator else "Unknown"
            
            embed.add_field(
                name=f"Warning {i+1}",
                value=f"**Reason:** {warning['reason']}\n**Moderator:** {mod_name}\n**Date:** <t:{int(datetime.fromisoformat(warning['created_at']).timestamp())}:R>",
                inline=False
            )
        
        embed.set_footer(text=f"Total warnings: {len(warnings)}")
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="clear")
    @app_commands.describe(amount="Number of messages to delete")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clear_messages(self, ctx, amount: int):
        """Clear a specified number of messages"""
        if amount <= 0 or amount > 100:
            await ctx.send("❌ Amount must be between 1 and 100!")
            return
        
        try:
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 for the command message
            
            embed = discord.Embed(
                title="🧹 Messages Cleared",
                description=f"Deleted {len(deleted)-1} messages",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Channel", value=ctx.channel.mention, inline=True)
            
            # Send confirmation message that deletes itself
            msg = await ctx.send(embed=embed, delete_after=5)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to delete messages!")
        except Exception as e:
            logger.error(f"Clear command error: {e}")
            await ctx.send("❌ An error occurred while clearing messages.")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
