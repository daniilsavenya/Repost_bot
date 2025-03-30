import os
import sys
import platform
import subprocess
import json
import re
from pathlib import Path
from time import time
from typing import List, Dict, Union

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

class BotInstaller:
    def __init__(self):
        self.os_name = platform.system()
        self.is_linux = self.os_name == "Linux"
        self.is_windows = self.os_name == "Windows"
        self.repo_url = "https://github.com/daniilsavenya/Repost_bot.git"
        self.repo_dir = Path("Repost_bot")
        self.config_path = Path("config.json")
        self.auth_url = "https://daniilsavenya.github.io/Repost_bot/vk_auth.html"
        
        self.venv_dir = Path("env")
        self.venv_bin = self.venv_dir / ("Scripts" if self.is_windows else "bin")
        self.python_exe = self.venv_bin / ("python.exe" if self.is_windows else "python")

    def print_color(self, color: str, message: str) -> None:
        print(f"{color}{message}{Colors.RESET}")

    def run_command(self, cmd: List[str], cwd: Union[str, Path] = None) -> None:
        try:
            subprocess.run(
                cmd,
                cwd=str(cwd) if cwd else None,
                check=True,
                shell=self.is_windows,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        except subprocess.CalledProcessError as e:
            self.print_color(Colors.RED, f"Command failed: {' '.join(cmd)}")
            self.print_color(Colors.YELLOW, f"Error: {e.stderr}")
            sys.exit(1)

    def check_dependencies(self) -> None:
        required = ["git"]
        self.print_color(Colors.CYAN, "Checking system dependencies...")
        
        for dep in required:
            try:
                subprocess.run(
                    [dep, "--version"],
                    capture_output=True,
                    check=True,
                    shell=self.is_windows
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.print_color(Colors.RED, f"Missing required dependency: {dep}")
                sys.exit(1)

    def clone_repo(self) -> None:
        if self.repo_dir.exists():
            self.print_color(Colors.YELLOW, "Repository already exists, skipping clone...")
            return

        self.print_color(Colors.GREEN, "Cloning repository...")
        self.run_command(["git", "clone", self.repo_url])

    def setup_virtualenv(self) -> None:
        if self.venv_dir.exists():
            self.print_color(Colors.YELLOW, "Virtual environment already exists, skipping...")
            return

        self.print_color(Colors.GREEN, "Creating virtual environment...")
        python_cmd = "python" if self.is_windows else "python3"
        self.run_command([python_cmd, "-m", "venv", str(self.venv_dir)])

    def install_dependencies(self) -> None:
        self.print_color(Colors.GREEN, "Installing Python dependencies...")

        pip_upgrade_cmd = [str(self.python_exe), "-m", "pip", "install", "--upgrade", "pip"]
        self.run_command(pip_upgrade_cmd)
        
        pip_install_cmd = [str(self.python_exe), "-m", "pip", "install", "-r", "requirements.txt"]
        self.run_command(pip_install_cmd)

    def validate_input(self, prompt: str, pattern: str, error_msg: str) -> str:
        while True:
            value = input(prompt).strip()
            if re.fullmatch(pattern, value):
                return value
            self.print_color(Colors.RED, error_msg)

    def create_config(self) -> None:
        self.print_color(Colors.CYAN, "\n=== Configuration Setup ===")
        
        vk_user_id = self.validate_input(
            "Enter VK User ID: ",
            r"^-?\d+$",
            "Invalid VK User ID (must be numeric)"
        )
        
        tg_channel_id = self.validate_input(
            "Enter Telegram Channel ID (with -100 prefix): ",
            r"^-?\d+$",
            "Invalid Channel ID format"
        )
        
        tg_bot_token = self.validate_input(
            "Enter Telegram Bot Token: ",
            r"^[0-9]{8,10}:[a-zA-Z0-9_-]{35}$",
            "Invalid Bot Token format"
        )
        
        self.print_color(Colors.YELLOW, f"\nGet VK Access Token from: {self.auth_url}")
        vk_access_token = self.validate_input(
            "Enter VK Access Token: ",
            r"^[a-zA-Z0-9._-]+$",
            "Invalid VK Token format"
        )
        
        log_level = "INFO"
        while True:
            user_input = input("Log Level [INFO/DEBUG/WARNING/ERROR] (default INFO): ").strip().upper()
            if not user_input:
                break
            if user_input in ["INFO", "DEBUG", "WARNING", "ERROR"]:
                log_level = user_input
                break
            self.print_color(Colors.RED, "Invalid log level")

        config = {
            "vk_user_id": int(vk_user_id),
            "tg_channel_id": int(tg_channel_id),
            "tg_bot_token": tg_bot_token,
            "vk_access_token": vk_access_token,
            "last_post_date": int(time()),
            "log_level": log_level
        }

        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=4)
        self.print_color(Colors.GREEN, "Configuration file created successfully!")

    def run_bot(self) -> None:
        self.print_color(Colors.CYAN, "\nStarting bot...")
        bot_cmd = [str(self.python_exe), str("main.py")]
        
        try:
            subprocess.run(bot_cmd, check=True)
        except KeyboardInterrupt:
            self.print_color(Colors.YELLOW, "\nBot stopped by user")
        except Exception as e:
            self.print_color(Colors.RED, f"Failed to start bot: {str(e)}")
            sys.exit(1)

    def setup_systemd_service(self) -> None:
        self.print_color(Colors.CYAN, "\n=== Systemd Service Setup ===")
        answer = input("Do you want to enable the bot as a systemd user service? [y/N] ").strip().lower()
        
        if answer != 'y':
            self.print_color(Colors.YELLOW, "Skipping systemd service setup...")
            return

        try:
            # Получаем абсолютные пути
            python_path = self.python_exe.resolve()
            main_script = Path.cwd() / "main.py"
            service_name = "repost-bot.service"
            
            # Создаем директорию для юнитов
            unit_dir = Path.home() / ".config/systemd/user"
            unit_dir.mkdir(parents=True, exist_ok=True)
            
            # Формируем содержимое юнита
            unit_content = f"""[Unit]
Description=Repost Bot Service
After=network.target

[Service]
ExecStart={python_path} {main_script}
WorkingDirectory={Path.cwd()}
Restart=on-failure
RestartSec=3
StandardOutput=journal

[Install]
WantedBy=default.target
"""
            # Записываем файл сервиса
            service_path = unit_dir / service_name
            with open(service_path, 'w') as f:
                f.write(unit_content)
            
            # Выполняем systemctl команды
            self.run_command(["systemctl", "--user", "daemon-reload"])
            self.run_command(["systemctl", "--user", "enable", service_name])
            self.run_command(["systemctl", "--user", "start", service_name])
            
            # Показываем статус
            self.print_color(Colors.GREEN, "\nService status:")
            subprocess.run(["systemctl", "--user", "status", service_name])
            
            # Рекомендации по lingering
            username = os.getenv("USER")
            self.print_color(Colors.YELLOW, "\nFor background operation without active session, run:")
            self.print_color(Colors.CYAN, f"sudo loginctl enable-linger {username}")
            
        except Exception as e:
            self.print_color(Colors.RED, f"Systemd setup failed: {str(e)}")
            sys.exit(1)

    def install(self) -> None:
        try:
            self.check_dependencies()
            self.clone_repo()
            os.chdir(self.repo_dir)
            self.setup_virtualenv()
            self.install_dependencies()
            self.create_config()
            self.run_bot()
            
            if self.is_linux:
                self.setup_systemd_service()
                
        except Exception as e:
            self.print_color(Colors.RED, f"Installation failed: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    if platform.system() == "Windows":
        os.system('color')
    installer = BotInstaller()
    installer.install()
    print(f"{Colors.GREEN}\nSetup completed successfully!{Colors.RESET}")