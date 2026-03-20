"""Setup wizard for podcast-agent."""

import shutil
import subprocess
import platform
import sys
from pathlib import Path
from dotenv import dotenv_values


def get_package_manager():
    """Detect Linux distro and return package manager commands."""
    system = platform.system().lower()
    if system == "darwin":
        return "brew install"
    elif system == "linux":
        # Check /etc/os-release
        try:
            with open("/etc/os-release") as f:
                content = f.read().lower()
                if "ubuntu" in content or "debian" in content:
                    return "sudo apt install"
                elif "centos" in content or "rhel" in content or "fedora" in content:
                    return "sudo yum install"
                elif "arch" in content:
                    return "sudo pacman -S"
        except:
            pass
        return "sudo apt install"  # default for unknown Linux
    return None


def check_dependencies():
    """Check and install missing dependencies."""
    print("\nStep 1: Checking Dependencies")
    required = ["yt-dlp", "ffmpeg", "tmux"]
    missing = []
    for tool in required:
        if not shutil.which(tool):
            missing.append(tool)

    if not missing:
        print("  ✓ All dependencies found")
        return

    pkg_mgr = get_package_manager()
    if pkg_mgr:
        cmd = f"{pkg_mgr} {' '.join(missing)}"
        print(f"  Missing: {', '.join(missing)}")
        print(f"  Install with: {cmd}")
        if input(f"  Run installation? [y/N]: ").lower() == "y":
            subprocess.run(cmd, shell=True, check=True)
            print("  ✓ Installation complete")


# ========================================
# Step 2: Choose Transcription Provider
# ========================================
def choose_transcription_provider():
    """Let user choose between local and cloud transcription."""
    print("\nStep 2: Transcription Provider")
    print("  [1] whispercpp - Local (fast, no API cost, needs Whisper.cpp)")
    print("  [2] siliconflow - Cloud API (fast, needs SILICONFLOW_API_KEY)")
    print("  [3] openai - Cloud API (needs OPENAI_API_KEY)")
    choice = input("\nSelect [1]: ").strip() or "1"

    if choice == "1":
        return setup_whispercpp()
    elif choice == "2":
        return "siliconflow", None
    elif choice == "3":
        return "openai", None


def setup_whispercpp():
    """Configure Whisper.cpp local transcription."""
    print("\n  Configuring Whisper.cpp...")

    cli_path = Path(input(
        "  CLI path [~/Desktop/whisper.cpp/build/bin/whisper-cli]: "
    ).strip() or "~/Desktop/whisper.cpp/build/bin/whisper-cli").expanduser()

    model_path = Path(input(
        "  Model path [~/Desktop/whisper.cpp/models/ggml-medium.bin]: "
    ).strip() or "~/Desktop/whisper.cpp/models/ggml-medium.bin").expanduser()

    # Offer to download model if missing
    if not model_path.exists():
        print(f"\n  Model not found: {model_path}")
        if input("  Download ggml-medium.bin (1.5GB)? [y/N]: ").lower() == "y":
            download_model(model_path)

    if not cli_path.exists():
        print(f"\n  ERROR: whisper-cli not found at {cli_path}")
        print("  Build with: cd ~/Desktop/whisper.cpp && mkdir build && cd build && cmake .. && make whisper-cli")
        sys.exit(1)

    return "whispercpp", {"cli_path": cli_path, "model_path": model_path}


def download_model(model_path):
    """Download ggml-medium.bin from HuggingFace."""
    model_path.parent.mkdir(parents=True, exist_ok=True)
    url = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin"
    print(f"  Downloading to {model_path}...")
    subprocess.run(["curl", "-L", "-o", str(model_path), url], check=True)
    print("  ✓ Download complete")


# ========================================
# Step 3: Configure LLM Provider + API Keys
# ========================================
LLM_PROVIDERS = {
    "1": ("minimax", "ANTHROPIC_API_KEY", "MiniMax Token Plan"),
    "2": ("siliconflow", "SILICONFLOW_API_KEY", "SiliconFlow"),
    "3": ("deepseek", "DEEPSEEK_API_KEY", "DeepSeek"),
    "4": ("openai", "OPENAI_API_KEY", "OpenAI"),
    "5": ("qwen", "DASHSCOPE_API_KEY", "Qwen"),
}


def configure_llm():
    """Configure LLM provider and API key (mandatory)."""
    print("\nStep 3: LLM Provider (Required)")
    print("  Select LLM Provider:")
    for k, (name, _, desc) in LLM_PROVIDERS.items():
        print(f"  [{k}] {name} - {desc}")

    choice = input("\nSelect [1]: ").strip() or "1"
    provider_name, key_env, _ = LLM_PROVIDERS.get(choice, LLM_PROVIDERS["1"])

    api_key = input(f"  Enter API Key for {provider_name} ({key_env}): ").strip()
    if not api_key:
        print("  ERROR: API key is required")
        sys.exit(1)

    return provider_name, {key_env: api_key}


# ========================================
# Step 4: Write Config Files
# ========================================
def write_configs(trans_provider, trans_config, llm_provider, api_keys):
    """Write ~/.api_keys and ~/.llm_providers."""
    # Write ~/.api_keys
    api_keys_file = Path.home() / ".api_keys"
    existing = dotenv_values(api_keys_file) if api_keys_file.exists() else {}

    # Preserve existing keys, update with new
    all_keys = {**existing, **api_keys}
    with open(api_keys_file, "w") as f:
        for key, value in all_keys.items():
            if value:  # Don't write empty values
                f.write(f"{key}={value}\n")

    # Write ~/.llm_providers
    llm_providers_file = Path.home() / ".llm_providers"
    lines = [
        "# Provider Configuration\n",
        f"LLM_PROVIDER={llm_provider}\n",
        f"TRANSCRIPTION_PROVIDER={trans_provider}\n",
    ]
    if trans_provider == "whispercpp" and trans_config:
        lines.append(f"WHISPERCPP_CLI_PATH={trans_config['cli_path']}\n")
        lines.append(f"WHISPERCPP_MODEL_PATH={trans_config['model_path']}\n")

    with open(llm_providers_file, "w") as f:
        f.writelines(lines)

    print(f"\n  ✓ ~/.api_keys updated")
    print(f"  ✓ ~/.llm_providers updated")


# ========================================
# Step 5: Test Configuration
# ========================================
def test_configuration():
    """Run a simple test."""
    print("\nStep 5: Testing...")
    # Simple test: just verify config loads
    from podcast_agent.config import Config
    from podcast_agent.providers import get_llm_provider_name
    config = Config.load()
    print(f"  ✓ Config loaded successfully")
    print(f"  LLM Provider: {get_llm_provider_name()}")
    print(f"  Transcription: {config.transcription_provider}")


# ========================================
# Main
# ========================================
def main():
    print("=" * 40)
    print("    Podcast Agent Setup Wizard")
    print("=" * 40)

    check_dependencies()
    trans_provider, trans_config = choose_transcription_provider()
    llm_provider, api_keys = configure_llm()
    write_configs(trans_provider, trans_config, llm_provider, api_keys)
    test_configuration()

    print("\n" + "=" * 40)
    print("    Setup Complete!")
    print("=" * 40)
