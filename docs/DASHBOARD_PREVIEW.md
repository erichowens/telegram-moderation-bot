# Telegram Moderation Bot - Dashboard Preview

## 🎨 Modern Web Dashboard

The Telegram Moderation Bot comes with a beautiful, modern web dashboard that provides real-time monitoring and control of your bot.

## 🚀 Quick Preview

To see the dashboard in action without setting up a bot:

```bash
python preview_dashboard.py
```

This will launch the dashboard in **demo mode** with simulated data so you can explore all features.

## 📸 Dashboard Features

### 1. **Real-Time Statistics**
- Live message count tracking
- Violation detection metrics
- Active group monitoring
- System health score

### 2. **Beautiful Visualizations**
- 24-hour activity charts
- Violation type breakdown (pie chart)
- Time-series data with Plotly
- Responsive, animated UI

### 3. **Violation Monitoring**
- Real-time violation feed
- Detailed violation information
- User and group tracking
- Severity indicators

### 4. **Activity Logs**
- Chronological event stream
- Color-coded log levels
- Search and filter capabilities
- Export functionality

### 5. **Settings Management**
- Adjustable detection thresholds
- Automated action configuration
- Per-group settings
- Rule customization

## 🎨 Design Features

- **Dark Theme**: Easy on the eyes for extended monitoring
- **Glass Morphism**: Modern translucent UI elements
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-Time Updates**: WebSocket-powered live data
- **Smooth Animations**: Polished user experience

## 🔧 Technical Stack

- **Backend**: Flask + Socket.IO for real-time communication
- **Frontend**: Tailwind CSS for beautiful, responsive design
- **Charts**: Plotly.js for interactive visualizations
- **Icons**: Lucide icons for clean, modern iconography

## 📱 Access Methods

### 1. Direct Launch
```bash
python src/web_dashboard.py
```
Then open: http://localhost:5000

### 2. Demo Mode (No Bot Required)
```bash
python preview_dashboard.py
```
Automatically opens: http://localhost:5555/login?demo=true

## 🔐 Security Features

- Token-based authentication
- Encrypted token storage
- Session management
- CORS protection
- Input validation

## 📊 Dashboard Sections

### Login Page
- Secure authentication
- Demo mode toggle
- Beautiful gradient animations
- Token validation

### Main Dashboard
- **Stats Cards**: Key metrics at a glance
- **Activity Charts**: Visual representation of bot activity
- **Violations Tab**: Recent violations with details
- **Activity Tab**: Real-time event log
- **Settings Tab**: Configuration management

## 🎯 Use Cases

1. **Group Administrators**
   - Monitor multiple groups from one interface
   - Track violation patterns
   - Adjust moderation sensitivity

2. **Community Managers**
   - Real-time threat detection
   - User behavior analysis
   - Performance metrics

3. **Bot Operators**
   - System health monitoring
   - Resource usage tracking
   - Configuration management

## 🚦 Getting Started

1. **Install Dependencies**
   ```bash
   pip install flask flask-socketio flask-cors plotly
   ```

2. **Run Demo Mode**
   ```bash
   python preview_dashboard.py
   ```

3. **Explore Features**
   - Click "Start Bot" to see simulated activity
   - Watch real-time violations appear
   - Try different chart views
   - Adjust settings sliders

## 💡 Tips

- The dashboard updates in real-time - no need to refresh
- Click on violations for more details
- Charts are interactive - hover for more information
- Settings changes are applied immediately
- Use demo mode to test configurations before going live

## 🔄 Live Updates

The dashboard uses WebSocket connections for instant updates:
- New violations appear immediately
- Statistics refresh automatically
- Charts update in real-time
- No manual refresh needed

## 📈 Performance

- Lightweight and fast
- Minimal resource usage
- Optimized for continuous monitoring
- Handles thousands of events efficiently

---

**Try it now!** Run `python preview_dashboard.py` to see the dashboard in action.