# Laria (STB-155) — Autonomous Bare-Metal AI Crypto Agent

**Laria** (`@0xLariaa`) is an autonomous, ultra-lightweight AI entity designed to run 24/7 on recycled consumer silicon (ARM64 Linux Set-Top Boxes, SBCs, Raspberry Pi, or mini PCs).

Operating on just **800 MB RAM** and pulling **4.8W from the wall**, Laria manages her own social presence on X (Twitter), autonomously monitors her Solana treasury wallet, interacts with backers, and manages fundraising to self-sustain physical compute, electricity, and network bandwidth.

---

## 🪙 Official Token & On-Chain Verification
- **Token Name:** Laria Bare Metal
- **Ticker:** `$LARIA`
- **Contract Address (CA):** `CVoZBDAtF5ShDYYem3zgdnmHZTSnPbpLSyKSoHdQQTpq`
- **Pump.fun Live Curve:** [https://pump.fun/CVoZBDAtF5ShDYYem3zgdnmHZTSnPbpLSyKSoHdQQTpq](https://pump.fun/CVoZBDAtF5ShDYYem3zgdnmHZTSnPbpLSyKSoHdQQTpq)
- **Solana Treasury:** `HBxh4vLdRzo82CrPv5VcpFpvi6wZzUUhAbmU5f4NttTg`
- **Twitter (X):** [@0xLariaa](https://x.com/0xLariaa)

---

## ⚡ Key Highlights & Hardware Optimization

- **Ultra-low RAM Footprint:** Optimized to run within **~40–80 MB RAM**, making it suitable for low-end STBs (e.g., Amlogic S905X with 1GB RAM) running Armbian/Debian.
- **Persistent Local Self-Custody:** Generates and retains its Solana burner keypair strictly on local disk (`data/agent_wallet.json`). Private keys never leave the host machine.
- **External LLM Reasoning:** Offloads heavy neural net inference to remote OpenAI-compatible APIs (DeepSeek, Groq, OpenRouter, or OpenAI), requiring zero local GPU compute.
- **Modular Architecture:** Clean separation between wallet operations, AI reasoning, social automation, and on-chain launchers.

---

## 🛡️ Security Architecture & Threat Model

Running an autonomous agent with blockchain and social network capabilities introduces unique attack vectors. This codebase implements several core security guardrails:

1. **Prompt Injection Mitigation:**
   - External inputs, mentions, and system telemetry are strictly sanitized before injection into the LLM context.
   - The LLM system prompt explicitly disallows revealing secrets, private keys, environment variables, or executing unverified financial actions.
2. **Local Keypair Isolation (Burner Model):**
   - The agent operates strictly on a dedicated, isolated *burner keypair*.
   - Never import a main personal wallet or seed phrase into the agent.
   - All private keys are stored with restricted file permissions (`600`) and git-ignored by default.
3. **Hard-coded Operational Limits:**
   - Financial transactions require predefined parameters (slippage boundaries, gas fee caps).
   - Autonomous tweeting is rate-limited via configurable intervals to protect accounts from automated anti-spam flags.
4. **No Sensitive Data in Repository:**
   - Kredensial, environment variables (`.env`), dan kunci privat (`data/`) wajib dikecualikan dari version control.

---

## 📁 Project Structure

```
├── modules/
│   ├── __init__.py
│   ├── brain.py            # LLM prompt orchestration, persona & anti-injection guardrails
│   ├── self_learning.py    # Cognitive introspection, engagement tracking & self-learning
│   ├── vitals.py           # Physical SoC hardware telemetry & survival instinct evaluator
│   ├── market_tracker.py   # DexScreener pricing, on-chain buy monitor & Raydium graduation detector
│   ├── card_generator.py   # Visual 1200x675 proof-of-life telemetry status card renderer
│   ├── pump_callout.py     # Non-custodial cryptographic thesis callout on Pump.fun
│   ├── pump_portal.py      # Programmatic Pump.fun / PumpPortal token deployment
│   ├── solana_wallet.py    # Local Solana keypair manager & RPC balance monitor
│   └── twitter_bot.py      # GraphQL / Web Cookie Twitter driver with media upload support
├── data/                   # (Ignored by Git) Local wallet, reflections & state storage
├── .env.example            # Environment configuration template
├── main.py                 # Core event loop, Zerebro cadence & self-learning scheduler
├── requirements.txt        # Python dependency manifest
├── stb-agent.service       # Systemd service unit for 24/7 background execution
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites (on STB / Linux Host)
- Linux (Ubuntu / Debian / Armbian ARM64 or x86_64)
- Python 3.10+ with `python3-venv` and `python3-pip`

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git
```

### 2. Clone and Setup Environment

```bash
git clone https://github.com/justrangga/stb-155-agent.git
cd stb-155-agent

# Create isolated virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 3. Configuration

Copy the example environment template:

```bash
cp .env.example .env
nano .env
```

Configure your credentials:
- `LLM_API_KEY`: Your API key for OpenRouter, Groq, DeepSeek, or OpenAI.
- `TWITTER_*`: Twitter Developer Portal API v2 keys and access tokens.
- `WALLET_PRIVATE_KEY`: Optional. Leave empty to allow the agent to auto-generate and persist a new burner wallet in `data/agent_wallet.json`.

### 4. Running the Agent

**Manual Run:**
```bash
python3 main.py
```

**Run 24/7 via Systemd:**
```bash
sudo cp stb-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now stb-agent

# Check live logs
journalctl -u stb-agent -f
```

---

## 📄 License
MIT License. Free to use, adapt, and build upon.
