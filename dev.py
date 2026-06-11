# dev.py

import subprocess
import sys

from watchfiles import run_process


def start():
    subprocess.run([sys.executable, "main.py"])


if __name__ == "__main__":
    run_process(".", target=start)
