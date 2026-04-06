#!/bin/bash

# --- CONFIGURACIÓN DE COLORES (Estilo Mímisbrunnr) ---
CYAN='\033[96m'
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${CYAN}${BOLD}########################################################"
echo -e "#                                                      #"
echo -e "#     MÍMISBRUNNR: AUTOMATED INSTALLER v2.0            #"
echo -e "#                                                      #"
echo -e "########################################################${RESET}"

# 1. Verificación de privilegios
if [ "$EUID" -ne 0 ]; then 
  echo -e "${RED}[-] Por favor, ejecuta el script con sudo.${RESET}"
  exit 1
fi

# 2. Actualización del sistema
echo -e "\n${CYAN}[*] Fase 1: Actualizando repositorios y sistema...${RESET}"
apt update && apt upgrade -y

# 3. Instalación de dependencias de Python y desarrollo
echo -e "\n${CYAN}[*] Fase 2: Instalando dependencias de Python (dev, pip, venv)...${RESET}"
apt install -y python3-pip python3-venv python3-dev build-essential libssl-dev libffi-dev

# 4. Instalación de herramientas ofensivas (Requeridas por Mímisbrunnr)
echo -e "\n${CYAN}[*] Fase 3: Instalando herramientas de seguridad del ecosistema...${RESET}"
# Se instalan las herramientas que el script invoca mediante subprocess 
apt install -y nmap nikto gobuster nuclei dirb hydra exploitdb dnsutils

# 5. Configuración del Entorno Virtual (VENV)
echo -e "\n${CYAN}[*] Fase 4: Creando entorno virtual de Python...${RESET}"
if [ -d ".venv" ]; then
    echo -e "${YELLOW}[!] El entorno virtual ya existe. Reinstalando dependencias...${RESET}"
else
    python3 -m venv .venv
    echo -e "${GREEN}[+] Entorno virtual '.venv' creado con éxito.${RESET}"
fi

# 6. Instalación de bibliotecas de Python dentro del entorno
echo -e "\n${CYAN}[*] Fase 5: Instalando bibliotecas necesarias (IA & YAML)...${RESET}"
# Se activan e instalan las librerías detectadas en el código fuente 
source .venv/bin/activate
pip install --upgrade pip
pip install google-genai openai anthropic pyyaml

# 7. Verificación de archivo de configuración
if [ ! -f "config.yaml" ]; then
    echo -e "\n${YELLOW}[!] Creando archivo tools.yaml de ejemplo...${RESET}"
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
echo -e "#   INSTALACIÓN COMPLETADA EXITOSAMENTE                #"
echo -e "########################################################${RESET}"
echo -e "${YELLOW}Para ejecutar Mímisbrunnr, usa los siguientes comandos:${RESET}"
echo -e "${BOLD}1. source .venv/bin/activate"
echo -e "2. python3 mimisbrunnr.py -t <TARGET> -m gemini -o report.md -c tools.yaml${RESET}\n"
