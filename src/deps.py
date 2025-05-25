from src.pkg import Package
from src.main import log, warn, prompt, print_info
import os

def resolve_dependencies(pkg):
    seen = set()
    stack = []
    deps = []

    def resolve(pkg_name):
        if pkg_name in seen:
            return
        if pkg_name in stack:
            warn(f"Circular dependency detected involving {pkg_name}")
            return
        stack.append(pkg_name)
        try:
            pkg = Package(pkg_name)
            for dep in pkg.depends:
                dep = dep.split()[0]  # Ignore make/run type
                resolve(dep)
            if pkg_name not in seen:
                deps.append(pkg_name)
                seen.add(pkg_name)
        except Exception as e:
            warn(f"Dependency {pkg_name} not found: {e}")
            if not prompt(f"Dependency {pkg_name} is missing. Continue?"):
                raise Exception(f"Aborted due to missing dependency {pkg_name}")
        stack.pop()

    log(f"Resolving dependencies for {pkg.name}...")
    resolve(pkg.name)
    return deps
