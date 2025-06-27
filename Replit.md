# PulseForge Bot

## Overview

PulseForge is a comprehensive Discord bot with an integrated web dashboard. It features moderation tools, music playback, utilities, gaming commands, and real-time monitoring capabilities. The application runs both a Discord bot and a Flask web server concurrently, providing both Discord functionality and web-based management.

## System Architecture

The system follows a modular architecture with clear separation between the Discord bot functionality and web dashboard:

- **Bot Layer**: Discord.py-based bot with cog-based command organization
- **Web Layer**: Flask application with SocketIO for real-time updates
- **Data Layer**: SQLite database for persistent storage
- **Utilities Layer**: Shared logging and configuration management

## Key Components

### Discord Bot (`bot/`)
- **Main Bot Class**: `PulseForgeBot` extends `commands.Bot` with custom prefix handling and rate limiting
- **Cog System**: Modular command organization across four main categories:
  - **Moderation**: Ban, kick, mute, warn, message cleanup
  - **Music**: YouTube audio playback with queue management
  - **Utilities**: Server info, user info, ping, system stats
  - **Gaming**: Trivia, dice rolling, coin flipping, random number generation
- **Database Integration**: SQLite-based storage for server settings, warnings, and command statistics

### Web Dashboard (`web/`)
- **Flask Application**: RESTful API endpoints and template rendering
- **Real-time Updates**: SocketIO integration for live statistics and monitoring
- **Dashboard Interface**: Bootstrap-based responsive UI with Alpine.js for interactivity
- **API Endpoints**: Statistics, command usage, and bot status information

### Database Schema
- **server_settings**: Guild-specific configuration (prefix, channels, welcome messages)
- **warnings**: User warning system with moderator tracking
- **command_stats**: Usage analytics and rate limiting data

### Frontend Architecture
- **Templates**: Jinja2-based HTML templates with Bootstrap 5 styling
- **JavaScript**: Alpine.js for reactive components, Chart.js for data visualization
- **Real-time Communication**: Socket.IO for live updates and notifications

## Data Flow

1. **Command Processing**: Discord commands → Bot cogs → Database updates → Response
2. **Web Requests**: HTTP requests → Flask routes → Database queries → JSON/HTML response  
3. **Real-time Updates**: Database changes → SocketIO events → Frontend updates
4. **Music Playback**: User commands → yt-dlp extraction → Discord voice client → Audio streaming

## External Dependencies

### Core Dependencies
- **discord.py**: Discord API interaction and bot framework
- **flask**: Web framework for dashboard API
- **flask-socketio**: Real-time bidirectional communication
- **yt-dlp**: YouTube audio extraction for music features
- **psutil**: System resource monitoring

### Frontend Libraries (CDN)
- **Bootstrap 5**: UI component framework
- **Chart.js**: Data visualization and analytics charts
- **Alpine.js**: Lightweight reactive JavaScript framework
- **Socket.IO Client**: Real-time communication client
- **HTMX**: Dynamic HTML updates and AJAX interactions

## Deployment Strategy

The application is designed for Replit deployment with the following configuration:

- **Runtime**: Python 3.11 with Nix package management
- **Concurrent Execution**: Threading-based approach running Flask and Discord bot simultaneously
- **Port Configuration**: Flask web server on port 5000 with automatic port detection
- **Process Management**: Main thread handles bot, daemon thread handles web server
- **Environment Variables**: Discord token, database path, and configuration via environment

### Configuration Management
- Environment-based configuration through `config.py`
- Separate settings for development and production environments
- Centralized logging configuration with file and console output
- Database path and connection settings configurable via environment variables

## Changelog
- June 27, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.
