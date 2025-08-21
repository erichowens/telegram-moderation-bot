"""
Simple GUI for Telegram Moderation Bot - User-friendly interface for non-technical users.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import queue
import json
import os
from datetime import datetime
from typing import Dict, List, Any

from src.bot import TelegramModerationBot
from src.config import Config
from src.model_manager import ModelManager


class ModBotGUI:
    """Main GUI application for the Telegram Moderation Bot."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Telegram Moderation Bot")
        self.root.geometry("900x700")
        
        # Bot state
        self.bot = None
        self.bot_running = False
        self.violations_queue = queue.Queue()
        
        # Data storage
        self.violations_data = []
        self.settings = self.load_settings()
        
        self.setup_ui()
        self.check_first_run()
    
    def setup_ui(self):
        """Set up the main user interface."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Setup tab
        self.setup_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.setup_tab, text="Setup")
        self.create_setup_tab()
        
        # Control panel tab
        self.control_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.control_tab, text="Control Panel")
        self.create_control_tab()
        
        # Violations tab
        self.violations_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.violations_tab, text="Violations")
        self.create_violations_tab()
        
        # Settings tab
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="Settings")
        self.create_settings_tab()
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_setup_tab(self):
        """Create the setup tab for first-time configuration."""
        frame = ttk.LabelFrame(self.setup_tab, text="Bot Setup", padding=10)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Instructions
        instructions = """
Welcome to Telegram Moderation Bot!

This bot helps keep your Telegram channels safe by automatically checking messages for:
• Spam and unwanted content
• Inappropriate images
• Harassment or bullying
• Adult content

To get started:
1. Get a bot token from @BotFather on Telegram
2. Download the AI models (we'll help you with this)
3. Configure your moderation rules
4. Start monitoring your channels
        """
        
        ttk.Label(frame, text=instructions, justify=tk.LEFT).pack(anchor="w", pady=(0, 20))
        
        # Bot token input
        token_frame = ttk.Frame(frame)
        token_frame.pack(fill="x", pady=5)
        ttk.Label(token_frame, text="Bot Token:").pack(side="left")
        self.token_entry = ttk.Entry(token_frame, show="*", width=50)
        self.token_entry.pack(side="left", padx=(10, 0), fill="x", expand=True)
        
        # Model status
        model_frame = ttk.LabelFrame(frame, text="AI Models", padding=10)
        model_frame.pack(fill="x", pady=10)
        
        self.model_status_label = ttk.Label(model_frame, text="Checking models...")
        self.model_status_label.pack(anchor="w")
        
        self.download_models_btn = ttk.Button(
            model_frame, 
            text="Download Required Models", 
            command=self.download_models
        )
        self.download_models_btn.pack(pady=5)
        
        # Start button
        self.start_btn = ttk.Button(
            frame, 
            text="Start Bot", 
            command=self.start_bot,
            style="Accent.TButton"
        )
        self.start_btn.pack(pady=20)
        
        self.check_models_status()
    
    def create_control_tab(self):
        """Create the control panel tab."""
        # Bot status
        status_frame = ttk.LabelFrame(self.control_tab, text="Bot Status", padding=10)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.bot_status_label = ttk.Label(status_frame, text="Bot: Stopped", font=("Arial", 12, "bold"))
        self.bot_status_label.pack(side="left")
        
        self.stop_btn = ttk.Button(status_frame, text="Stop Bot", command=self.stop_bot)
        self.stop_btn.pack(side="right")
        self.stop_btn.config(state="disabled")
        
        # Quick stats
        stats_frame = ttk.LabelFrame(self.control_tab, text="Today's Activity", padding=10)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill="x")
        
        self.stats_labels = {}
        stats = [
            ("Messages Checked", "0"),
            ("Violations Found", "0"),
            ("Actions Taken", "0"),
            ("Channels Monitored", "0")
        ]
        
        for i, (label, value) in enumerate(stats):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(stats_grid, text=f"{label}:").grid(row=row, column=col, sticky="w", padx=5)
            self.stats_labels[label] = ttk.Label(stats_grid, text=value, font=("Arial", 10, "bold"))
            self.stats_labels[label].grid(row=row, column=col+1, sticky="w", padx=5)
        
        # Recent activity log
        log_frame = ttk.LabelFrame(self.control_tab, text="Activity Log", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.activity_log = scrolledtext.ScrolledText(log_frame, height=15, state="disabled")
        self.activity_log.pack(fill="both", expand=True)
        
        # Add log control buttons
        log_buttons = ttk.Frame(log_frame)
        log_buttons.pack(fill="x", pady=5)
        
        ttk.Button(log_buttons, text="Clear Log", command=self.clear_log).pack(side="left")
        ttk.Button(log_buttons, text="Save Log", command=self.save_log).pack(side="left", padx=5)
        ttk.Button(log_buttons, text="Auto-scroll", command=self.toggle_autoscroll).pack(side="right")
        
        self.autoscroll = True
    
    def create_violations_tab(self):
        """Create the violations monitoring tab."""
        # Filter controls
        filter_frame = ttk.Frame(self.violations_tab)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Filter by:").pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var, values=[
            "All", "Spam", "Harassment", "Adult Content", "Hate Speech", "Violence"
        ])
        filter_combo.pack(side="left", padx=5)
        filter_combo.bind("<<ComboboxSelected>>", self.filter_violations)
        
        ttk.Button(filter_frame, text="Refresh", command=self.refresh_violations).pack(side="right")
        
        # Violations table
        table_frame = ttk.Frame(self.violations_tab)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("Time", "Channel", "Type", "Action", "Confidence")
        self.violations_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.violations_tree.heading(col, text=col)
            self.violations_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.violations_tree.yview)
        self.violations_tree.configure(yscrollcommand=scrollbar.set)
        
        self.violations_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.violations_tree.bind("<Double-1>", self.show_violation_details)
        
        # Add sample violations for demo
        self.add_sample_violations()
    
    def create_settings_tab(self):
        """Create the settings configuration tab."""
        # Moderation rules
        rules_frame = ttk.LabelFrame(self.settings_tab, text="Moderation Rules", padding=10)
        rules_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(rules_frame, text="Set how strict the bot should be (0 = lenient, 100 = strict):").pack(anchor="w")
        
        rules_grid = ttk.Frame(rules_frame)
        rules_grid.pack(fill="x", pady=10)
        
        self.rule_scales = {}
        rules = [
            ("Spam Detection", 70),
            ("Harassment Detection", 80),
            ("Adult Content", 90),
            ("Hate Speech", 85),
            ("Violence Detection", 85)
        ]
        
        for i, (rule_name, default_value) in enumerate(rules):
            row = i // 2
            col = (i % 2) * 3
            
            ttk.Label(rules_grid, text=rule_name).grid(row=row, column=col, sticky="w", padx=5)
            
            scale = tk.Scale(rules_grid, from_=0, to=100, orient="horizontal", length=150)
            scale.set(self.settings.get(rule_name.lower().replace(" ", "_"), default_value))
            scale.grid(row=row, column=col+1, padx=5)
            self.rule_scales[rule_name] = scale
        
        # Actions
        actions_frame = ttk.LabelFrame(self.settings_tab, text="Actions", padding=10)
        actions_frame.pack(fill="x", padx=10, pady=5)
        
        self.action_vars = {}
        actions = [
            ("Delete violating messages", True),
            ("Warn users about violations", True),
            ("Log all violations", True),
            ("Send alerts to admins", False)
        ]
        
        for action_name, default_value in actions:
            var = tk.BooleanVar(value=self.settings.get(action_name.lower().replace(" ", "_"), default_value))
            self.action_vars[action_name] = var
            ttk.Checkbutton(actions_frame, text=action_name, variable=var).pack(anchor="w", pady=2)
        
        # Save button
        ttk.Button(self.settings_tab, text="Save Settings", command=self.save_settings).pack(pady=20)
    
    def check_first_run(self):
        """Check if this is the first run and show setup wizard."""
        if not os.path.exists("config/config.yaml") or not self.settings.get("setup_complete", False):
            messagebox.showinfo(
                "Welcome!", 
                "Welcome to Telegram Moderation Bot!\n\nLet's get you set up. Please go to the Setup tab to configure your bot."
            )
            self.notebook.select(0)  # Select setup tab
    
    def check_models_status(self):
        """Check if required models are downloaded."""
        model_manager = ModelManager()
        status = model_manager.check_models_status()
        
        if status["all_ready"]:
            self.model_status_label.config(text="✓ All models ready", foreground="green")
            self.download_models_btn.config(state="disabled")
        else:
            missing = ", ".join(status["missing"])
            self.model_status_label.config(text=f"⚠ Missing models: {missing}", foreground="orange")
            self.download_models_btn.config(state="normal")
    
    def download_models(self):
        """Download required models in a separate thread."""
        self.download_models_btn.config(state="disabled", text="Downloading...")
        self.status_bar.config(text="Downloading AI models... This may take a few minutes.")
        
        def download_thread():
            try:
                model_manager = ModelManager()
                model_manager.download_default_models(
                    progress_callback=self.update_download_progress
                )
                self.root.after(0, self.download_complete)
            except Exception as e:
                self.root.after(0, lambda: self.download_error(str(e)))
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def update_download_progress(self, progress_text):
        """Update download progress in the status bar."""
        self.status_bar.config(text=f"Downloading: {progress_text}")
    
    def download_complete(self):
        """Handle successful model download."""
        self.status_bar.config(text="Models downloaded successfully!")
        self.check_models_status()
        messagebox.showinfo("Success", "AI models downloaded successfully! You can now start the bot.")
    
    def download_error(self, error_msg):
        """Handle model download error."""
        self.download_models_btn.config(state="normal", text="Download Required Models")
        self.status_bar.config(text="Download failed")
        messagebox.showerror("Download Error", f"Failed to download models:\n{error_msg}")
    
    def start_bot(self):
        """Start the Telegram bot."""
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showerror("Error", "Please enter your bot token first!")
            return
        
        # Save token to config
        self.save_token_to_config(token)
        
        try:
            self.bot = TelegramModerationBot(token)
            self.bot_running = True
            
            # Start bot in separate thread
            self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
            self.bot_thread.start()
            
            # Update UI
            self.bot_status_label.config(text="Bot: Running", foreground="green")
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.status_bar.config(text="Bot started successfully!")
            
            self.log_activity("Bot started and monitoring channels")
        self.update_stats()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start bot:\n{str(e)}")
    
    def stop_bot(self):
        """Stop the Telegram bot."""
        self.bot_running = False
        if self.bot:
            self.bot.stop()
        
        self.bot_status_label.config(text="Bot: Stopped", foreground="red")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_bar.config(text="Bot stopped")
        
        self.log_activity("Bot stopped")
        self.update_stats()
    
    def run_bot(self):
        """Run the bot (called in separate thread)."""
        try:
            self.bot.run()
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Bot Error", str(e)))
    
    def log_activity(self, message):
        """Add a message to the activity log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.activity_log.config(state="normal")
        self.activity_log.insert(tk.END, log_entry)
        if self.autoscroll:
            self.activity_log.see(tk.END)
        self.activity_log.config(state="disabled")
    
    def filter_violations(self, event=None):
        """Filter violations table by type."""
        # Implementation for filtering violations
        pass
    
    def refresh_violations(self):
        """Refresh the violations table."""
        # Implementation for refreshing violations data
        pass
    
    def show_violation_details(self, event):
        """Show detailed information about a violation."""
        selection = self.violations_tree.selection()
        if selection:
            # Implementation for showing violation details
            pass
    
    def save_settings(self):
        """Save current settings to file."""
        # Update settings from UI controls
        for rule_name, scale in self.rule_scales.items():
            self.settings[rule_name.lower().replace(" ", "_")] = scale.get()
        
        for action_name, var in self.action_vars.items():
            self.settings[action_name.lower().replace(" ", "_")] = var.get()
        
        self.settings["setup_complete"] = True
        
        # Save to file
        with open("gui_settings.json", "w") as f:
            json.dump(self.settings, f, indent=2)
        
        messagebox.showinfo("Settings Saved", "Your settings have been saved successfully!")
        self.status_bar.config(text="Settings saved")
    
    def load_settings(self):
        """Load settings from file."""
        try:
            with open("gui_settings.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_token_to_config(self, token):
        """Save bot token to config file."""
        os.makedirs("config", exist_ok=True)
        
        config_data = {
            "telegram": {"token": token},
            "moderation": {
                "text_model": {"type": "transformers", "path": "models/text_model"},
                "vision_model": {"type": "transformers", "path": "models/vision_model"},
                "multimodal_model": {"type": "transformers", "path": "models/multimodal_model"}
            },
            "policies": [
                {"name": "spam", "description": "Spam detection", "threshold": 0.7, "action": "delete"},
                {"name": "harassment", "description": "Harassment detection", "threshold": 0.8, "action": "delete"},
                {"name": "nsfw", "description": "Adult content", "threshold": 0.9, "action": "delete"}
            ]
        }
        
        import yaml
        with open("config/config.yaml", "w") as f:
            yaml.dump(config_data, f, default_flow_style=False)
    
    def clear_log(self):
        """Clear the activity log."""
        self.activity_log.config(state="normal")
        self.activity_log.delete(1.0, tk.END)
        self.activity_log.config(state="disabled")
    
    def save_log(self):
        """Save activity log to file."""
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, "w") as f:
                    f.write(self.activity_log.get(1.0, tk.END))
                messagebox.showinfo("Saved", "Activity log saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save log: {e}")
    
    def toggle_autoscroll(self):
        """Toggle automatic scrolling of the log."""
        self.autoscroll = not self.autoscroll
    
    def add_sample_violations(self):
        """Add sample violation data for demonstration."""
        sample_data = [
            ("12:34:56", "General Chat", "Spam", "Deleted", "87%"),
            ("12:35:12", "Announcements", "Harassment", "Warned", "73%"),
            ("12:36:03", "General Chat", "Adult Content", "Deleted", "95%"),
            ("12:37:45", "Off Topic", "Excessive Caps", "Warned", "62%"),
            ("12:38:20", "General Chat", "Hate Speech", "Deleted", "89%")
        ]
        
        for item in sample_data:
            self.violations_tree.insert("", "end", values=item)
    
    def update_stats(self):
        """Update statistics display."""
        if self.bot:
            stats = self.bot.get_stats()
            self.stats_labels["Messages Checked"].config(text=str(stats.get("messages_checked", 0)))
            self.stats_labels["Violations Found"].config(text=str(stats.get("violations_found", 0)))
            self.stats_labels["Actions Taken"].config(text=str(stats.get("actions_taken", 0)))
        
        # Update channels monitored (placeholder)
        self.stats_labels["Channels Monitored"].config(text="3")
        
        # Schedule next update
        self.root.after(5000, self.update_stats)  # Update every 5 seconds
    
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


if __name__ == "__main__":
    app = ModBotGUI()
    app.run()