from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, timedelta
from bot.database import db
from utils.logger import setup_logger
import json

logger = setup_logger(__name__)

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@main.route('/dashboard')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@main.route('/api/stats')
def api_stats():
    """Get bot statistics"""
    try:
        # Get command statistics
        command_stats = db.get_command_stats(days=7)
        
        # Get total commands used
        total_commands = sum(stat['usage_count'] for stat in command_stats)
        
        # Get server count (this would come from the bot instance in a real setup)
        # For now, we'll get unique guild_ids from the database
        guild_query = "SELECT COUNT(DISTINCT guild_id) as server_count FROM command_stats"
        server_result = db.execute_query(guild_query)
        server_count = server_result[0]['server_count'] if server_result else 0
        
        stats = {
            'servers': server_count,
            'total_commands': total_commands,
            'commands_today': 0,  # Would need to calculate from today's data
            'uptime': '0h 0m 0s',  # Would come from bot instance
            'status': 'online'
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500

@main.route('/api/command-usage')
def api_command_usage():
    """Get command usage statistics"""
    try:
        days = request.args.get('days', 7, type=int)
        command_stats = db.get_command_stats(days=days)
        
        # Format for chart
        labels = [stat['command_name'] for stat in command_stats[:10]]
        data = [stat['usage_count'] for stat in command_stats[:10]]
        
        return jsonify({
            'labels': labels,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error getting command usage: {e}")
        return jsonify({'error': 'Failed to get command usage'}), 500

@main.route('/api/servers')
def api_servers():
    """Get server list with basic info"""
    try:
        # Get servers from database
        query = """
            SELECT guild_id, COUNT(DISTINCT user_id) as active_users, 
                   COUNT(*) as total_commands
            FROM command_stats 
            WHERE used_at >= datetime('now', '-7 days')
            GROUP BY guild_id
            ORDER BY total_commands DESC
            LIMIT 10
        """
        results = db.execute_query(query)
        
        servers = []
        for result in results:
            servers.append({
                'id': result['guild_id'],
                'name': f"Server {result['guild_id']}",  # Would get real name from bot
                'members': 0,  # Would get from bot
                'active_users': result['active_users'],
                'commands_used': result['total_commands']
            })
        
        return jsonify(servers)
    except Exception as e:
        logger.error(f"Error getting servers: {e}")
        return jsonify({'error': 'Failed to get servers'}), 500

@main.route('/api/recent-activity')
def api_recent_activity():
    """Get recent bot activity"""
    try:
        query = """
            SELECT cs.*, ss.prefix
            FROM command_stats cs
            LEFT JOIN server_settings ss ON cs.guild_id = ss.guild_id
            ORDER BY cs.used_at DESC
            LIMIT 20
        """
        results = db.execute_query(query)
        
        activities = []
        for result in results:
            activities.append({
                'id': result['id'],
                'type': 'command',
                'command': result['command_name'],
                'user_id': result['user_id'],
                'guild_id': result['guild_id'],
                'timestamp': result['used_at']
            })
        
        return jsonify(activities)
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        return jsonify({'error': 'Failed to get recent activity'}), 500

@main.route('/api/warnings/<int:guild_id>')
def api_warnings(guild_id):
    """Get warnings for a specific guild"""
    try:
        warnings = db.get_warnings(guild_id)
        
        formatted_warnings = []
        for warning in warnings:
            formatted_warnings.append({
                'id': warning['id'],
                'user_id': warning['user_id'],
                'moderator_id': warning['moderator_id'],
                'reason': warning['reason'],
                'created_at': warning['created_at']
            })
        
        return jsonify(formatted_warnings)
    except Exception as e:
        logger.error(f"Error getting warnings: {e}")
        return jsonify({'error': 'Failed to get warnings'}), 500

@main.route('/api/music-history/<int:guild_id>')
def api_music_history(guild_id):
    """Get music history for a specific guild"""
    try:
        history = db.get_music_history(guild_id)
        
        formatted_history = []
        for track in history:
            formatted_history.append({
                'id': track['id'],
                'title': track['title'],
                'url': track['url'],
                'duration': track['duration'],
                'user_id': track['user_id'],
                'played_at': track['played_at']
            })
        
        return jsonify(formatted_history)
    except Exception as e:
        logger.error(f"Error getting music history: {e}")
        return jsonify({'error': 'Failed to get music history'}), 500

@main.route('/api/server-settings/<int:guild_id>')
def api_server_settings(guild_id):
    """Get server settings"""
    try:
        settings = db.get_server_settings(guild_id)
        
        if not settings:
            # Return default settings if none exist
            settings = {
                'guild_id': guild_id,
                'prefix': '!',
                'mod_channel_id': None,
                'log_channel_id': None,
                'welcome_channel_id': None,
                'welcome_message': None,
                'auto_role_id': None
            }
        
        return jsonify(settings)
    except Exception as e:
        logger.error(f"Error getting server settings: {e}")
        return jsonify({'error': 'Failed to get server settings'}), 500

@main.route('/api/server-settings/<int:guild_id>', methods=['POST'])
def update_server_settings(guild_id):
    """Update server settings"""
    try:
        data = request.get_json()
        
        # Update settings in database
        allowed_fields = ['prefix', 'mod_channel_id', 'log_channel_id', 
                         'welcome_channel_id', 'welcome_message', 'auto_role_id']
        
        updates = {k: v for k, v in data.items() if k in allowed_fields}
        
        if updates:
            db.update_server_settings(guild_id, **updates)
            return jsonify({'success': True, 'message': 'Settings updated successfully'})
        else:
            return jsonify({'error': 'No valid fields to update'}), 400
            
    except Exception as e:
        logger.error(f"Error updating server settings: {e}")
        return jsonify({'error': 'Failed to update server settings'}), 500

@main.route('/api/system-info')
def api_system_info():
    """Get system information"""
    try:
        import psutil
        import platform
        
        # Get system info
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_info = {
            'platform': platform.system(),
            'python_version': platform.python_version(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used': memory.used // 1024 // 1024,  # MB
            'memory_total': memory.total // 1024 // 1024,  # MB
            'disk_percent': (disk.used / disk.total) * 100,
            'disk_used': disk.used // 1024 // 1024 // 1024,  # GB
            'disk_total': disk.total // 1024 // 1024 // 1024,  # GB
        }
        
        return jsonify(system_info)
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return jsonify({'error': 'Failed to get system information'}), 500
