#!/bin/bash

# --- COLOR CONFIGURATION (Mímisbrunnr Style) ---
CYAN='\033[96m'
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${CYAN}${BOLD}########################################################"
echo -e "#                                                      #"
echo -e "#      MÍMISBRUNNR: AUTOMATED INSTALLER v2.0           #"
echo -e "#                                                      #"
echo -e "########################################################${RESET}"

# 1. Privilege Verification
if [ "$EUID" -ne 0 ]; then 
  echo -e "${RED}[-] Please run the script with sudo.${RESET}"
  exit 1
fi

# 2. System Update
echo -e "\n${CYAN}[*] Phase 1: Updating repositories and system...${RESET}"
apt update && apt upgrade -y

# 3. Python and Development Dependencies Installation
echo -e "\n${CYAN}[*] Phase 2: Installing Python dependencies (dev, pip, venv)...${RESET}"
apt install -y python3-pip python3-venv python3-dev build-essential libssl-dev libffi-dev

# 4. Offensive Tool Installation (Required by Mímisbrunnr)
echo -e "\n${CYAN}[*] Phase 3: Installing security ecosystem tools...${RESET}"
# Installing tools invoked by the script via subprocess 
apt install -y nmap nikto gobuster nuclei dirb hydra exploitdb dnsutils

# 5. Virtual Environment Configuration (VENV)
echo -e "\n${CYAN}[*] Phase 4: Creating Python virtual environment...${RESET}"
if [ -d ".venv" ]; then
    echo -e "${YELLOW}[!] Virtual environment already exists. Reinstalling dependencies...${RESET}"
else
    python3 -m venv .venv
    echo -e "${GREEN}[+] Virtual environment '.venv' successfully created.${RESET}"
fi

# 6. Python Library Installation inside the environment
echo -e "\n${CYAN}[*] Phase 5: Installing necessary libraries (AI & YAML)...${RESET}"
# Activating and installing libraries detected in the source code 
source .venv/bin/activate
pip install --upgrade pip
pip install google-genai openai anthropic pyyaml

# 7. Configuration File Verification
if [ ! -f "config.yaml" ]; then
    echo -e "\n${YELLOW}[!] Creating sample tools.yaml file...${RESET}"
    cat <<EOF > tools.yaml
tools:
  - name: "nikto"
    command: "nikto -h http://<TARGET_IP>"
  - name: "gobuster"
    command: "gobuster dir -u http://<TARGET_IP> -w /usr/share/wordlists/dirb/common.txt"
  - name: "dirb"
    command: "dirb http://<TARGET_IP>"
  - name: "nuclei"
    command: "nuclei -u http://<TARGET_IP>"
EOF
fi

echo -e "\n${GREEN}${BOLD}########################################################"
echo -e "#    INSTALLATION COMPLETED SUCCESSFULLY               #"
echo -e "########################################################${RESET}"
echo -e "${YELLOW}To execute Mímisbrunnr, use the following commands:${RESET}"
echo -e "${BOLD}1. source .venv/bin/activate"
echo -e "2. python3 mimisbrunnr.py -t <TARGET> -m gemini -o report.md -c tools.yaml${RESET}\n"
