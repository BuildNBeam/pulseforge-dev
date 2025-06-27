import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import yt_dlp
from collections import deque
from bot.database import db
from utils.logger import setup_logger
from config import Config

logger = setup_logger(__name__)

class YTDLSource:
    """YouTube-DL source for music playback"""
    
    ytdl_format_options = {
        'format': 'bestaudio/best',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0'
    }
    
    ytdl = yt_dlp.YoutubeDL(ytdl_format_options)
    
    @classmethod
    async def from_url(cls, url, *, loop=None):
        """Create source from URL"""
        loop = loop or asyncio.get_event_loop()
        
        try:
            data = await loop.run_in_executor(None, lambda: cls.ytdl.extract_info(url, download=False))
            
            if data is None:
                return None
            
            if isinstance(data, dict) and 'entries' in data and data['entries']:
                data = data['entries'][0]
            
            if not isinstance(data, dict):
                return None
            
            return {
                'url': data.get('url', ''),
                'title': data.get('title', 'Unknown'),
                'duration': data.get('duration', 0),
                'webpage_url': data.get('webpage_url', ''),
                'thumbnail': data.get('thumbnail')
            }
        except Exception as e:
            logger.error(f"Error extracting audio info: {e}")
            return None

class MusicPlayer:
    """Music player for a guild"""
    
    def __init__(self, bot, guild_id):
        self.bot = bot
        self.guild_id = guild_id
        self.queue = deque()
        self.current = None
        self.voice_client = None
        self.volume = 0.5
        self.loop = False
        
    def add_to_queue(self, track):
        """Add track to queue"""
        self.queue.append(track)
    
    def remove_from_queue(self, index):
        """Remove track from queue by index"""
        if 0 <= index < len(self.queue):
            queue_list = list(self.queue)
            removed = queue_list.pop(index)
            self.queue = deque(queue_list)
            return removed
        return None
    
    def clear_queue(self):
        """Clear the queue"""
        self.queue.clear()
    
    def shuffle_queue(self):
        """Shuffle the queue"""
        import random
        queue_list = list(self.queue)
        random.shuffle(queue_list)
        self.queue = deque(queue_list)
    
    async def play_next(self):
        """Play next song in queue"""
        if not self.queue and not self.loop:
            return
        
        if self.queue:
            self.current = self.queue.popleft()
        elif self.loop and self.current:
            pass  # Keep current song for looping
        
        if self.current and self.voice_client:
            try:
                source = discord.FFmpegPCMAudio(
                    self.current['url'],
                    before_options=Config.FFMPEG_OPTIONS['before_options'],
                    options=Config.FFMPEG_OPTIONS['options']
                )
                
                # Apply volume
                source = discord.PCMVolumeTransformer(source, volume=self.volume)
                
                def after_playing(error):
                    if error:
                        logger.error(f"Player error: {error}")
                    else:
                        # Add to history
                        if self.current:
                            db.add_music_history(
                                self.guild_id,
                                self.current.get('requester_id', 0),
                                self.current.get('title', 'Unknown'),
                                self.current.get('webpage_url', ''),
                                self.current.get('duration', 0)
                            )
                    
                    coro = self.play_next()
                    fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                    try:
                        fut.result()
                    except Exception as e:
                        logger.error(f"Error in after_playing: {e}")
                
                self.voice_client.play(source, after=after_playing)
                
            except Exception as e:
                logger.error(f"Error playing track: {e}")

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}
    
    def get_player(self, guild_id):
        """Get or create music player for guild"""
        if guild_id not in self.players:
            self.players[guild_id] = MusicPlayer(self.bot, guild_id)
        return self.players[guild_id]
    
    @commands.hybrid_command(name="join")
    @app_commands.describe(channel="Voice channel to join")
    async def join_voice(self, ctx, channel: discord.VoiceChannel = None):
        """Join a voice channel"""
        if not channel:
            if ctx.author.voice:
                channel = ctx.author.voice.channel
            else:
                await ctx.send("❌ You must be in a voice channel or specify one!")
                return
        
        if ctx.guild.voice_client:
            if ctx.guild.voice_client.channel == channel:
                await ctx.send("✅ Already connected to this channel!")
                return
            else:
                await ctx.guild.voice_client.move_to(channel)
        else:
            await channel.connect()
        
        player = self.get_player(ctx.guild.id)
        player.voice_client = ctx.guild.voice_client
        
        embed = discord.Embed(
            title="🎵 Joined Voice Channel",
            description=f"Connected to {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="leave")
    async def leave_voice(self, ctx):
        """Leave the voice channel"""
        if not ctx.guild.voice_client:
            await ctx.send("❌ I'm not connected to any voice channel!")
            return
        
        player = self.get_player(ctx.guild.id)
        player.queue.clear()
        player.current = None
        
        await ctx.guild.voice_client.disconnect()
        
        embed = discord.Embed(
            title="👋 Left Voice Channel",
            description="Disconnected from voice channel",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="play")
    @app_commands.describe(query="Song to play (URL or search query)")
    async def play_music(self, ctx, *, query: str):
        """Play music from YouTube"""
        if not ctx.author.voice:
            await ctx.send("❌ You must be in a voice channel to play music!")
            return
        
        # Join voice channel if not connected
        if not ctx.guild.voice_client:
            await ctx.author.voice.channel.connect()
        
        player = self.get_player(ctx.guild.id)
        player.voice_client = ctx.guild.voice_client
        
        # Show loading message
        loading_msg = await ctx.send("🔍 Searching for music...")
        
        # Extract track info
        track_info = await YTDLSource.from_url(query)
        
        if not track_info:
            await loading_msg.edit(content="❌ Could not find or extract audio from the provided query.")
            return
        
        # Add requester info
        track_info['requester'] = ctx.author
        track_info['requester_id'] = ctx.author.id
        
        # Add to queue
        player.add_to_queue(track_info)
        
        embed = discord.Embed(
            title="🎵 Added to Queue",
            description=f"**[{track_info['title']}]({track_info['webpage_url']})**",
            color=discord.Color.blue()
        )
        embed.add_field(name="Requested by", value=ctx.author.mention, inline=True)
        embed.add_field(name="Position in queue", value=str(len(player.queue)), inline=True)
        
        if track_info.get('duration'):
            minutes, seconds = divmod(track_info['duration'], 60)
            embed.add_field(name="Duration", value=f"{minutes}:{seconds:02d}", inline=True)
        
        if track_info.get('thumbnail'):
            embed.set_thumbnail(url=track_info['thumbnail'])
        
        await loading_msg.edit(content="", embed=embed)
        
        # Start playing if nothing is currently playing
        if not player.voice_client.is_playing():
            await player.play_next()
    
    @commands.hybrid_command(name="pause")
    async def pause_music(self, ctx):
        """Pause the current song"""
        if not ctx.guild.voice_client or not ctx.guild.voice_client.is_playing():
            await ctx.send("❌ Nothing is currently playing!")
            return
        
        ctx.guild.voice_client.pause()
        
        embed = discord.Embed(
            title="⏸️ Music Paused",
            description="The current song has been paused",
            color=discord.Color.yellow()
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="resume")
    async def resume_music(self, ctx):
        """Resume the current song"""
        if not ctx.guild.voice_client or not ctx.guild.voice_client.is_paused():
            await ctx.send("❌ Nothing is currently paused!")
            return
        
        ctx.guild.voice_client.resume()
        
        embed = discord.Embed(
            title="▶️ Music Resumed",
            description="The current song has been resumed",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="skip")
    async def skip_music(self, ctx):
        """Skip the current song"""
        if not ctx.guild.voice_client or not ctx.guild.voice_client.is_playing():
            await ctx.send("❌ Nothing is currently playing!")
            return
        
        ctx.guild.voice_client.stop()
        
        embed = discord.Embed(
            title="⏭️ Song Skipped",
            description="Skipped to the next song",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="queue")
    async def show_queue(self, ctx):
        """Show the music queue"""
        player = self.get_player(ctx.guild.id)
        
        if not player.current and not player.queue:
            await ctx.send("❌ The queue is empty!")
            return
        
        embed = discord.Embed(
            title="🎵 Music Queue",
            color=discord.Color.blue()
        )
        
        # Current song
        if player.current:
            embed.add_field(
                name="Now Playing",
                value=f"**[{player.current['title']}]({player.current['webpage_url']})**\nRequested by: {player.current.get('requester', 'Unknown')}",
                inline=False
            )
        
        # Queue
        if player.queue:
            queue_text = ""
            for i, track in enumerate(list(player.queue)[:10]):  # Show first 10
                queue_text += f"{i+1}. **[{track['title']}]({track['webpage_url']})**\n"
            
            embed.add_field(
                name=f"Up Next ({len(player.queue)} songs)",
                value=queue_text,
                inline=False
            )
            
            if len(player.queue) > 10:
                embed.add_field(
                    name="",
                    value=f"... and {len(player.queue) - 10} more songs",
                    inline=False
                )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="volume")
    @app_commands.describe(volume="Volume level (0-100)")
    async def set_volume(self, ctx, volume: int):
        """Set the music volume"""
        if not 0 <= volume <= 100:
            await ctx.send("❌ Volume must be between 0 and 100!")
            return
        
        player = self.get_player(ctx.guild.id)
        player.volume = volume / 100.0
        
        if ctx.guild.voice_client and ctx.guild.voice_client.source:
            ctx.guild.voice_client.source.volume = player.volume
        
        embed = discord.Embed(
            title="🔊 Volume Changed",
            description=f"Volume set to {volume}%",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="nowplaying")
    async def now_playing(self, ctx):
        """Show currently playing song"""
        player = self.get_player(ctx.guild.id)
        
        if not player.current:
            await ctx.send("❌ Nothing is currently playing!")
            return
        
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**[{player.current['title']}]({player.current['webpage_url']})**",
            color=discord.Color.blue()
        )
        embed.add_field(name="Requested by", value=player.current.get('requester', 'Unknown'), inline=True)
        embed.add_field(name="Volume", value=f"{int(player.volume * 100)}%", inline=True)
        embed.add_field(name="Loop", value="✅ Enabled" if player.loop else "❌ Disabled", inline=True)
        
        if player.current.get('duration'):
            minutes, seconds = divmod(player.current['duration'], 60)
            embed.add_field(name="Duration", value=f"{minutes}:{seconds:02d}", inline=True)
        
        if player.current.get('thumbnail'):
            embed.set_thumbnail(url=player.current['thumbnail'])
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="clearqueue")
    async def clear_queue(self, ctx):
        """Clear the music queue"""
        player = self.get_player(ctx.guild.id)
        player.clear_queue()
        
        embed = discord.Embed(
            title="🗑️ Queue Cleared",
            description="The music queue has been cleared",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))
