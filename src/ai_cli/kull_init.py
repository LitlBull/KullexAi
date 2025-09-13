from __future__ import annotations
import os
import sys
import subprocess
from pathlib import Path
from .config import CONFIG_DIR, CONFIG_PATH, DEFAULTS

# ---------- helpers ----------

def detect_distro() -> str:
    p = Path("/etc/os-release")
    if p.exists():
        data = p.read_text(encoding="utf-8", errors="ignore")
        for line in data.splitlines():
            if line.startswith("ID="):
                return line[3:].strip().strip('"').lower()
            if line.startswith("ID_LIKE="):
                return line[8:].strip().strip('"').lower()
    elif Path("/etc/lsb-release").exists():
        return "debian/ubuntu"
    if Path("/etc/debian_version").exists():
        return "debian/ubuntu"
    if Path("/etc/redhat-release").exists():
        return "redhat/centos/fedora"
    if Path("/etc/arch-release").exists():
        return "arch"
    if Path("/etc/alpine-release").exists():
        return "alpine"
    return "unknown"

def check_command(cmd: str) -> bool:
    """Check if a command exists in PATH"""
    try:
        subprocess.run(["which", cmd], capture_output=True, check=True)
        return True
    except:
        return False

def check_ollama() -> bool:
    """Check if Ollama is installed and running"""
    if not check_command("ollama"):
        return False
    try:
        r = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        return r.returncode == 0
    except:
        return False

def check_vllm_server(url: str = "http://localhost:8000") -> bool:
    """Check if vLLM server is accessible"""
    try:
        import requests
        r = requests.get(f"{url}/health", timeout=2)
        return r.status_code == 200
    except:
        return False

def get_ollama_models() -> list[str]:
    """Get list of installed Ollama models"""
    try:
        r = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if r.returncode != 0:
            return []
        models = []
        for line in r.stdout.splitlines()[1:]:  # Skip header
            if line.strip():
                model_name = line.split()[0]
                models.append(model_name)
        return models
    except:
        return []

def write_config(provider: str, model: str, endpoint: str = "", **kwargs) -> None:
    """Write configuration to TOML file"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    config_lines = [
        "# KullexAi Configuration",
        f"provider = \"{provider}\"",
        f"model = \"{model}\"",
    ]
    
    if endpoint:
        config_lines.append(f"endpoint = \"{endpoint}\"")
    
    config_lines.extend([
        f"window_bytes = {kwargs.get('window_bytes', DEFAULTS['window_bytes'])}",
        f"max_tokens = {kwargs.get('max_tokens', DEFAULTS['max_tokens'])}",
        f"redact = \"{kwargs.get('redact', DEFAULTS['redact'])}\"",
    ])
    
    CONFIG_PATH.write_text("\n".join(config_lines) + "\n", encoding="utf-8")
    print(f"\n✓ Configuration saved to {CONFIG_PATH}")

def run_init():
    """Interactive setup wizard for KullexAi"""
    print("\n" + "="*50)
    print("     KullexAi Setup Wizard")
    print("="*50)
    
    # Detect system
    distro = detect_distro()
    print(f"\nDetected system: {distro}")
    
    # Provider selection
    print("\nSelect AI provider:")
    print("1. Ollama (local, CPU/GPU)")
    print("2. vLLM (local, GPU inference server)")
    print("3. OpenAI (cloud)")
    print("4. Anthropic (cloud)")
    print("5. OpenRouter (cloud, multiple models)")
    
    while True:
        choice = input("\nEnter choice (1-5): ").strip()
        if choice in ["1", "2", "3", "4", "5"]:
            break
        print("Invalid choice. Please enter 1-5.")
    
    provider = ""
    model = ""
    endpoint = ""
    
    if choice == "1":  # Ollama
        provider = "ollama"
        print("\nChecking Ollama installation...")
        
        if not check_ollama():
            print("⚠ Ollama not found or not running!")
            print("\nTo install Ollama:")
            print("  curl -fsSL https://ollama.ai/install.sh | sh")
            print("  ollama serve  # Start the server")
            print("\nThen pull a model:")
            print("  ollama pull llama3.2")
            
            if input("\nContinue anyway? (y/n): ").lower() != "y":
                print("Setup cancelled.")
                return
        else:
            print("✓ Ollama is installed and running")
            
            models = get_ollama_models()
            if models:
                print(f"\nFound {len(models)} installed model(s):")
                for i, m in enumerate(models, 1):
                    print(f"  {i}. {m}")
                
                model_choice = input("\nSelect model number (or enter custom name): ").strip()
                try:
                    idx = int(model_choice) - 1
                    if 0 <= idx < len(models):
                        model = models[idx]
                    else:
                        model = model_choice
                except:
                    model = model_choice or "llama3.2"
            else:
                print("No models found. Suggested models:")
                print("  - llama3.2 (small, fast)")
                print("  - llama3.1:70b (large, powerful)")
                print("  - mistral (balanced)")
                model = input("\nEnter model name [llama3.2]: ").strip() or "llama3.2"
                print(f"\nPull this model with: ollama pull {model}")
        
        custom_endpoint = input("\nOllama endpoint [http://localhost:11434]: ").strip()
        if custom_endpoint:
            endpoint = custom_endpoint
    
    elif choice == "2":  # vLLM
        provider = "vllm"
        print("\nChecking vLLM server...")
        
        endpoint = input("vLLM server URL [http://localhost:8000/v1]: ").strip() or "http://localhost:8000/v1"
        
        if not check_vllm_server(endpoint.replace("/v1", "")):
            print("⚠ vLLM server not accessible!")
            print("\nTo start vLLM server:")
            print("  python -m vllm.entrypoints.openai.api_server \\")
            print("    --model <your-model> --port 8000")
            
            if input("\nContinue anyway? (y/n): ").lower() != "y":
                print("Setup cancelled.")
                return
        else:
            print("✓ vLLM server is accessible")
        
        model = input("Model name (as loaded in vLLM): ").strip()
        if not model:
            print("Model name is required for vLLM!")
            return
    
    elif choice == "3":  # OpenAI
        provider = "openai"
        print("\nOpenAI Setup")
        print("Models: gpt-4o-mini (cheap), gpt-4o (powerful)")
        
        model = input("Model [gpt-4o-mini]: ").strip() or "gpt-4o-mini"
        
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            print("\n⚠ OPENAI_API_KEY not found in environment!")
            print("Export it with: export OPENAI_API_KEY=sk-...")
            if input("\nContinue anyway? (y/n): ").lower() != "y":
                print("Setup cancelled.")
                return
        else:
            print("✓ OPENAI_API_KEY found")
    
    elif choice == "4":  # Anthropic
        provider = "anthropic"
        print("\nAnthropic Setup")
        print("Models: claude-3-haiku-20240307 (fast), claude-3-5-sonnet-20241022 (powerful)")
        
        model = input("Model [claude-3-haiku-20240307]: ").strip() or "claude-3-haiku-20240307"
        
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            print("\n⚠ ANTHROPIC_API_KEY not found in environment!")
            print("Export it with: export ANTHROPIC_API_KEY=...")
            if input("\nContinue anyway? (y/n): ").lower() != "y":
                print("Setup cancelled.")
                return
        else:
            print("✓ ANTHROPIC_API_KEY found")
    
    elif choice == "5":  # OpenRouter
        provider = "openrouter"
        print("\nOpenRouter Setup")
        print("Popular models:")
        print("  - google/gemini-flash-1.5-8b (very cheap)")
        print("  - anthropic/claude-3.5-sonnet (powerful)")
        print("  - openai/gpt-4o-mini (balanced)")
        
        model = input("Model [google/gemini-flash-1.5-8b]: ").strip() or "google/gemini-flash-1.5-8b"
        
        key = os.getenv("OPENROUTER_API_KEY")
        if not key:
            print("\n⚠ OPENROUTER_API_KEY not found in environment!")
            print("Get a key at: https://openrouter.ai/")
            print("Export it with: export OPENROUTER_API_KEY=...")
            if input("\nContinue anyway? (y/n): ").lower() != "y":
                print("Setup cancelled.")
                return
        else:
            print("✓ OPENROUTER_API_KEY found")
    
    # Advanced settings
    print("\n" + "-"*40)
    if input("Configure advanced settings? (y/n) [n]: ").lower() == "y":
        window = input(f"Max input bytes [{DEFAULTS['window_bytes']}]: ").strip()
        window_bytes = int(window) if window else DEFAULTS['window_bytes']
        
        tokens = input(f"Max output tokens [{DEFAULTS['max_tokens']}]: ").strip()
        max_tokens = int(tokens) if tokens else DEFAULTS['max_tokens']
        
        redact = input("Redaction mode (basic/off) [basic]: ").strip() or "basic"
    else:
        window_bytes = DEFAULTS['window_bytes']
        max_tokens = DEFAULTS['max_tokens']
        redact = DEFAULTS['redact']
    
    # Write config
    write_config(
        provider=provider,
        model=model,
        endpoint=endpoint,
        window_bytes=window_bytes,
        max_tokens=max_tokens,
        redact=redact
    )
    
    # Final instructions
    print("\n" + "="*50)
    print("Setup complete! You can now use KullexAi:")
    print("\nExamples:")
    print("  journalctl -xe | kull -sum")
    print("  dmesg | kull -sol")
    print("  nmap localhost | kull -scan")
    print("\nFor streaming output, add --stream")
    print("For help: kull --help")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_init()