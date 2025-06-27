from flask_socketio import emit, disconnect
from datetime import datetime
import threading
import time
from utils.logger import setup_logger
from bot.database import db

logger = setup_logger(__name__)

# Store active connections
active_connections = set()

def register_socketio_events(socketio):
    """Register SocketIO event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        from flask import request
        active_connections.add(request.sid)
        logger.info(f"Client connected: {request.sid}")
        emit('status', {'message': 'Connected to PulseForge Dashboard'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        from flask import request
        active_connections.discard(request.sid)
        logger.info(f"Client disconnected: {request.sid}")
    
    @socketio.on('join_room')
    def handle_join_room(data):
        """Handle joining a room (e.g., for server-specific updates)"""
        from flask_socketio import join_room
        room = data.get('room')
        if room:
            join_room(room)
            emit('status', {'message': f'Joined room: {room}'})
    
    @socketio.on('leave_room')
    def handle_leave_room(data):
        """Handle leaving a room"""
        from flask_socketio import leave_room
        room = data.get('room')
        if room:
            leave_room(room)
            emit('status', {'message': f'Left room: {room}'})
    
    @socketio.on('request_stats')
    def handle_request_stats():
        """Handle request for current stats"""
        try:
            # Get basic stats
            command_stats = db.get_command_stats(days=1)
            total_commands_today = sum(stat['usage_count'] for stat in command_stats)
            
            stats = {
                'timestamp': datetime.utcnow().isoformat(),
                'servers': 0,  # Would come from bot instance
                'users': 0,   # Would come from bot instance
                'commands_today': total_commands_today,
                'uptime': '0h 0m 0s',  # Would come from bot instance
                'status': 'online'
            }
            
            emit('stats_update', stats)
        except Exception as e:
            logger.error(f"Error sending stats: {e}")
            emit('error', {'message': 'Failed to get statistics'})
    
    @socketio.on('request_activity')
    def handle_request_activity():
        """Handle request for recent activity"""
        try:
            query = """
                SELECT command_name, guild_id, user_id, used_at
                FROM command_stats
                ORDER BY used_at DESC
                LIMIT 10
            """
            results = db.execute_query(query)
            
            activities = []
            for result in results:
                activities.append({
                    'type': 'command',
                    'command': result['command_name'],
                    'guild_id': result['guild_id'],
                    'user_id': result['user_id'],
                    'timestamp': result['used_at']
                })
            
            emit('activity_update', {'activities': activities})
        except Exception as e:
            logger.error(f"Error sending activity: {e}")
            emit('error', {'message': 'Failed to get recent activity'})

def broadcast_command_used(command_name, guild_id, user_id):
    """Broadcast when a command is used"""
    if not active_connections:
        return
    
    try:
        from web.app import socketio
        
        activity = {
            'type': 'command',
            'command': command_name,
            'guild_id': guild_id,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        socketio.emit('new_activity', activity)
        logger.debug(f"Broadcasted command usage: {command_name}")
    except Exception as e:
        logger.error(f"Error broadcasting command usage: {e}")

def broadcast_member_joined(guild_id, user_id):
    """Broadcast when a member joins a server"""
    if not active_connections:
        return
    
    try:
        from web.app import socketio
        
        activity = {
            'type': 'member_join',
            'guild_id': guild_id,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        socketio.emit('new_activity', activity)
        logger.debug(f"Broadcasted member join: {user_id}")
    except Exception as e:
        logger.error(f"Error broadcasting member join: {e}")

def broadcast_member_left(guild_id, user_id):
    """Broadcast when a member leaves a server"""
    if not active_connections:
        return
    
    try:
        from web.app import socketio
        
        activity = {
            'type': 'member_leave',
            'guild_id': guild_id,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        socketio.emit('new_activity', activity)
        logger.debug(f"Broadcasted member leave: {user_id}")
    except Exception as e:
        logger.error(f"Error broadcasting member leave: {e}")

def start_stats_broadcaster(socketio):
    """Start background thread to broadcast stats periodically"""
    def broadcast_stats():
        while True:
            try:
                if active_connections:
                    # Get current stats
                    command_stats = db.get_command_stats(days=1)
                    total_commands_today = sum(stat['usage_count'] for stat in command_stats)
                    
                    stats = {
                        'timestamp': datetime.utcnow().isoformat(),
                        'servers': 0,  # Would come from bot instance
                        'users': 0,   # Would come from bot instance
                        'commands_today': total_commands_today,
                        'uptime': '0h 0m 0s',  # Would come from bot instance
                        'status': 'online'
                    }
                    
                    socketio.emit('stats_update', stats)
                
                time.sleep(30)  # Update every 30 seconds
            except Exception as e:
                logger.error(f"Error in stats broadcaster: {e}")
                time.sleep(60)  # Wait longer on error
    
    # Start broadcaster thread
    stats_thread = threading.Thread(target=broadcast_stats, daemon=True)
    stats_thread.start()
    logger.info("Stats broadcaster started")
