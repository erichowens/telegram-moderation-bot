#!/usr/bin/env python3
"""
Preview the Web Dashboard in Demo Mode
Run this script to see how the dashboard looks without needing a bot token
"""

import sys
import os
import webbrowser
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from web_dashboard import ModBotDashboard
except ImportError:
    print("Error: Could not import web_dashboard module")
    print("Please ensure you have installed all requirements:")
    print("  pip install -r requirements.txt")
    sys.exit(1)


def main():
    """Launch the dashboard in demo mode."""
    print("\n" + "="*60)
    print("   TELEGRAM MODERATION BOT - DASHBOARD PREVIEW")
    print("="*60)
    print()
    print("🚀 Starting dashboard in DEMO MODE...")
    print("📝 No bot token required for preview")
    print()
    
    # Create dashboard instance
    dashboard = ModBotDashboard(bot=None)
    
    # Set host and port
    host = '127.0.0.1'
    port = 5555  # Use different port to avoid conflicts
    
    # URL for demo mode
    demo_url = f"http://{host}:{port}/login?demo=true"
    
    print(f"🌐 Dashboard will open at: {demo_url}")
    print()
    print("Features you can preview:")
    print("  ✅ Real-time statistics dashboard")
    print("  ✅ Violation monitoring interface")
    print("  ✅ Interactive charts and graphs")
    print("  ✅ Activity logs and alerts")
    print("  ✅ Settings configuration panel")
    print()
    print("Press Ctrl+C to stop the preview")
    print("-"*60)
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(2)
        webbrowser.open(demo_url)
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        # Run the dashboard
        dashboard.run(host=host, port=port, debug=False, demo=True)
    except KeyboardInterrupt:
        print("\n\n✅ Dashboard preview stopped")
        print("Thank you for trying the dashboard!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please check that port 5555 is available")


if __name__ == '__main__':
    main()