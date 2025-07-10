# deviceinfo.py

import os
import platform
import psutil
from log import setup_logging

logger = setup_logging()

class DeviceInfo:

    @staticmethod
    def get_cpu_info() -> str:
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.strip().startswith("model name"):
                        cpu_name = line.split(":", 1)[1].strip()
                        for token in ["(R)", "(TM)", "®", "™"]:
                            cpu_name = cpu_name.replace(token, "")
                        cpu_name = cpu_name.strip()
                        cores = os.cpu_count() or "?"
                        return f"{cores}x {cpu_name}"
        except Exception as e:
            logger.warning(f"Failed to read /proc/cpuinfo: {e}")

        cpu = platform.processor()
        if cpu and cpu != platform.machine():
            return cpu
        cores = os.cpu_count() or "?"
        return f"{cores}x CPU"



    @staticmethod
    def get_memory_info() -> str:
        mem_gib = round(psutil.virtual_memory().total / (1024 ** 3))
        return f"{mem_gib}.0 GiB"

    @staticmethod
    def get_disk_info() -> str:
        try:
            partitions = psutil.disk_partitions(all=False)
            total = 0
            for p in partitions:
                if "rw" in p.opts and os.path.exists(p.mountpoint):
                    usage = psutil.disk_usage(p.mountpoint)
                    total += usage.total
            total_gib = round(total / (1024 ** 3))
            return f"{total_gib}.0 GiB"
        except Exception as e:
            logger.warning(f"Could not get full disk info: {e}")
            return "Unknown"

    @staticmethod
    def get_board_info() -> str:
        vendor = "Unknown"
        name = "Unknown"
        try:
            with open("/sys/class/dmi/id/board_vendor") as f:
                vendor = f.read().strip()
        except Exception as e:
            logger.warning(f"Failed to read board vendor: {e}")

        try:
            with open("/sys/class/dmi/id/board_name") as f:
                name = f.read().strip()
        except Exception as e:
            logger.warning(f"Failed to read board name: {e}")

        if vendor != "Unknown" and name != "Unknown":
            return f"{vendor} {name}"
        return name if name != "Unknown" else vendor

    @staticmethod
    def get_gpu_info() -> str:
        try:
            import subprocess
            output = subprocess.check_output(["lspci"], text=True)
            gpus = []

            for line in output.splitlines():
                if "VGA compatible controller" in line or "3D controller" in line:
                    # Get the part after ": "
                    gpu_info = line.split(": ", 1)[-1]

                    # Remove anything inside parentheses
                    import re
                    gpu_info = re.sub(r"\s*\(.*?\)", "", gpu_info).strip()

                    gpus.append(gpu_info)

            return ", ".join(gpus) if gpus else "No GPU found"

        except Exception as e:
            logger.warning(f"lspci failed: {e}")
            return "Unknown"


    @staticmethod
    def get_kernel_info() -> str:
        return platform.release()

    @staticmethod
    def get_os_info() -> str:
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME"):
                        return line.split("=")[1].replace('"', "").strip()
        except Exception as e:
            logger.warning(f"Could not get OS info: {e}")
        return platform.system()

    @staticmethod
    def get_os_version() -> str:
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("VERSION_ID"):
                        return line.split("=")[1].replace('"', "").strip()
        except Exception as e:
            logger.warning(f"Could not get OS version: {e}")
        return "Unknown"

    @staticmethod
    def get_desktop_info() -> str:
        environment = os.environ.get("XDG_CURRENT_DESKTOP", "Unknown")
        environment = environment.replace("X-", "").replace("Budgie:GNOME", "Budgie").replace(":Unity7:ubuntu", "")
        winsys = os.environ.get("XDG_SESSION_TYPE", "Unknown").capitalize()
        return f'{environment} ({winsys})'
