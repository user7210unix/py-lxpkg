import logging
import sys
import os
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# ANSI codes
ITALIC = "\033[3m"
RESET = "\033[0m"

# Logging setup
logging.basicConfig(filename="/var/log/lxpkg.log", level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s")

# Colorful output functions
def log(msg, verbose_only=False):
    if verbose_only and os.getenv("LXPKG_VERBOSE", "0") != "1":
        return
    print(f"{Fore.LIGHTBLACK_EX}{ITALIC}==> {msg}{RESET}")
    logging.info(msg)

def warn(msg):
    print(f"{Fore.YELLOW}{Style.BRIGHT}[WARNING] {msg}{Style.RESET_ALL}")
    logging.warning(msg)

def die(msg, exit_code=1):
    print(f"{Fore.RED}{Style.BRIGHT}[ERROR] {msg}{Style.RESET_ALL}")
    logging.error(msg)
    sys.exit(exit_code)

def print_success(msg):
    print(f"{Fore.GREEN}{Style.BRIGHT}[SUCCESS] {msg}{Style.RESET_ALL}")
    logging.info(msg)

def print_info(msg):
    print(f"{Fore.CYAN}{Style.BRIGHT}[INFO] {msg}{Style.RESET_ALL}")
    logging.info(msg)

def prompt(msg):
    print(f"{Fore.GREEN}{Style.BRIGHT}{msg}{Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLACK_EX}Continue? [y/N] {RESET}", end="")
    response = input().strip().lower()
    return response in ["y", "yes"]
