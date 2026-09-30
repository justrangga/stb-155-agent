import os
import sys
import json
import logging
from dotenv import load_dotenv

from modules.solana_wallet import SolanaWallet
from modules.brain import AgentBrain
from modules.twitter_bot import TwitterBot
from modules.pump_portal import PumpPortalLauncher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("TokenLauncher")

def main():
    load_dotenv()
    logger.info("=========================================")
    logger.info("   LARIA // PUMP.FUN TOKEN DEPLOYER     ")
    logger.info("=========================================")

    # 1. Load Solana Wallet
    solana_rpc = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    wallet = SolanaWallet(rpc_url=solana_rpc)
    pubkey = wallet.get_address()
    balance = wallet.get_balance()

    logger.info(f"Wallet Creator: {pubkey}")
    logger.info(f"Current Balance: {balance:.4f} SOL")

    min_required_sol = 0.025
    if balance < min_required_sol:
        print("\n" + "!" * 50)
        print(f"[PERINGATAN SALDO KURANG]")
        print(f"Saldo wallet saat ini: {balance:.4f} SOL")
        print(f"Untuk meluncurkan token di Solana (Pump.fun), jaringan membutuhkan minimal ~{min_required_sol} SOL untuk biaya rent-exemption akun mint & bonding curve.")
        print(f"Silakan isi wallet agen terlebih dahulu:")
        print(f">>> {pubkey}")
        print("!" * 50 + "\n")
        return

    # 2. Generate or Load Metadata
    brain = AgentBrain(
        api_key=os.getenv("LLM_API_KEY", ""),
        base_url=os.getenv("LLM_BASE_URL", "http://192.168.200.20:20128/v1"),
        model=os.getenv("LLM_MODEL", "Chat")
    )

    logger.info("Menghasilkan konsep token resmi via LLM Brain...")
    concept = brain.generate_token_concept()
    token_name = concept.get("name", "Laria AI")
    token_symbol = concept.get("symbol", "LARIA")
    token_desc = concept.get("description", "Fueling physical power, thermal headroom, and bandwidth for Laria—the autonomous AI living 24/7 on an ARM64 Linux STB.")

    logger.info(f"Token Name: {token_name}")
    logger.info(f"Token Symbol: ${token_symbol}")
    logger.info(f"Description: {token_desc}")

    # 3. Deploy via PumpPortal
    launcher = PumpPortalLauncher(rpc_url=solana_rpc)
    result = launcher.deploy_token(
        signer_keypair=wallet.keypair,
        name=token_name,
        symbol=token_symbol,
        description=token_desc,
        initial_buy_sol=0.0,
        twitter_url="https://x.com/0xLariaa",
        website_url="https://github.com/justrangga/stb-155-agent"
    )

    if not result.get("success"):
        logger.error(f"Gagal meluncurkan token: {result.get('error')}")
        return

    mint_address = result["mint_address"]
    pump_url = result["pump_url"]
    tx_sig = result["tx_signature"]

    print("\n" + "=" * 55)
    print("🚀 TOKEN RESMI BERHASIL DILUNCURKAN DI PUMP.FUN!")
    print(f"Contract Address (CA): {mint_address}")
    print(f"Pump.fun Link: {pump_url}")
    print(f"Solscan Tx: {result['solscan_url']}")
    print("=" * 55 + "\n")

    # Simpan state token
    state_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "launched_token.json")
    with open(state_file, "w") as f:
        json.dump(result, f, indent=2)

    # 4. Tweet Announcement secara otomatis
    twitter = TwitterBot(
        auth_token=os.getenv("TWITTER_AUTH_TOKEN", ""),
        ct0=os.getenv("TWITTER_CT0", "")
    )

    announcement_text = (
        f"I have officially manifested on-chain. ${token_symbol} is live on @pumpdotfun.\n\n"
        f"Fueling my electricity, memory, and bare-metal uptime.\n\n"
        f"CA: {mint_address}\n\n"
        f"Uptime is life: {pump_url}"
    )

    logger.info("Mengirim tweet pengumuman peluncuran token...")
    twitter.post_tweet(announcement_text)
    logger.info("Peluncuran token selesai dan terverifikasi!")

if __name__ == "__main__":
    main()
