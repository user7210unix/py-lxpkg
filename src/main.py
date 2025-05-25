#!/usr/bin/env python3
import sys
import os
from src.utils import log, warn, die, print_success, print_info, prompt
from src.pkg import Package
from src.fetch import fetch_sources
from src.build import build_package
from src.deps import resolve_dependencies

# Configuration
def load_config():
    config_file = "/etc/lxpkg.conf"
    defaults = {
        "LXPKG_PATH": "/usr/src/lxpkg/repo",
        "LXPKG_COMPRESS": "xz",
        "LXPKG_SKIP_CHECKSUMS": "0",
        "LXPKG_STRIP": "1",
        "LXPKG_COLOR": "1",
        "LXPKG_VERBOSE": "0"
    }
    if not os.path.exists(config_file):
        log(f"Creating default configuration at {config_file}")
        with open(config_file, "w") as f:
            f.write("# lxpkg configuration file\n")
            for key, value in defaults.items():
                f.write(f"{key}={value}\n")
    # Parse key-value pairs
    config = defaults.copy()
    try:
        with open(config_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        if key in defaults:
                            config[key] = value
                    except ValueError:
                        warn(f"Invalid line in {config_file}: {line}")
    except Exception as e:
        warn(f"Failed to read {config_file}: {e}")
    for key, value in config.items():
        os.environ.setdefault(key, value)
    if os.environ["LXPKG_COLOR"] == "0" or not sys.stderr.isatty():
        from src.utils import Fore, Style, ITALIC, RESET
        Fore = Style = type("", (), {"__getattr__": lambda self, x: ""})()
        ITALIC = RESET = ""

# Temporary directories
def setup_temp_dirs():
    log("Setting up temporary directories...")
    cache_dir = os.getenv("LXPKG_CACHEDIR", "/var/cache/lxpkg")
    src_dir = f"/tmp/lxpkg-{os.getlogin()}/src"
    bld_dir = f"/tmp/lxpkg-{os.getlogin()}/build"
    pkg_dir = f"/tmp/lxpkg-{os.getlogin()}/pkg"
    for dir in [src_dir, bld_dir, pkg_dir]:
        if os.path.exists(dir):
            log(f"Cleaning existing directory {dir}")
            os.system(f"rm -rf {dir}")
        os.makedirs(dir)
    os.makedirs(cache_dir, exist_ok=True)
    sys_db = os.path.join(os.getenv("LXPKG_ROOT", "/"), "var/db/lxpkg/installed")
    os.makedirs(sys_db, exist_ok=True)
    return cache_dir, src_dir, bld_dir, pkg_dir, sys_db

# Commands
def search_packages(query):
    print_info(f"Searching for packages matching '{query}'...")
    found = False
    repo_path = os.getenv("LXPKG_PATH")
    for root, dirs, _ in os.walk(repo_path):
        for pkg_name in dirs:
            if query.lower() in pkg_name.lower():
                pkg_dir = os.path.join(root, pkg_name)
                if os.path.exists(os.path.join(pkg_dir, "version")):
                    try:
                        pkg = Package(pkg_name)
                        section = os.path.basename(os.path.dirname(pkg_dir))
                        print(f" * {pkg_name:<20} Section: {section} Version: {pkg.version}")
                        found = True
                    except Exception as e:
                        warn(f"Skipping {pkg_name}: {e}")
    if not found:
        warn(f"No packages found matching '{query}'")

def install_package(pkg_name):
    print_info(f"Installing package {pkg_name}...")
    cache_dir, src_dir, bld_dir, pkg_dir, sys_db = setup_temp_dirs()
    try:
        pkg = Package(pkg_name)
        deps = resolve_dependencies(pkg)
        print_success(f"Resolved dependencies: {', '.join(deps)}")
        for dep in deps:
            dep_pkg = Package(dep)
            print_info(f"Processing package {dep}...")
            fetch_sources(dep_pkg, src_dir)
            build_package(dep_pkg, src_dir, bld_dir, pkg_dir, sys_db)
        print_success(f"Successfully installed {pkg_name}")
    except Exception as e:
        die(f"Installation failed for {pkg_name}: {e}")

def list_installed():
    print_info("Listing installed packages...")
    sys_db = os.path.join(os.getenv("LXPKG_ROOT", "/"), "var/db/lxpkg/installed")
    if not os.path.exists(sys_db):
        print_info("No packages installed.")
        return
    for pkg_name in os.listdir(sys_db):
        pkg_dir = os.path.join(sys_db, pkg_name)
        if os.path.isdir(pkg_dir):
            version_file = os.path.join(pkg_dir, "version")
            if os.path.exists(version_file):
                with open(version_file) as f:
                    version = f.read().strip()
                print(f" * {pkg_name:<20} Version: {version}")
            else:
                warn(f"Skipping {pkg_name}: missing version file")

def show_version():
    print_success("lxpkg version 1.2.7")

def show_help():
    print("lxpkg: Package manager for lxos")
    print("Usage: lxpkg [command] [pkg...]")
    print("Commands:")
    commands = [
        ("i,install", "Install packages"),
        ("s,search", "Search for packages"),
        ("l,list", "List installed packages"),
        ("v,version", "Show lxpkg version"),
        ("h,help", "Show this help message")
    ]
    for cmd, desc in commands:
        print(f"  {cmd:<20} {desc}")
    print("Configuration file: /etc/lxpkg.conf")
    configs = [
        ("LXPKG_PATH", "Repository paths (default: /usr/src/lxpkg/repo)"),
        ("LXPKG_COMPRESS", "Compression type (gz, xz, zst; default: xz)"),
        ("LXPKG_SKIP_CHECKSUMS", "Skip checksum verification (set to 1)"),
        ("LXPKG_VERBOSE", "Enable verbose logging (set to 1)")
    ]
    for var, desc in configs:
        print(f"  {var:<20} {desc}")

# Main
def main():
    log(f"Command-line arguments: {sys.argv}", verbose_only=True)
    load_config()
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)
    command = sys.argv[1].lstrip("-")  # Strip leading dashes
    commands = {
        "i": lambda: install_package(sys.argv[2]) if len(sys.argv) == 3 else die("install requires a package name"),
        "install": lambda: install_package(sys.argv[2]) if len(sys.argv) == 3 else die("install requires a package name"),
        "s": lambda: search_packages(sys.argv[2]) if len(sys.argv) == 3 else search_packages(""),
        "search": lambda: search_packages(sys.argv[2]) if len(sys.argv) == 3 else search_packages(""),
        "l": list_installed,
        "list": list_installed,
        "v": show_version,
        "version": show_version,
        "h": show_help,
        "help": show_help
    }
    if command not in commands:
        die(f"Unknown command: {command}")
    if os.getuid() != 0 and not os.getenv("BOOTSTRAP_LXPKG") and not os.getenv("LXPKG_SUDO"):
        cmd_su = os.getenv("LXPKG_SU", "sudo")
        os.execvp(cmd_su, [cmd_su] + sys.argv)
    commands[command]()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        die(f"Unexpected error: {e}")
