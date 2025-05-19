"""
File: myforge_terminal/utils/config.py
Description: Configuration Module - Manage application configuration

Structure:
  Classes:
    Config:
      Description: Manage application configuration
      - __init__(self, filename='config.json')
      - get(self, key, default=None)
      - set(self, key, value)
      - load(self)
      - save(self)
      - reset_to_default(self)
"""

import os
import json

class Config:
    """Manage application configuration"""
    
    def __init__(self, filename="config.json"):
        """Initialize configuration"""
        self.filename = filename
        self.config = self._get_default_config()
        
        # Load config if exists
        self.load()
    
    def get(self, key, default=None):
        """Get configuration value by key"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
    
    def load(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, "r") as f:
                    loaded_config = json.load(f)
                    
                    # Update config with loaded values
                    self._update_config(loaded_config)
        except Exception as e:
            print(f"Error loading configuration: {e}")
    
    def save(self):
        """Save configuration to file"""
        try:
            with open(self.filename, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def reset_to_default(self):
        """Reset configuration to default values"""
        self.config = self._get_default_config()
    
    def _update_config(self, loaded_config):
        """Update configuration with loaded values"""
        for key, value in loaded_config.items():
            if key == "commands" and isinstance(value, dict):
                # Ensure commands dictionary exists
                if "commands" not in self.config or not isinstance(self.config["commands"], dict):
                    self.config["commands"] = {}
                
                # Merge commands
                self.config["commands"].update(value)
            else:
                self.config[key] = value
    
    def _get_default_config(self):
        """Get default configuration"""
        default_commands = {
            "launch_llama": "cd /var/www/myforge.ai/llama.cpp/build/bin && ./llama-server -m ../../models/openchat-3.5-0106.Q4_K_M.gguf --port 8001 --threads 6",
            "activate_venv": "source /var/www/myforge.ai/venv/bin/activate",
            "start_uvicorn": "uvicorn server:app --host 0.0.0.0 --port=8080 --reload",
            "kill_uvicorn": "pkill -f uvicorn",
            "reload_nginx": "sudo systemctl reload nginx",
            "restart_nginx": "systemctl restart nginx",
            "nginx_status": "systemctl status nginx",
            "test_nginx": "nginx -t",
            "cd_website": "cd /var/www/myforge.ai",
            "cd_nginx": "cd /etc/nginx/sites-available",
            "cd_home": "cd ~",
            "list_files": "ls -l",
            "python_processes": "ps aux | grep python",
            "check_memory": "free -h",
            "check_disk": "df -h",
            "check_cpu": "top -bn1 | head -n 5",
            "health_check": "curl http://localhost:42181/health"
        }
        
        default_servers = {
            "MyForge": {
                "username": "forgeadmin",
                "hostname": "209.145.57.9",
                "port": 22
            },
            "Vultr": {
                "username": "root",
                "hostname": "149.28.126.226",
                "port": 22
            }
        }
        
        return {
            "username": "forgeadmin",
            "hostname": "209.145.57.9",
            "port": 22,
            "password": "",
            "key_path": "",
            "commands": default_commands,
            "servers": default_servers,
            "theme": "dark",
            "font_size": 10,
            "log_commands": True,
            "auto_connect": False
        }