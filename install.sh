#!/usr/bin/env bash
set -eo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

CONFIG_TEMPLATE='{
    "vk_user_id": %s,
    "tg_channel_id": %s,
    "tg_bot_token": "%s",
    "vk_access_token": "%s",
    "last_post_date": %s,
    "log_level": "%s"
}'

error_exit() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
    exit 1
}

validate_number() {
    [[ "$1" =~ ^-?[0-9]+$ ]] || error_exit "Invalid number format: $1"
}

validate_token() {
    [[ "$1" =~ ^[a-zA-Z0-9:_.\-]+$ ]] || error_exit "Invalid token format"
}

check_dependencies() {
    local dependencies=("git" "python3")
    for dep in "${dependencies[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            error_exit "$dep is not installed. Please install it first."
        fi
    done
}

install_bot() {
    if [ ! -d "Repost_bot" ]; then
        echo -e "${GREEN}[1/5] Cloning repository...${NC}"
        git clone https://github.com/daniilsavenya/Repost_bot.git || error_exit "Failed to clone repository"
    else
        echo -e "${YELLOW}[1/5] Existing repository found, skipping clone...${NC}"
    fi

    echo -e "${GREEN}[2/5] Entering project directory...${NC}"
    cd Repost_bot || error_exit "Project directory not found"

    if [ ! -d "env" ]; then
        echo -e "${GREEN}[3/5] Creating virtual environment...${NC}"
        python3 -m venv env || error_exit "Virtual environment creation failed"
    else
        echo -e "${YELLOW}[3/5] Virtual environment already exists, skipping...${NC}"
    fi

    echo -e "${GREEN}[4/5] Installing dependencies...${NC}"
    source env/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt || error_exit "Dependency installation failed"
}

configure_bot() {
    echo -e "\n${GREEN}[5/5] Configuration Setup ${NC}"
    
    read -p "Enter VK User ID (get from https://daniilsavenya.github.io/Repost_bot/vk_auth.html): " vk_user_id
    validate_number "$vk_user_id"
    
    read -p "Enter Telegram Channel ID (include -100 prefix for public channels): " tg_channel_id
    validate_number "$tg_channel_id"
    
    read -p "Enter Telegram Bot Token: " tg_bot_token
    validate_token "$tg_bot_token"
    
    echo -e "${YELLOW}Get VK Access Token from:"
    echo -e "https://daniilsavenya.github.io/Repost_bot/vk_auth.html${NC}"
    read -p "Enter VK Access Token: " vk_access_token
    validate_token "$vk_access_token"
    
    log_level="INFO"
    read -p "Enter Log Level [INFO/DEBUG/WARNING/ERROR] (default INFO): " input_log_level
    [[ -n "$input_log_level" ]] && log_level="$input_log_level"
    
    last_post_date=$(date +%s)
    
    echo -e "${GREEN}Creating config.json...${NC}"
    printf "$CONFIG_TEMPLATE" "$vk_user_id" "$tg_channel_id" "$tg_bot_token" \
        "$vk_access_token" "$last_post_date" "$log_level" > config.json
    
    [[ -s config.json ]] || error_exit "Failed to create configuration file"
}

run_bot() {
    echo -e "\n${GREEN}Launching bot for verification...${NC}"
    source env/bin/activate
    if ! python3 main.py; then
        echo -e "${RED}Bot startup failed. Check configuration and dependencies.${NC}"
        exit 1
    fi
}

main() {
    check_dependencies
    install_bot
    configure_bot
    run_bot
    echo -e "${GREEN}\nSetup complete! Bot is running. Press Ctrl+C to stop.${NC}"
}

main