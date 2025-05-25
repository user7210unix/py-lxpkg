import os
import urllib.request
import tarfile
import zipfile
import subprocess
from src.utils import log, warn, die, print_success, print_info, prompt

def fetch_sources(pkg, src_dir):
    src_path = os.path.join(src_dir, pkg.name)
    os.makedirs(src_path, exist_ok=True)
    os.chdir(src_path)
    if not pkg.sources:
        warn(f"No sources file found for {pkg.name}")
        if not prompt("No sources found. Continue?"):
            die(f"Aborted due to missing sources for {pkg.name}")
        return
    for url in pkg.sources:
        filename = url.split("/")[-1]
        log(f"Processing source: {url}")
        if not os.path.exists(filename):
            print_info(f"Downloading {filename}...")
            try:
                urllib.request.urlretrieve(url, filename)
                print_success(f"Downloaded {filename}")
            except Exception as e:
                die(f"Failed to download {filename}: {e}")
        # Verify checksum
        if filename in pkg.checksums and os.getenv("LXPKG_SKIP_CHECKSUMS") != "1":
            print_info(f"Verifying checksum for {filename}...")
            expected = pkg.checksums[filename]
            result = subprocess.run(["sha256sum", filename], capture_output=True, text=True)
            actual = result.stdout.split()[0]
            if actual != expected:
                warn(f"Checksum mismatch for {filename}: expected {expected}, got {actual}")
                if not prompt("Checksum verification failed. Continue?"):
                    die(f"Aborted due to checksum mismatch for {filename}")
            print_success(f"Checksum verified for {filename}")
        # Extract
        log(f"Extracting {filename} to {src_path}")
        try:
            if filename.endswith((".tar.gz", ".tgz")):
                with tarfile.open(filename, "r:gz") as tar:
                    tar.extractall(src_path, filter="data")
            elif filename.endswith((".tar.bz2", ".tbz2")):
                with tarfile.open(filename, "r:bz2") as tar:
                    tar.extractall(src_path, filter="data")
            elif filename.endswith((".tar.xz", ".txz")):
                with tarfile.open(filename, "r:xz") as tar:
                    tar.extractall(src_path, filter="data")
            elif filename.endswith(".zip"):
                with zipfile.ZipFile(filename, "r") as zip_ref:
                    zip_ref.extractall(src_path)
                # Move files from subdirectory if created
                subdirs = [d for d in os.listdir(src_path) if os.path.isdir(os.path.join(src_path, d))]
                if len(subdirs) == 1:
                    subdir = subdirs[0]
                    for item in os.listdir(os.path.join(src_path, subdir)):
                        os.rename(os.path.join(src_path, subdir, item), os.path.join(src_path, item))
                    os.rmdir(os.path.join(src_path, subdir))
            else:
                warn(f"Unknown archive type for {filename}, skipping extraction")
                continue
            log(f"Extracted {filename} successfully")
        except Exception as e:
            warn(f"Failed to extract {filename}: {e}")
            if not prompt(f"Extraction failed for {filename}. Continue?"):
                die(f"Aborted due to extraction failure for {filename}")
