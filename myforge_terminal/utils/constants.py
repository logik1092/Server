"""
File: myforge_terminal/utils/constants.py
Description: Constants Module - Application constants

Structure:
  (No public classes or functions defined in this file - constants only)
"""

# Application information
APP_NAME = "MyForge SSH Terminal"
APP_VERSION = "2.0.0"
APP_AUTHOR = "MyForge Team"

# Default paths
DEFAULT_PATH = "/var/www/myforge.ai"
NGINX_PATH = "/etc/nginx/sites-available"
HOME_PATH = "~"

# File types
TEXT_FILE_EXTENSIONS = [
    '.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.md',
    '.ini', '.conf', '.cfg', '.log', '.sh', '.bash', '.php', '.c',
    '.cpp', '.h', '.java', '.yaml', '.yml', '.toml', '.csv', '.lua'
]

BINARY_FILE_EXTENSIONS = [
    '.pdf', '.gz', '.zip', '.tar', '.rar', '.jpg', '.jpeg', '.png',
    '.gif', '.mp3', '.mp4', '.avi', '.mov', '.exe', '.dll', '.so', '.bin'
]

# Special markers for data capture
CWD_START_MARKER = "__MYFORGE_CWD_START__"
CWD_END_MARKER = "__MYFORGE_CWD_END__"
LS_FILES_START_MARKER = "__MYFORGE_LS_FILES_START__"
LS_FILES_END_MARKER = "__MYFORGE_LS_FILES_END__"

# Default server configurations
DEFAULT_SERVERS = {
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

# Default commands
DEFAULT_COMMANDS = {
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