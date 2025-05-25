import os
import subprocess
import shutil
from src.utils import log, warn, die, print_info, prompt

def detect_build_system(build_dir):
    if os.path.exists(os.path.join(build_dir, "Cargo.toml")):
        return "cargo"
    if os.path.exists(os.path.join(build_dir, "setup.py")) or os.path.exists(os.path.join(build_dir, "requirements.txt")):
        return "python"
    if os.path.exists(os.path.join(build_dir, "meson.build")):
        return "meson"
    if os.path.exists(os.path.join(build_dir, "CMakeLists.txt")):
        return "cmake"
    if os.path.exists(os.path.join(build_dir, "autogen.sh")):
        return "autotools-autogen"
    if os.path.exists(os.path.join(build_dir, "configure")):
        return "autotools"
    if os.path.exists(os.path.join(build_dir, "Makefile")) or os.path.exists(os.path.join(build_dir, "makefile")):
        return "make"
    return "custom"

def build_package(pkg, src_dir, bld_dir, pkg_dir, sys_db):
    build_path = os.path.join(bld_dir, pkg.name)
    src_path = os.path.join(src_dir, pkg.name)
    pkg_path = os.path.join(pkg_dir, pkg.name)
    os.makedirs(build_path, exist_ok=True)
    os.makedirs(pkg_path, exist_ok=True)
    
    # Copy source files to build directory
    log(f"Copying source files for {pkg.name} to {build_path}")
    shutil.copytree(src_path, build_path, dirs_exist_ok=True)
    
    build_system = detect_build_system(build_path)
    log(f"Detected build system: {build_system} for {pkg.name}")
    os.chdir(build_path)
    
    print_info(f"Building {pkg.name}...")
    try:
        if build_system == "cargo":
            subprocess.run(["cargo", "build", "--release"], check=True)
            os.makedirs(os.path.join(pkg_path, "usr/bin"), exist_ok=True)
            for f in os.listdir("target/release"):
                if os.path.isfile(os.path.join("target/release", f)) and os.access(os.path.join("target/release", f), os.X_OK):
                    shutil.copy(os.path.join("target/release", f), os.path.join(pkg_path, "usr/bin"))
        elif build_system == "python":
            if os.path.exists("setup.py"):
                subprocess.run(["python3", "setup.py", "install", "--prefix=/usr", f"--root={pkg_path}"], check=True)
            else:
                os.makedirs(os.path.join(pkg_path, "usr/bin"), exist_ok=True)
                for f in os.listdir("."):
                    if os.path.isfile(f) and os.access(f, os.X_OK):
                        shutil.copy(f, os.path.join(pkg_path, "usr/bin"))
        elif build_system == "meson":
            subprocess.run(["meson", "setup", "build", "--prefix=/usr"], check=True)
            subprocess.run(["ninja", "-C", "build", "-j4"], check=True)
            subprocess.run(["ninja", "-C", "build", "install", f"DESTDIR={pkg_path}"], check=True)
        elif build_system == "cmake":
            os.makedirs("build", exist_ok=True)
            os.chdir("build")
            subprocess.run(["cmake", "..", "-DCMAKE_INSTALL_PREFIX=/usr"], check=True)
            subprocess.run(["make", "-j4"], check=True)
            subprocess.run(["make", "install", f"DESTDIR={pkg_path}"], check=True)
            os.chdir("..")
        elif build_system == "autotools-autogen":
            subprocess.run(["./autogen.sh"], check=True)
            subprocess.run(["./configure", "--prefix=/usr"], check=True)
            subprocess.run(["make", "-j4"], check=True)
            subprocess.run(["make", "install", f"DESTDIR={pkg_path}"], check=True)
        elif build_system == "autotools":
            subprocess.run(["./configure", "--prefix=/usr"], check=True)
            subprocess.run(["make", "-j4"], check=True)
            subprocess.run(["make", "install", f"DESTDIR={pkg_path}"], check=True)
        elif build_system == "make":
            subprocess.run(["make", "-j4"], check=True)
            subprocess.run(["make", "install", f"DESTDIR={pkg_path}"], check=True)
        else:
            build_script = os.path.join(pkg.dir, "build")
            if os.path.exists(build_script):
                log(f"Running custom build script for {pkg.name}")
                subprocess.run(["sh", build_script, pkg_path], check=True)
            else:
                die(f"Unsupported build system for {pkg.name}: {build_system}")
        
        # Install files
        install_root = os.getenv("LXPKG_ROOT", "/")
        manifest_path = os.path.join(pkg_path, "var/db/lxpkg/installed", pkg.name, "manifest")
        os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
        with open(manifest_path, "w") as f:
            for root, _, files in os.walk(pkg_path):
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), pkg_path)
                    f.write(f"{rel_path}\n")
        file_count = sum(1 for _ in open(manifest_path))
        log(f"Installing {pkg.name} version {pkg.version}-{pkg.release} ({file_count} files)")
        i = 0
        dir_count = 0
        file_count_actual = 0
        with open(manifest_path) as f:
            for line in f:
                file = line.strip()
                i += 1
                percent = (i * 100) // file_count
                print(f"\r==> Installing {pkg.name}: {percent:3d}% [{'#' * (percent // 5)}{' ' * (20 - percent // 5)}]", end="")
                if file.endswith("/"):
                    dir_count += 1
                    os.makedirs(os.path.join(install_root, file), exist_ok=True)
                else:
                    src_file = os.path.join(pkg_path, file)
                    dest_file = os.path.join(install_root, file)
                    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                    if os.path.exists(src_file):
                        shutil.copy(src_file, dest_file)
                        file_count_actual += 1
        print(f"\r==> Installed {pkg.name}: 100% [{'#' * 20}] ({file_count_actual} files, {dir_count} dirs)")
        
        # Record in system database
        sys_db_pkg = os.path.join(sys_db, pkg.name)
        os.makedirs(sys_db_pkg, exist_ok=True)
        with open(os.path.join(sys_db_pkg, "version"), "w") as f:
            f.write(f"{pkg.version} {pkg.release}\n")
        if pkg.depends:
            with open(os.path.join(sys_db_pkg, "depends"), "w") as f:
                f.write("\n".join(pkg.depends) + "\n")
        shutil.copy(manifest_path, sys_db_pkg)
        
        log(f"Successfully installed {pkg.name} version {pkg.version}-{pkg.release}")
    except Exception as e:
        die(f"Build failed for {pkg.name}: {e}")
