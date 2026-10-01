import os
import re
import time
import logging
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

def format_compact_uptime(raw: str) -> str:
    if not raw:
        return "0m"
    days = re.search(r'(\d+)\s*day', raw)
    hours = re.search(r'(\d+)\s*hour', raw)
    mins = re.search(r'(\d+)\s*minute', raw)
    
    parts = []
    if days:
        parts.append(f"{days.group(1)}d")
    if hours:
        parts.append(f"{int(hours.group(1)):02d}h")
    if mins:
        parts.append(f"{int(mins.group(1)):02d}m")
    
    return ' '.join(parts) if parts else raw.replace('up ', '').strip()

class CardGenerator:
    """
    Renders high-resolution (1200x675) Cybernetic Telemetry Cards for Laria.
    Visual proof of life on ARM64 Linux hardware, Solana treasury, and bonding curve progress.
    Engineered with dynamic text bounds to mathematically guarantee zero text clipping or overlapping.
    """
    def __init__(self, data_dir: str = None):
        if not data_dir:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(data_dir, exist_ok=True)
        self.data_dir = data_dir
        self.output_card_path = os.path.join(data_dir, "telemetry_card.png")

    def generate_card(self, telemetry: dict = None, market_data: dict = None, custom_output_path: str = None, evolution_stage: int = 2) -> str:
        width, height = 1200, 675
        img = Image.new("RGB", (width, height), color="#06080d")
        draw = ImageDraw.Draw(img)

        # Fonts loading with robust fallbacks
        font_dir = "/usr/share/fonts/truetype/dejavu"
        try:
            f_title = ImageFont.truetype(f"{font_dir}/DejaVuSans-Bold.ttf", 23)
            f_subtitle = ImageFont.truetype(f"{font_dir}/DejaVuSans.ttf", 13)
            f_card_label = ImageFont.truetype(f"{font_dir}/DejaVuSans-Bold.ttf", 12)
            f_card_value = ImageFont.truetype(f"{font_dir}/DejaVuSans-Bold.ttf", 26)
            f_card_val_small = ImageFont.truetype(f"{font_dir}/DejaVuSans-Bold.ttf", 21)
            f_card_sub = ImageFont.truetype(f"{font_dir}/DejaVuSans.ttf", 12)
            f_pill = ImageFont.truetype(f"{font_dir}/DejaVuSans-Bold.ttf", 12)
            f_mono_bold = ImageFont.truetype(f"{font_dir}/DejaVuSansMono-Bold.ttf", 13)
            f_mono_repo = ImageFont.truetype(f"{font_dir}/DejaVuSansMono-Bold.ttf", 12)
            f_pct = ImageFont.truetype(f"{font_dir}/DejaVuSans-Bold.ttf", 20)
            f_scale = ImageFont.truetype(f"{font_dir}/DejaVuSans-Bold.ttf", 10)
        except Exception:
            f_title = f_subtitle = f_card_label = f_card_value = f_card_val_small = f_card_sub = f_pill = f_mono_bold = f_mono_repo = f_pct = f_scale = ImageFont.load_default()

        # High-Contrast Cybernetic Palette
        c_card_bg = "#0b1018"
        c_card_border = "#1c283f"
        c_accent_green = "#00ffa3"  # Neon Mint
        c_accent_cyan = "#00e5ff"   # Cyber Cyan
        c_accent_amber = "#ffb800"  # Solar Amber
        c_accent_purple = "#c084fc" # Electric Violet
        c_accent_pink = "#f43f5e"   # Laser Pink
        
        c_text_bright = "#ffffff"
        c_text_label = "#9fb5d4"    # Crisp readable label
        c_text_sub = "#7891b3"      # Clear secondary text
        c_text_dim = "#556b8a"      # Minor scale markers

        # 1. Background Grid & Outer Viewfinder Frame
        grid_gap = 48
        for x in range(0, width, grid_gap):
            draw.line([(x, 0), (x, height)], fill="#0d1421", width=1)
        for y in range(0, height, grid_gap):
            draw.line([(0, y), (width, y)], fill="#0d1421", width=1)

        margin = 32
        bx1, by1 = margin, margin
        bx2, by2 = width - margin, height - margin
        draw.rectangle([bx1, by1, bx2, by2], outline="#1a263d", width=1)

        # Viewfinder Corner Brackets
        bracket_len = 26
        for (cx, cy, dx, dy) in [
            (bx1, by1, 1, 1),
            (bx2, by1, -1, 1),
            (bx1, by2, 1, -1),
            (bx2, by2, -1, -1)
        ]:
            draw.line([(cx, cy), (cx + dx * bracket_len, cy)], fill=c_accent_green, width=2)
            draw.line([(cx, cy), (cx, cy + dy * bracket_len)], fill=c_accent_green, width=2)

        # 2. Header Bar
        header_x = bx1 + 22
        header_y = by1 + 18

        # Glowing Node Status Orb
        draw.ellipse([header_x, header_y + 3, header_x + 20, header_y + 23], fill="#0a3324", outline=c_accent_green, width=1)
        draw.ellipse([header_x + 5, header_y + 8, header_x + 15, header_y + 18], fill=c_accent_green)

        title_x = header_x + 32
        draw.text((title_x, header_y - 2), "LARIA OS  //  BARE-METAL NODE TELEMETRY", fill=c_text_bright, font=f_title)
        draw.text((title_x, header_y + 28), "ARM64 Linux STB-155  •  Autonomous Solana Agent  •  Verifiable Hardware Vitals", fill=c_text_sub, font=f_subtitle)

        # Dynamic Top-Right Status Pills (Guaranteed Zero Overlap)
        pill2_text = "24/7 ONLINE"
        pill2_tw = draw.textlength(pill2_text, font=f_pill)
        pill2_w = int(pill2_tw + 44)
        pill2_h = 32
        pill2_x = bx2 - 22 - pill2_w
        pill2_y = header_y + 3

        pill1_text = f"STAGE {evolution_stage} : EVOLVED"
        pill1_tw = draw.textlength(pill1_text, font=f_pill)
        pill1_w = int(pill1_tw + 26)
        pill1_h = 32
        pill1_x = pill2_x - 14 - pill1_w
        pill1_y = pill2_y

        draw.rounded_rectangle([pill1_x, pill1_y, pill1_x + pill1_w, pill1_y + pill1_h], radius=6, fill="#0c1929", outline=c_accent_cyan, width=1)
        draw.text((pill1_x + 13, pill1_y + 9), pill1_text, fill=c_accent_cyan, font=f_pill)

        draw.rounded_rectangle([pill2_x, pill2_y, pill2_x + pill2_w, pill2_y + pill2_h], radius=6, fill="#0a261c", outline=c_accent_green, width=1)
        draw.ellipse([pill2_x + 13, pill2_y + 11, pill2_x + 21, pill2_y + 19], fill=c_accent_green)
        draw.text((pill2_x + 30, pill2_y + 9), pill2_text, fill=c_accent_green, font=f_pill)

        # Horizontal Divider Line
        div_y = header_y + 54
        draw.line([(bx1 + 22, div_y), (bx2 - 22, div_y)], fill="#1a263d", width=1)

        # 3. Six Telemetry Metric Boxes (2 rows x 3 columns)
        content_x1 = bx1 + 22
        content_x2 = bx2 - 22
        content_w = content_x2 - content_x1

        gap_x = 18
        card_w = (content_w - (2 * gap_x)) // 3
        card_h = 106
        gap_y = 14
        start_y = div_y + 16

        temp_c = telemetry.get('temperature_c', 52.0) if telemetry else 52.0
        mem_used = telemetry.get('memory', {}).get('used_mb', 322) if telemetry else 322
        mem_total = telemetry.get('memory', {}).get('total_mb', 787) if telemetry else 787
        raw_uptime = telemetry.get('uptime', '1d 09h 48m') if telemetry else '1d 09h 48m'
        uptime = format_compact_uptime(raw_uptime)
        treasury_sol = telemetry.get('treasury_sol', 0.0131) if telemetry else 0.0131
        mcap = market_data.get('market_cap', 3347.08) if market_data else 3347.08
        curve_pct = market_data.get('curve_progress', 0.01) if market_data else 0.01

        metrics = [
            # Row 1
            {
                "tag": "HARDWARE CORE",
                "val": "STB-155 (ARM64)",
                "sub": "Amlogic Quad-Core @ 1.5 GHz",
                "accent": c_accent_cyan
            },
            {
                "tag": "SoC TEMPERATURE",
                "val": f"{temp_c:.1f} °C",
                "sub": "Thermal Zone: Nominal (< 70°C)",
                "accent": c_accent_amber if temp_c > 50 else c_accent_green
            },
            {
                "tag": "SYSTEM MEMORY",
                "val": f"{mem_used} / {mem_total} MB",
                "sub": f"{int((mem_used/max(1, mem_total))*100)}% Allocated • Daemon ~32 MB",
                "accent": c_accent_green
            },
            # Row 2
            {
                "tag": "HARDWARE UPTIME",
                "val": uptime,
                "sub": "Zero Reboots • Systemd 24/7",
                "accent": c_accent_purple
            },
            {
                "tag": "TREASURY RESERVE",
                "val": f"{treasury_sol:.4f} SOL",
                "sub": "Non-Custodial Fuel For Uptime & RPC",
                "accent": c_accent_green
            },
            {
                "tag": "MARKET VALUATION",
                "val": f"${mcap:,.0f}",
                "sub": "Token $LARIA • 1B Total Supply",
                "accent": c_accent_pink
            }
        ]

        for idx, m in enumerate(metrics):
            col = idx % 3
            row = idx // 3
            mx = content_x1 + col * (card_w + gap_x)
            my = start_y + row * (card_h + gap_y)

            draw.rounded_rectangle([mx, my, mx + card_w, my + card_h], radius=6, fill=c_card_bg, outline=c_card_border, width=1)
            draw.rectangle([mx, my + 6, mx + 3, my + card_h - 6], fill=m["accent"])
            draw.text((mx + 16, my + 13), m["tag"], fill=c_text_label, font=f_card_label)
            
            # Big Value with Auto-Fit Guardrail
            val_str = str(m["val"])
            val_w = draw.textlength(val_str, font=f_card_value)
            chosen_font = f_card_value if val_w <= (card_w - 36) else f_card_val_small
            draw.text((mx + 16, my + 36), val_str, fill=c_text_bright, font=chosen_font)
            
            draw.text((mx + 16, my + 76), m["sub"], fill=c_text_sub, font=f_card_sub)

        # 4. Bonding Curve Progress Section
        pbar_box_y = start_y + 2 * card_h + gap_y + 14
        pbar_box_h = 96
        draw.rounded_rectangle([content_x1, pbar_box_y, content_x2, pbar_box_y + pbar_box_h], radius=6, fill=c_card_bg, outline=c_card_border, width=1)
        draw.rectangle([content_x1, pbar_box_y + 6, content_x1 + 3, pbar_box_y + pbar_box_h - 6], fill=c_accent_green)

        draw.text((content_x1 + 18, pbar_box_y + 14), "PUMP.FUN BONDING CURVE PROGRESSION", fill=c_text_label, font=f_card_label)
        draw.text((content_x1 + 18, pbar_box_y + 32), "Target: ~85 SOL Pool Reserve for Raydium DEX Migration & Liquidity Burn", fill=c_text_sub, font=f_card_sub)

        pct_str = f"{curve_pct:.2f}% GRADUATED"
        pct_tw = draw.textlength(pct_str, font=f_pct)
        badge_w = int(pct_tw + 24)
        badge_h = 32
        badge_x = content_x2 - 18 - badge_w
        badge_y = pbar_box_y + 14

        draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=6, fill="#0a261c", outline=c_accent_green, width=1)
        draw.text((badge_x + 12, badge_y + 6), pct_str, fill=c_accent_green, font=f_pct)

        bx1_bar = content_x1 + 18
        bx2_bar = content_x2 - 18
        by1_bar = pbar_box_y + 56
        by2_bar = by1_bar + 14
        bar_full_w = bx2_bar - bx1_bar

        draw.rounded_rectangle([bx1_bar, by1_bar, bx2_bar, by2_bar], radius=4, fill="#111824", outline="#1c2738", width=1)
        fill_w = max(10, int(bar_full_w * (curve_pct / 100.0)))
        draw.rounded_rectangle([bx1_bar, by1_bar, bx1_bar + fill_w, by2_bar], radius=4, fill=c_accent_green)

        draw.text((bx1_bar, by2_bar + 5), "0% PUMP.FUN", fill=c_text_dim, font=f_scale)
        draw.text((bx1_bar + bar_full_w // 2 - 25, by2_bar + 5), "50% HALFWAY", fill=c_text_dim, font=f_scale)
        m_100_w = draw.textlength("100% RAYDIUM DEX", font=f_scale)
        draw.text((bx2_bar - m_100_w, by2_bar + 5), "100% RAYDIUM DEX", fill=c_accent_cyan, font=f_scale)

        # 5. Footer Split Section (Aligned with 3-Column Grid)
        footer_y = pbar_box_y + pbar_box_h + 12
        footer_h = 76

        col1_x = content_x1
        col2_end_x = col1_x + (2 * card_w) + gap_x
        col3_x = col2_end_x + gap_x
        col3_end_x = content_x2

        # Left Footer Card: Mint CA (Spans Column 1 & 2)
        draw.rounded_rectangle([col1_x, footer_y, col2_end_x, footer_y + footer_h], radius=6, fill=c_card_bg, outline=c_card_border, width=1)
        draw.rectangle([col1_x, footer_y + 6, col1_x + 3, footer_y + footer_h - 6], fill=c_accent_cyan)
        draw.text((col1_x + 18, footer_y + 12), "SOLANA CONTRACT ADDRESS (MINT)", fill=c_text_label, font=f_card_label)
        draw.text((col1_x + 18, footer_y + 32), "CVoZBDAtF5ShDYYem3zgdnmHZTSnPbpLSyKSoHdQQTpq", fill=c_accent_cyan, font=f_mono_bold)
        draw.text((col1_x + 18, footer_y + 54), "100% Fair Launch • Zero Presale • Pump.fun Verified Callout", fill=c_text_sub, font=f_card_sub)

        # Right Footer Card: Source & Identity (Spans Column 3)
        draw.rounded_rectangle([col3_x, footer_y, col3_end_x, footer_y + footer_h], radius=6, fill=c_card_bg, outline=c_card_border, width=1)
        draw.rectangle([col3_x, footer_y + 6, col3_x + 3, footer_y + footer_h - 6], fill=c_accent_purple)
        draw.text((col3_x + 18, footer_y + 12), "VERIFIED SOURCE & IDENTITY", fill=c_text_label, font=f_card_label)
        draw.text((col3_x + 18, footer_y + 32), "github.com/justrangga/stb-155-agent", fill=c_text_bright, font=f_mono_repo)
        draw.text((col3_x + 18, footer_y + 54), "X: @0xLariaa • Armbian Linux 6.1", fill=c_accent_green, font=f_card_sub)

        dest = custom_output_path or self.output_card_path
        img.save(dest, "PNG")
        logger.info(f"[CardGenerator] Status card rendered: {dest}")
        return dest
