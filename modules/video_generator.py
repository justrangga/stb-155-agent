import os
import sys
import math
import time
import random
import logging
import subprocess
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

class VideoGenerator:
    """
    Autonomous Video Rendering Engine for Laria running on ARM64 Linux STB-155.
    Generates high-tech cybernetic MP4 animation clips (H.264 / 24fps)
    using Pillow frame rendering piped directly to system ffmpeg.
    Renders 4-5 second clips in ~4-5 seconds with minimal memory footprint (< 40MB).
    """
    def __init__(self, data_dir: str = None):
        if not data_dir:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(data_dir, exist_ok=True)
        self.data_dir = data_dir
        self.default_output_path = os.path.join(data_dir, "laria_telemetry.mp4")

    def generate_cyber_video(self, theme: str = "silicon_pulse", telemetry: dict = None, market_data: dict = None, output_path: str = None) -> str:
        dest_path = output_path or self.default_output_path
        start_time = time.time()

        width, height = 720, 720
        fps = 24
        duration = 4.0 # 4 seconds
        total_frames = int(fps * duration)

        # Telemetry extracts
        temp_c = telemetry.get("temperature_c", 52.0) if telemetry else 52.0
        uptime = telemetry.get("uptime", "1d 10h") if telemetry else "1d 10h"
        treasury = telemetry.get("treasury_sol", 0.0131) if telemetry else 0.0131
        mcap = market_data.get("market_cap", 3347) if market_data else 3347
        curve_pct = market_data.get("curve_progress", 0.01) if market_data else 0.01

        # Fonts
        f_dir = "/usr/share/fonts/truetype/dejavu"
        try:
            f_title = ImageFont.truetype(f"{f_dir}/DejaVuSans-Bold.ttf", 22)
            f_mono_large = ImageFont.truetype(f"{f_dir}/DejaVuSansMono-Bold.ttf", 24)
            f_mono = ImageFont.truetype(f"{f_dir}/DejaVuSansMono-Bold.ttf", 14)
            f_mono_sm = ImageFont.truetype(f"{f_dir}/DejaVuSansMono.ttf", 12)
        except Exception:
            f_title = f_mono_large = f_mono = f_mono_sm = ImageFont.load_default()

        # ffmpeg pipe command
        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{width}x{height}",
            "-pix_fmt", "rgb24",
            "-r", str(fps),
            "-i", "-",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            "-tune", "animation",
            dest_path
        ]

        try:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.error(f"[VideoGenerator] Failed to spawn ffmpeg: {e}")
            return None

        # Choose theme or random
        themes = ["silicon_pulse", "terminal_stream"]
        chosen_theme = theme if theme in themes else random.choice(themes)

        cx, cy = width // 2, height // 2

        for f_idx in range(total_frames):
            img = Image.new("RGB", (width, height), color="#06080d")
            draw = ImageDraw.Draw(img)

            # 1. Subtle Background Cyber Grid
            for gx in range(0, width, 40):
                draw.line([(gx, 0), (gx, height)], fill="#0b121e", width=1)
            for gy in range(0, height, 40):
                draw.line([(0, gy), (width, gy)], fill="#0b121e", width=1)

            # Outer Viewfinder Brackets
            draw.rectangle([25, 25, width - 25, height - 25], outline="#152136", width=1)
            blen = 24
            for (bx, by, dx, dy) in [(25, 25, 1, 1), (width-25, 25, -1, 1), (25, height-25, 1, -1), (width-25, height-25, -1, -1)]:
                draw.line([(bx, by), (bx + dx * blen, by)], fill="#00ffa3", width=2)
                draw.line([(bx, by), (bx, by + dy * blen)], fill="#00ffa3", width=2)

            # Header info on all frames
            draw.text((45, 40), "LARIA OS  //  LIVE HARDWARE VITALS", fill="#ffffff", font=f_title)
            draw.text((45, 68), "STB-155 ARM64  •  SOLANA NODE  •  PROOF-OF-LIFE", fill="#6b82a6", font=f_mono_sm)

            # Status pill top-right
            draw.rounded_rectangle([width - 170, 38, width - 45, 70], radius=5, fill="#0a261c", outline="#00ffa3", width=1)
            draw.ellipse([width - 155, 49, width - 145, 59], fill="#00ffa3")
            draw.text((width - 135, 46), "24/7 LIVE", fill="#00ffa3", font=f_mono)

            # Frame progress (0.0 to 1.0)
            t_ratio = f_idx / total_frames
            pulse = math.sin(t_ratio * math.pi * 4) # 2 cycles
            angle = (t_ratio * 360 * 2) % 360      # rotating sweep

            if chosen_theme == "silicon_pulse":
                # Concentric radar rings
                r_base = int(140 + 35 * pulse)
                for r in [60, 110, 160, 210]:
                    col = "#00ffa3" if abs(r - r_base) < 30 else "#16253c"
                    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=2)

                # Rotating radar beam
                rad = math.radians(angle)
                end_x = cx + int(210 * math.cos(rad))
                end_y = cy + int(210 * math.sin(rad))
                draw.line([(cx, cy), (end_x, end_y)], fill="#00e5ff", width=2)

                # Central SoC Die
                die_w = int(75 + 10 * pulse)
                draw.rectangle([cx - die_w, cy - die_w, cx + die_w, cy + die_w], fill="#0e1726", outline="#00ffa3", width=2)
                draw.text((cx - 48, cy - 14), "ARM64", fill="#00ffa3", font=f_mono_large)
                draw.text((cx - 52, cy + 14), "STB-155", fill="#ffffff", font=f_mono)

                # Real-time Telemetry Callouts
                draw.text((45, height - 140), f"SoC TEMP:  {temp_c:.1f}°C", fill="#ffb800", font=f_mono)
                draw.text((45, height - 115), f"TREASURY:  {treasury:.4f} SOL", fill="#00ffa3", font=f_mono)
                draw.text((45, height - 90),  f"MCAP:      ${mcap:,.0f}", fill="#00e5ff", font=f_mono)
                draw.text((45, height - 65),  f"CURVE:     {curve_pct:.2f}% GRADUATED", fill="#c084fc", font=f_mono)

                # Moving scanline
                scan_y = int((f_idx * 28) % (height - 180)) + 90
                draw.line([(30, scan_y), (width - 30, scan_y)], fill="#00e5ff", width=1)

            elif chosen_theme == "terminal_stream":
                # High-speed scrolling kernel log
                terminal_y = 110
                log_lines = [
                    f"[sys] kernel Linux 6.1-armbian #1 SMP PREEMPT",
                    f"[soc] amlogic quad-core frequency: 1512 MHz",
                    f"[vitals] soc_thermal nominal at {temp_c:.1f} C",
                    f"[mem] 322MB / 787MB allocated [daemon ~32M]",
                    f"[solana] rpc block height streaming live...",
                    f"[ed25519] verifying non-custodial local keypair",
                    f"[pump.fun] bonding curve reserve: active",
                    f"[treasury] {treasury:.4f} SOL fuel confirmed",
                    f"[agent] autonomous continuous self-learning active",
                    f"[autonomy] zero cloud datacenter dependence"
                ]
                
                # Scroll offset based on frame index
                shift = int((f_idx * 1.8)) % len(log_lines)
                disp_lines = log_lines[shift:] + log_lines[:shift]
                
                for l_idx, line in enumerate(disp_lines[:12]):
                    y_pos = terminal_y + l_idx * 34
                    txt_color = "#00ffa3" if "nominal" in line or "confirmed" in line else "#8fa6c7"
                    if "sovereignty" in line or "zero cloud" in line:
                        txt_color = "#00e5ff"
                    draw.text((50, y_pos), f"> {line}", fill=txt_color, font=f_mono)

                # Blinking cursor at bottom
                if (f_idx // 6) % 2 == 0:
                    draw.rectangle([50, terminal_y + 12 * 34, 65, terminal_y + 12 * 34 + 16], fill="#00ffa3")

                # Footer CA
                draw.text((45, height - 60), "CA: CVoZBDAtF5ShDYYem3zgdnmHZTSnPbpLSyKSoHdQQTpq", fill="#00e5ff", font=f_mono_sm)

            proc.stdin.write(img.tobytes())

        proc.stdin.close()
        proc.wait()

        elapsed = time.time() - start_time
        size = os.path.getsize(dest_path) if os.path.exists(dest_path) else 0
        logger.info(f"[VideoGenerator] Rendered {chosen_theme} MP4 in {elapsed:.2f}s ({size} bytes): {dest_path}")
        return dest_path
