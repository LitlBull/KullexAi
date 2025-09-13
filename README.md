# KullexAi (`kull`)

KullexAi is an AI-powered CLI tool that acts like a Unix filter. It reads terminal output from stdin, echoes it to stdout, and appends an AI-generated section at the end. It is designed for log review, anomaly detection, and network scan analysis while following the KISS rule. It supports multiple providers (OpenAI, Anthropic, OpenRouter, Ollama, vLLM), can stream output with --stream, and scrubs API keys, tokens, and passwords before sending to providers. The modes are: -sum for summarization, -sol for solutions, -ser for deepsearch, and -scan for network scan analysis.

Features:
- **Pluggable providers**: OpenAI, Anthropic, OpenRouter, or local backends (Ollama, vLLM).
- **Streaming support**: live Server-Sent Event (SSE) output with `--stream`.
- **Redaction**: basic scrubbing of API keys, tokens, and passwords before sending to providers.
- **Modes**:
  - `-sum` → Summarize logs/scans
  - `-sol` → Suggest solutions and fixes
  - `-ser` → Deepsearch (clusters + anomalies)
  - `-scan` → Network scan analysis (nmap, masscan, etc.)
  - `-exp` → Provide an explanation of contents.

Thanks to PEP668, you will need to be in a VENV.

Use: python3 -m vent/path/to/venv Then: source /path/to/venv/bin/activate

run "pip install -e ." from the root folder.

if your using Ollama or vLLM, you should try to already have it installed with the model of your choosing, I'm using ollama with mistral:7b pulled, before running "kull init" to enter the setup wizard.

I recommend using "--stream" with your commands unless you're specifying an output file. 

To install, clone the repository, change into the project directory, and install with pip:

git clone https://github.com/yourname/kullexai.git  
cd kullexai  
pip install -e .  

You can also install with pipx:  

pipx install .  

Once installed, run the init wizard:  

kull init  

You will be prompted to choose between Ollama (local CPU/GPU models), vLLM (local GPU inference server), or a cloud API (OpenAI, Anthropic, OpenRouter). If you choose a cloud API, export your API key into the environment, for example with OpenAI:  

export OPENAI_API_KEY=sk-...  

Your configuration will be saved at ~/.config/kullexai/config.toml.  

Example commands you can run:  

``` BASH

journalctl -u ssh -n 300 | kull -sum --stream 

#-sum tells KullexAi: “summarize this.”

#--stream makes it print the summary live, as the AI types it out. Without --stream, it would stay quiet until the full summary is ready, then dump it all at once.`

dmesg | tail -n 200 | kull -sum

#Summarizes the last 200 kernel log messages.  

cat /var/log/kern.log | grep -i "warn" | kull -sum

#Filters kernel logs for warnings and summarizes them.  

journalctl -u apache2 -n 200 | kull -sol  

#Analyzes the last 200 Apache service logs and suggests solutions.  

dmesg | grep -i ext4 | kull -sol  

#Searches kernel logs for EXT4 filesystem errors and proposes fixes.  

journalctl -xe | kull -ser --stream  

#Deepsearch of system logs for anomalies, clusters, and metrics. Streams the results live.  

grep "Failed password" /var/log/auth.log | kull -ser  

#Analyzes failed SSH login attempts, clustering repeated events.  

grep "error" /var/log/syslog | tail -n 500 | kull -ser -o errors.md  

#Finds errors in syslog, analyzes the last 500 lines, and writes results to `errors.md`.  

nmap -sV -p- 192.168.1.10 | kull -scan  

#Scans all ports on host 192.168.1.10 with service/version detection, then analyzes with KullexAi.  

masscan 192.168.1.0/24 -p22,80,443 --rate=1000 | kull -scan  

#Performs a fast masscan across the subnet for ports 22, 80, and 443, then analyzes the results.  
