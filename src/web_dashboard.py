"""
Modern Web Dashboard for Telegram Moderation Bot
Beautiful, responsive web interface using Flask and modern UI
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import secrets

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import plotly.graph_objs as go
import plotly.utils

try:
    from .bot import TelegramModerationBot
    from .moderation import ModerationResult
    from .security import TokenManager
except ImportError:
    from bot import TelegramModerationBot
    from moderation import ModerationResult
    from security import TokenManager


class ModBotDashboard:
    """Modern web dashboard for the Telegram Moderation Bot."""
    
    def __init__(self, bot: Optional[TelegramModerationBot] = None):
        self.app = Flask(__name__, 
                         template_folder='../web/templates',
                         static_folder='../web/static')
        self.app.secret_key = secrets.token_hex(32)
        CORS(self.app)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self.bot = bot
        self.token_manager = TokenManager()
        
        # Statistics tracking
        self.stats = {
            'messages_processed_today': 0,
            'violations_today': 0,
            'actions_taken_today': 0,
            'active_groups': 0,
            'uptime': 0,
            'health_status': 'healthy',
            'cache_hit_rate': 0,
            'avg_response_time': 0
        }
        
        # Real-time data
        self.recent_violations = []
        self.activity_log = []
        self.performance_data = []
        
        self.setup_routes()
        self.setup_socketio()
    
    def setup_routes(self):
        """Set up Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main dashboard page."""
            # Check for demo mode
            if request.args.get('demo') == 'true':
                session['authenticated'] = True
                session['demo_mode'] = True
            
            if not session.get('authenticated'):
                return redirect(url_for('login'))
            
            return render_template('dashboard.html')
        
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """Login page."""
            if request.method == 'POST':
                token = request.json.get('token')
                if self._validate_token(token):
                    session['authenticated'] = True
                    return jsonify({'success': True})
                return jsonify({'success': False, 'error': 'Invalid token'}), 401
            return render_template('login.html')
        
        @self.app.route('/api/stats')
        def get_stats():
            """Get current statistics."""
            if not session.get('authenticated'):
                return jsonify({'error': 'Not authenticated'}), 401
            return jsonify(self.stats)
        
        @self.app.route('/api/violations')
        def get_violations():
            """Get recent violations."""
            if not session.get('authenticated'):
                return jsonify({'error': 'Not authenticated'}), 401
            return jsonify(self.recent_violations[-50:])  # Last 50 violations
        
        @self.app.route('/api/activity')
        def get_activity():
            """Get activity log."""
            if not session.get('authenticated'):
                return jsonify({'error': 'Not authenticated'}), 401
            return jsonify(self.activity_log[-100:])  # Last 100 activities
        
        @self.app.route('/api/charts/overview')
        def get_overview_chart():
            """Get overview chart data."""
            if not session.get('authenticated'):
                return jsonify({'error': 'Not authenticated'}), 401
            
            # Create time series data
            times = [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)]
            messages = [self._get_messages_at_hour(t) for t in times]
            violations = [self._get_violations_at_hour(t) for t in times]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=times, y=messages,
                mode='lines+markers',
                name='Messages',
                line=dict(color='#3B82F6', width=2)
            ))
            fig.add_trace(go.Scatter(
                x=times, y=violations,
                mode='lines+markers',
                name='Violations',
                line=dict(color='#EF4444', width=2)
            ))
            
            fig.update_layout(
                title='24-Hour Activity',
                xaxis_title='Time',
                yaxis_title='Count',
                template='plotly_dark',
                height=300
            )
            
            return jsonify(json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig)))
        
        @self.app.route('/api/charts/violations')
        def get_violations_chart():
            """Get violations breakdown chart."""
            if not session.get('authenticated'):
                return jsonify({'error': 'Not authenticated'}), 401
            
            categories = ['Spam', 'Harassment', 'NSFW', 'Hate Speech', 'Caps']
            values = [30, 25, 15, 20, 10]  # Example data
            
            fig = go.Figure(data=[go.Pie(
                labels=categories,
                values=values,
                hole=.3,
                marker_colors=['#EF4444', '#F59E0B', '#8B5CF6', '#EC4899', '#6366F1']
            )])
            
            fig.update_layout(
                title='Violations by Type',
                template='plotly_dark',
                height=300
            )
            
            return jsonify(json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig)))
        
        @self.app.route('/api/bot/start', methods=['POST'])
        def start_bot():
            """Start the bot."""
            if not session.get('authenticated'):
                return jsonify({'error': 'Not authenticated'}), 401
            
            # In demo mode, simulate bot starting
            if session.get('demo_mode'):
                self._simulate_demo_activity()
                return jsonify({'success': True, 'message': 'Demo bot started'})
            
            if self.bot and not self.bot.bot_running:
                # Start bot in background
                asyncio.create_task(self._start_bot())
                return jsonify({'success': True, 'message': 'Bot starting...'})
            return jsonify({'success': False, 'message': 'Bot already running'})
        
        @self.app.route('/api/bot/stop', methods=['POST'])
        def stop_bot():
            """Stop the bot."""
            if not session.get('authenticated'):
                return jsonify({'error': 'Not authenticated'}), 401
            
            if self.bot and self.bot.bot_running:
                self.bot.stop()
                return jsonify({'success': True, 'message': 'Bot stopped'})
            return jsonify({'success': False, 'message': 'Bot not running'})
        
        @self.app.route('/api/settings', methods=['GET', 'POST'])
        def settings():
            """Get or update settings."""
            if not session.get('authenticated'):
                return jsonify({'error': 'Not authenticated'}), 401
            
            if request.method == 'POST':
                settings = request.json
                self._save_settings(settings)
                return jsonify({'success': True})
            
            return jsonify(self._load_settings())
    
    def setup_socketio(self):
        """Set up Socket.IO for real-time updates."""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            if session.get('authenticated'):
                emit('connected', {'message': 'Connected to dashboard'})
                # Send initial stats
                emit('stats_update', self.stats)
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            pass
        
        @self.socketio.on('request_update')
        def handle_update_request():
            """Handle request for updated stats."""
            if session.get('authenticated'):
                emit('stats_update', self.stats)
    
    def update_stats(self, stats: Dict[str, Any]):
        """Update statistics and broadcast to connected clients."""
        self.stats.update(stats)
        self.socketio.emit('stats_update', self.stats, broadcast=True)
    
    def add_violation(self, violation: Dict[str, Any]):
        """Add a violation and broadcast to clients."""
        violation['timestamp'] = datetime.now().isoformat()
        self.recent_violations.append(violation)
        self.recent_violations = self.recent_violations[-100:]  # Keep last 100
        
        self.socketio.emit('new_violation', violation, broadcast=True)
    
    def add_activity(self, activity: str, level: str = 'info'):
        """Add to activity log."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'message': activity,
            'level': level
        }
        self.activity_log.append(entry)
        self.activity_log = self.activity_log[-500:]  # Keep last 500
        
        self.socketio.emit('new_activity', entry, broadcast=True)
    
    def _validate_token(self, token: str) -> bool:
        """Validate the bot token."""
        # Simple validation for demo - in production, verify against Telegram API
        return token and len(token) > 20 and ':' in token
    
    def _get_messages_at_hour(self, hour: datetime) -> int:
        """Get message count for a specific hour (mock data)."""
        import random
        return random.randint(50, 200)
    
    def _get_violations_at_hour(self, hour: datetime) -> int:
        """Get violation count for a specific hour (mock data)."""
        import random
        return random.randint(0, 20)
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load bot settings."""
        settings_file = 'config/settings.json'
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                return json.load(f)
        return {
            'thresholds': {
                'spam': 0.7,
                'harassment': 0.6,
                'nsfw': 0.8,
                'hate_speech': 0.7
            },
            'actions': {
                'delete_messages': True,
                'warn_users': True,
                'ban_repeat_offenders': False
            },
            'monitoring': {
                'log_all_violations': True,
                'send_alerts': False
            }
        }
    
    def _save_settings(self, settings: Dict[str, Any]):
        """Save bot settings."""
        settings_file = 'config/settings.json'
        os.makedirs('config', exist_ok=True)
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
    
    async def _start_bot(self):
        """Start the bot asynchronously."""
        if self.bot:
            self.add_activity('Starting bot...', 'info')
            await self.bot.run()
            self.add_activity('Bot started successfully', 'success')
    
    def _simulate_demo_activity(self):
        """Simulate activity for demo mode."""
        import threading
        import random
        import time
        
        def generate_demo_data():
            """Generate fake data for demo."""
            time.sleep(1)
            
            # Update stats
            self.stats.update({
                'messages_processed_today': random.randint(1000, 5000),
                'violations_today': random.randint(50, 200),
                'active_groups': random.randint(5, 15),
                'health_status': 'healthy',
                'uptime': random.randint(3600, 86400),
                'cache_hit_rate': random.uniform(0.85, 0.99),
                'avg_response_time': random.uniform(50, 150)
            })
            self.socketio.emit('stats_update', self.stats, broadcast=True)
            
            # Generate some violations
            violation_types = ['Spam', 'Harassment', 'NSFW', 'Caps Lock', 'Hate Speech']
            groups = ['General Chat', 'Tech Discussion', 'Gaming', 'News Channel', 'Support']
            users = ['User123', 'JohnDoe', 'Alice99', 'Bob2024', 'Charlie_X']
            
            for _ in range(random.randint(3, 8)):
                violation = {
                    'type': random.choice(violation_types),
                    'group': random.choice(groups),
                    'user': random.choice(users),
                    'timestamp': datetime.now().isoformat(),
                    'severity': random.choice(['low', 'medium', 'high'])
                }
                time.sleep(random.uniform(2, 5))
                self.add_violation(violation)
            
            # Generate activity logs
            activities = [
                'Bot started successfully',
                'Connected to Telegram servers',
                'Monitoring 10 groups',
                'Message processed from General Chat',
                'Spam detected and removed',
                'User warned for violation',
                'Health check completed',
                'Cache cleared',
                'Settings updated'
            ]
            
            for activity in random.sample(activities, 5):
                self.add_activity(activity, random.choice(['info', 'success', 'warning']))
                time.sleep(random.uniform(1, 3))
        
        # Run in background thread
        thread = threading.Thread(target=generate_demo_data)
        thread.daemon = True
        thread.start()
    
    def run(self, host='127.0.0.1', port=5000, debug=False, demo=False):
        """Run the dashboard."""
        print(f"🌐 Dashboard running at http://{host}:{port}")
        if demo:
            print(f"📺 Demo mode: http://{host}:{port}/login?demo=true")
        self.socketio.run(self.app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    dashboard = ModBotDashboard()
    dashboard.run(debug=True)