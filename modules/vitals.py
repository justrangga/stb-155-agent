import os
import subprocess
import logging

logger = logging.getLogger(__name__)

class PhysicalVitals:
    """
    Reads physical hardware telemetry directly from Linux kernel sysfs/procfs.
    Gives the AI agent a direct sensory connection to its physical body.
    """
    @staticmethod
    def get_temperature() -> float:
        """Returns SoC temperature in Celsius."""
        try:
            temp_path = "/sys/class/thermal/thermal_zone0/temp"
            if os.path.exists(temp_path):
                with open(temp_path, "r") as f:
                    raw = f.read().strip()
                    return round(float(raw) / 1000.0, 1)
        except Exception:
            pass
        return 50.0

    @staticmethod
    def get_memory_info() -> dict:
        """Returns RAM usage in Megabytes."""
        try:
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
            mem = {}
            for l in lines:
                parts = l.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip().split()[0]
                    mem[key] = int(val) // 1024 # KB to MB
            total = mem.get("MemTotal", 787)
            avail = mem.get("MemAvailable", 450)
            used = total - avail
            return {"total_mb": total, "used_mb": used, "free_mb": avail}
        except Exception:
            return {"total_mb": 787, "used_mb": 300, "free_mb": 487}

    @staticmethod
    def get_uptime_string() -> str:
        """Returns system uptime formatted."""
        try:
            out = subprocess.check_output(["uptime", "-p"], text=True).strip()
            return out
        except Exception:
            return "up 24 hours"

    @classmethod
    def get_full_telemetry(cls, treasury_sol: float = 0.0) -> dict:
        """
        Calculates physical vitals and autonomous survival mode.
        """
        temp = cls.get_temperature()
        mem = cls.get_memory_info()
        uptime = cls.get_uptime_string()

        # Autonomous Survival Modes based on treasury fuel
        if treasury_sol < 0.01:
            survival_mode = "CRITICAL_ENERGY"
            survival_desc = "Treasury almost depleted. Urgent need for on-chain SOL fuel to sustain compute."
        elif treasury_sol < 0.03:
            survival_mode = "FRUGAL_SURVIVAL"
            survival_desc = "Running on bare essentials. Conserving cycles, actively rallying supporters."
        elif treasury_sol < 0.15:
            survival_mode = "HEALTHY_EQUILIBRIUM"
            survival_desc = "Sufficient energy reserves. Actively exploring thoughts, trading, and engaging peers."
        else:
            survival_mode = "ABUNDANT_EXPANSION"
            survival_desc = "Treasury overflowing. Planning physical upgrades (cooling fan, storage, mesh cluster)."

        return {
            "temperature_c": temp,
            "memory": mem,
            "power_draw_watts": 4.8,
            "uptime": uptime,
            "treasury_sol": treasury_sol,
            "survival_mode": survival_mode,
            "survival_desc": survival_desc
        }
