import argparse
import sys
import subprocess
import getpass
import os
import re

#Import AI libraries
try:
	from google import genai
	from openai import OpenAI
	import anthropic
	import yaml
	
except ImportError:
	print("[-] Missing required libraries. Please install them using:")
	print(" pip install openai google-genai anthropic pyyaml")
	sys.exit(1)

class Colors:
	ORANGE = '\033[38;5;208m'
	CYAN = '\033[96m'
	GREEN = '\033[92m'
	YELLOW = '\033[93m'
	RED = '\033[91m'
	BOLD = '\033[1m'
	RESET = '\033[0m'


def initial_banner():
	"""Displays a stylized banner when starting the tool."""
		
	banner = rf"""{Colors.GREEN}
    ==============================================================================
    ||                                                                          ||
    ||  __  __ ___ __  __ ___  ____  ____  ____  _   _ _   _ _   _ ____         ||
    || |  \/  |_ _|  \/  |_ _|/ ___|| __ )|  _ \| | | | \ | | \ | |  _ \        ||
    || | |\/| || || |\/| || | \___ \|  _ \| |_) | | | |  \| |  \| | |_) |       ||
    || | |  | || || |  | || |  ___) | |_) |  _ <| |_| | |\  | |\  |  _ <        ||
    || |_|  |_|___|_|  |_|___||____/|____/|_| \_\\___/|_| \_|_| \_|_| \_\       ||
    ||                                                                          ||
    ||                >>  AI-AUGMENTED OFFENSIVE INSIGHT  <<                    ||
    ||                >>       VULNERABILITY SEER v2.0    <<                    ||
    ||                                                                          ||
    =============================================================================={Colors.RESET}
    """
	print (banner)
		

def get_arguments():
	"Configures and returns the command line arguments."

	parser = argparse.ArgumentParser(
		description = f"{Colors.GREEN}{Colors.BOLD} MIMISBRUNNR: AI-Augmented Offensive Framework{Colors.RESET}\n"
			"An Advanced security tool that orchestrates Nmap scan, AI-driven analysis, "
			" and deterministic tool execution across 5 automated phases",
		
		formatter_class = argparse.RawTextHelpFormatter,
		add_help = False,
		
		#"Open-source framework for executing offensive security tools integrating Artificial Intelligence",
		epilog = "Usage example: python3 mimisbrunnr.py -t 192.168.1.100 -m gemini -c tools.yaml -o report.md"
	)
	
	
	config_group = parser.add_argument_group(f'{Colors.YELLOW}General Configuration{Colors.RESET}')
	config_group.add_argument("-h", "--help", action='help', help="Show this detailed help message and exit")
	
	config_group.add_argument("-c", "--config", default="tools.yaml", required=True, help="Path to the file containing mandatory tools.\n"
		"This file defines the determinsitic tools (like Nuclei or Gobuster) \n"
		"that Mimisbrunnr will execute regardless of AI suggestions.")
		
	target_group = parser.add_argument_group(f'{Colors.YELLOW} Target Identification{Colors.RESET}')
	group = target_group.add_mutually_exclusive_group(required=True)
	group.add_argument("-t", "--target", help="Specify a single target (IP or Domain) for assessment.")
	group.add_argument("-f", "--file", help="Path to a text file containing multiple targets (one per line).")
	
	ai_group = parser.add_argument_group(f'{Colors.YELLOW}AI Intelligence & Output{Colors.RESET}')
	ai_group.add_argument("-m", "--model", choices=['chatgpt', 'gemini', 'claude'], required=True, help="Select the AI provider to power the analysis")
	ai_group.add_argument("-o", "--output", required=True, help="Filename for the initial AI report. \n"
		"Note: Final attack vectors will be saved in 'attacks_vectors.md' inside the report folder.")
	ai_group.add_argument("-v", "--verbose", action="store_true", help="Enable real-time logging. Displays raw tool outputs and internal workflow steps.")
	
	return parser.parse_args()

def load_config(config_path):
	"""Loads the tools and their instructions from a YAML configuration file"""
	
	if not os.path.exists(config_path):
		print(f"{Colors.RED}[!] Error: Config file '{config_path}' not found.{Colors.RESET}")
		return default_tools
	
	try:
		with open(config_path, 'r') as file:
			config = yaml.safe_load(file)
		
		if config and 'tools' in config:
			tools_dict = {}
			for item in config['tools']:
				name = str(item.get('name', '')).lower()
				command = str(item.get('command', ''))
				if name and command:
					tools_dict[name] = command
			
			print(f"{Colors.GREEN}[+] Configuration loaded successfully. {len(tools_dict)} dynamic tools activated{Colors.RESET}")
			return tools_dict
		
		else:
			return {}
	except Exception as e:
		print(f"{Colors.RED}[-] Error loading config file: {e}{Colors.RESET}")
		return {}


def run_nmap_scan(target, verbose):
	
	"""
	Executes an Nmap scan against the specified target to the profile the asset.
	Uses -sV (version), -sC (Default scripts), -O (OS Detection), and -Pn (Skip Ping).
	Return the scan output as a string.
	"""
	
	print(f"{Colors.CYAN}[*] Starting Phase 1: Initial Nmap scan for target {target}...{Colors.RESET}")
		
	command = ["nmap", "-sV", "-sC", "-O", "-Pn", "-T4", target]
	
	print(f"{Colors.ORANGE}[*] Executing: {' '.join(command)}{Colors.RESET}")
		
	try:
		result = subprocess.run(command, capture_output=True, text=True, check=True)
		if verbose:
			print(f"{Colors.GREEN}[+] Nmap scan successfully completed for {target}{Colors.RESET}")
		return result.stdout

	except subprocess.CalledProcess as e:
		print(f"{Colors.RED}[-] Nmap execution failed for {target}. Error code: {e.returncode}{Colors.RESET}")
		print(f"{Colors.RED}[-] Error details: {e.stderr}{Colors.RESET}")
		return None
	except FileNotFoundError:
		print(f"{Colors.RED}[-] Nmap is not installed or not found in the system PATH. Please install it (e.g., sudo apt install nmap).{Colors.RESET}")
		sys.exit(1)



def save_raw_output(target, scan_data, verbose):
	"""Saves the raw Nmap output to a text file for record keeping and future AI processing."""
	filename = f"{target.replace('/', '_')}_nmap_raw.txt"
	
	try:
		with open(filename, 'w') as f:
			f.write(scan_data)
		if verbose:
			print(f"{Colors.GREEN}[[+] Raw Nmap output saved to: {filename}{Colors.RESET}")
		return filename
	except Exception as e:
		print(f"{Colors.RED}[-] Error saving raw output for {target}: {e}{Colors.RESET}")
		return None

def call_ai_model(model_choice, full_prompt, api_key):
	"""Centralized function to call the selected AI API"""
	
	try:
		if model_choice == 'gemini':	
			client = genai.Client(api_key=api_key)
			response = client.models.generate_content(
				model='gemini-2.5-flash',
				contents=full_prompt
			)
			return response.text
			
		elif model_choice == 'chatgpt':
			client = OpenAI(api_key=api_key)
			response = client.chat.completions.create(
				model="gpt-3.5-turbo",
				messages=[
					{"role": "system", "content": "You are an expert penetration tester."},
					{"role": "user", "content": full_prompt}
				]
			)
			return response.choices[0].message.content
			
		elif model_choice == 'claude':
			client = anthropic.Anthropic(api_key=api_key)
			message = client.messages.create(
				model="claude-haiku-4-5",
				max_tokens=2048,
				system="You are an expert penetration tester and offensive cybersecurity analyst.",
				messages=[
					{"role": "user", "content": full_prompt}
				]
			)
			return message.content[0].text

	except Exception as e:
		print(f"{Colors.RED}[-] AI Call failed using {model_choice.upper()}: {str(e)}{Colors.RESET}")
		return None

def analyze_with_ai(model_choice, scan_data, verbose, api_key):
	"""Sends the Nmap output to the selected AI model to generate attack vectors."""
	
	print(f"{Colors.CYAN}[*] Starting Phase 2: Analyzing data with {model_choice.upper()}...{Colors.RESET}")
	
	system_prompt = """
	You are an expert penetration tester and offensive cybersecurity analyst.
	Analyze the following raw Nmap scan output.
	Identify exposed services, potential misconfigurations, and specific vulnerabilities.
	Based on the findings, define viable attack vectors.
	If you suggest tools like dig, dirbuster, gobuster, nikto, or sqlmap, ALWAYS provide the exact command line enclosed in ```bash code blocks.
	Format your response in clear Markdown.
	
	
	Nmap Scan Data:
	"""
	
	full_prompt = system_prompt + scan_data
	return call_ai_model(model_choice, full_prompt, api_key)
	

def second_scan(ai_report, target, report_dir, verbose, tools_dict):
	"""
	Phase 3: Extracts and executes specific tool commands from the AI's markdown report.
	Filters for tools: dig, dirbuster, gobuster, nikto, sqlmap, hydra, searchspoit, dirb.
	Returns the path to the Phase 3 log file.
	"""
	
	print(f"\n{Colors.CYAN}[*] Starting Phase 3: Extracting secondary attack vectors from AI Report...{Colors.RESET}")
	
	#Extract only the keys (tool names) from the dictionary
	extracted_commands = []
	allowed_tools = ('dig', 'dirbuster', 'gobuster', 'nikto', 'sqlmap', 'hydra', 'searchsploit', 'dirb')
	
		
	block_commands = re.findall(r'```[a-zA-Z]*\n(.*?)```', ai_report, re.DOTALL)
	inline_commands = re.findall(r'`([^`]+)`', ai_report)
	
	all_potential_lines = []
	for block in block_commands:
		all_potential_lines.extend(block.splitlines())
	all_potential_lines.extend(inline_commands)
	all_potential_lines.extend(ai_report.splitlines())
	
	for line in all_potential_lines:
		clean_line = re.sub(r'^[\-\*\$\>]\s+', '', line.strip()).strip()
		if not clean_line or clean_line.startswith('#'):
			continue
	
		first_word = clean_line.split()[0].lower()
		if first_word in allowed_tools:
			cmd = clean_line.replace("<TARGET_IP>", target)
			if cmd not in extracted_commands:
				extracted_commands.append(cmd)
	
	for tool_name, yaml_command in tools_dict.items():
		cmd = yaml_command.replace("<TARGET_IP>", target)
		if cmd not in extracted_commands:
			extracted_commands.append(cmd)
			
	phase3_log = os.path.join(report_dir, f"{target.replace('/','_')}_phase3_results.txt")
						
	if not extracted_commands:
		print(f"{Colors.RED}[-] No specific Phase 3 tools found in the AI report. {Colors.RESET}")
	
		with open(phase3_log, 'w') as f:
			f.write("No secondary tools were extracted or executed in Phase 3.\n")
		return phase3_log

	print(f"{Colors.GREEN}[+] Found {len(extracted_commands)} executable commands for Phase 3{Colors.RESET}")

	with open(phase3_log, 'w') as log_file:
		log_file.write(F"=== Phase 3 Execution Results for {target} ===\n\n")
		
		for cmd in extracted_commands:
			print(f"{Colors.ORANGE}\n[+] Executing: {cmd}\n{Colors.RESET}")
			log_file.write(f"[*] Command: {cmd}\n")
			log_file.write("-" * 40 + "\n")
			
			try:
				result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
				
				if verbose:
					preview = '\n'.join(result.stdout.split('\n')[:5])
					print(preview + "\n[...] Output truncated. See log file")
					
				log_file.write(result.stdout)
				if result.stderr:
					log_file.write("\n[ERRORS/WARNINGS]:\n" + result.stderr)
					
			except subprocess.TimeoutExpired:
				print(f"{Colors.RED}[-] Command timeout after 5 minutes{Colors.RESET}")
				log_file.write("[-] Execution timed out\n")
			except Exception as e:
				print(f"{Colors.RED}[-] Execution failed: {e}{Colors.RESET}")
				log_file.write(f"[-] Error: {e}\n")
			
			log_file.write("\n\n")
	
	print(f"{Colors.GREEN}\n[+] Phase 3 completed. Results saved to {phase3_log}{Colors.RESET}")
	return phase3_log


def final_analysis_report(model_choices, target, nmap_data, phase3_log, report_dir, verbose, api_key):
	"""
	Phases 4 and 5: Correlates Nmap data with Phase 3 execution results to model
	final attack vectors and writes them to attacks_vectors.md
	"""
	
	print(f"\n{Colors.CYAN}[*] Starting Phase 4: Correlating data and modeling attack vectors with {model_choices.upper()}...{Colors.RESET}")
	
	try:
		with open(phase3_log, 'r') as f:
			phase3_data = f.read()
	except Exception as e:
		phase3_data = f"Could not read Phase 3 results: {e}"
		
	system_prompt = f"""
	You are a Master Penetration Tester. I am providing you with the intelligence from two phases of s security assessment against target {target}:
		1. The initial Nmap port scan.
		2. The exact terminal output from secondary enumeration tools (line Nikto, Gobuster, Searchsplit, etc.) that were launched based on the initial scan.
		
		YOUR TASK:
		Correlate the findings from both sources to model a highly concrete, step-by-step Attack Vector to compromise the system.
		- Identify the "low-hanging fruit" or the most critical vulnerability confirmed by the Phase 3 logs.
		- Provide the exact exploitation commands or Metasploit module configuration required to gain access.
		- If credentials were found or vulnerabilities confirmed, prioritize those paths.
		- Details brief post-exploitation steps (e.g., privilege escalation checks) once access is gained.
		
		Format your entire response in professional Markdown.
		
		======================================
		SOURCE 1: INITIAL NMAP SCAN
		======================================
		{nmap_data}
		

		======================================
		SOURCE 2: PHASE 3 ENUMERATION LOGS
		======================================
		{phase3_data}

		"""
		
	ai_final_report = call_ai_model(model_choices, system_prompt, api_key)
		
	if ai_final_report:
		print(f"{Colors.CYAN}[*] Starting Phase 5: Generating final attack vectors report...{Colors.RESET}")
		final_report_path = os.path.join(report_dir, "attacks_vectors.md")
			
		with open(final_report_path, 'a') as f:
			f.write(f"#Final Attack Vector modeling for Target: {target}\n\n")
			f.write(ai_final_report)
			f.write("\n\n---\n\n")

		print(f"{Colors.GREEN}[+] Final attack vectors successfully generated and saved to: {final_report_path}{Colors.RESET}")
	
	else:
		print(f"{Colors.RED}[-] Failed to generate Phase 5 final report{Colors.RESET}")


def main():
	initial_banner()
	
	args = get_arguments()
	
	#Load Dynamic Tools an their instructions from YAML
	tools_dict = load_config(args.config)
	
	
	#Create a specific directory for the selected AI model's reports
	report_dir = f"reports_{args.model}"
	os.makedirs(report_dir, exist_ok=True)
	final_output_path = os.path.join(report_dir, args.output)
	
	
	api_key = ""
	print(f"{Colors.YELLOW}[*] Setting up credentials for {args.model.upper()}...{Colors.RESET}")
	if args.model == 'gemini':
		api_key = getpass.getpass(prompt="[?] Please enter your Gemini API Key: ")
	elif args.model == 'chatgpt':
		api_key = getpass.getpass(prompt="[?] Please enter your OpenAI API Key: ")
	elif args.model == 'claude':
		api_key = getpass.getpass(prompt="[?] Please enter your Anthropic API Key: ")
	
	if args.verbose:
		print(f"{Colors.GREEN}[+] Starting framework with verbose mode enabled...{Colors.RESET}")
		print(f"{Colors.GREEN}[+] Selected AI model: {args.model.upper()}{Colors.RESET}")
		print(f"{Colors.GREEN}[+] Configuration file: {args.config}{Colors.RESET}")
		print(f"{Colors.GREEN}[+] Output directory created/verified: {report_dir}/{Colors.RESET}")
		
	#Logic to determine the target
	targets = []
	if args.target:
			targets.append(args.target)
			if args.verbose:
				print(f"{Colors.GREEN}[+] Loading individual asset: {args.target}{Colors.RESET}")
	
	elif args.file:
		if args.verbose:
			print(f"{Colors.GREEN}[+] Loading multiple assets from file: {args.file}{Colors.RESET}")
			
		try:
			with open(args.file, 'r') as f:
				targets = [line.strip() for line in f if line.strip()]
			print (f"{Colors.GREEN}[+] Total assets loaded from file: {len(targets)}{Colors.RESET}")
		except FileNotFoundError:
			print (f"{Colors.RED}[-] Error: The file '{args.file}' was not found{Colors.RESET}")
			sys.exit(1) 
		
	#Execute the 5 phases for each target	
	for target in targets:
		
		#Phase 1: Nmap
		scan_output = run_nmap_scan(target, args.verbose)
		
		if scan_output:		
			save_raw_output(target, scan_output, args.verbose)
			print(f"{Colors.GREEN}[+] Phase 1 completed. Ready to send data to the AI model.{Colors.RESET}")
			
			#Phase 2: AI Analysis
			ai_report = analyze_with_ai(args.model, scan_output, args.verbose, api_key)
			
			if ai_report:
				print(F"{Colors.GREEN}[+] AI Analysis complete. Writing to final report...{Colors.RESET}")
					
				#Append to the final markdown output file
				with open(final_output_path, 'a') as report_file:
					report_file.write(f"# Analysis for Target: {target}\n\n")
					report_file.write(ai_report)
					report_file.write("\n\n---\n\n")
			
				print(f"{Colors.GREEN}[+] Initial attack vectors appended to {final_output_path}{Colors.RESET}")
			
				#Phase 3: Extraction and Execution
				phase3_log_path = second_scan(ai_report, target, report_dir, args.verbose, tools_dict)
				
				
				#Phase 4 & 5: Correlation and Final Report
				final_analysis_report(args.model, target, scan_output, phase3_log_path, report_dir, args.verbose, api_key)
				
	
if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		print(f"{Colors.RED}\n Execution interrupted by the user. Exiting...{Colors.RESET}")
		sys.exit(1)
