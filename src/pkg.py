import os
import logging
from src.utils import warn, prompt

class Package:
    def __init__(self, name, repo=None):
        self.name = name
        self.repo = repo or os.getenv("LXPKG_PATH", "/usr/src/lxpkg/repo")
        self.dir = None
        for root, dirs, _ in os.walk(self.repo):
            if name in dirs:
                self.dir = os.path.join(root, name)
                logging.debug(f"Found package {name} in {self.dir}")
                break
        if not self.dir or not os.path.exists(self.dir):
            raise Exception(f"Package {name} not found in {self.repo}")
        self.version = self._read_file("version").split()[0]
        self.release = self._read_file("version").split()[1] if len(self._read_file("version").split()) > 1 else "0"
        self.sources = self._read_file("sources").splitlines() if os.path.exists(self._path("sources")) else []
        self.depends = self._read_file("depends").splitlines() if os.path.exists(self._path("depends")) else []
        self._checksums = None  # Cache for checksums
        self.checksums = self._read_checksums()

    def _path(self, fname):
        return os.path.join(self.dir, fname)

    def _read_file(self, fname):
        try:
            with open(self._path(fname)) as f:
                content = f.read().strip()
                logging.debug(f"Read {fname} for {self.name}: {content}")
                return content
        except FileNotFoundError:
            logging.warning(f"Missing {fname} for {self.name}")
            return ""

    def _read_checksums(self):
        if self._checksums is not None:
            return self._checksums
        checksums = {}
        checksum_file = self._path("checksums")
        if not os.path.exists(checksum_file):
            logging.warning(f"No checksums file for {self.name}")
            return checksums
        with open(checksum_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    checksum, filename = line.split(maxsplit=1)
                    checksums[filename] = checksum
                    logging.debug(f"Checksum for {filename}: {checksum}")
                except ValueError:
                    warn(f"Invalid checksum format in {self.name}/checksums: '{line}'")
                    # Try to infer filename from sources
                    source_filename = self.sources[0].split("/")[-1] if self.sources else None
                    if source_filename and prompt(f"Use inferred filename '{source_filename}' for checksum '{line}'?"):
                        checksums[source_filename] = line
                        logging.debug(f"Inferred checksum for {source_filename}: {line}")
                    elif not prompt("Invalid checksum format. Continue without verification?"):
                        raise Exception(f"Aborted due to invalid checksum format in {self.name}/checksums")
        if not checksums and os.getenv("LXPKG_SKIP_CHECKSUMS") != "1":
            warn(f"No valid checksums found for {self.name}")
            if not prompt("No valid checksums. Continue without verification?"):
                raise Exception(f"Aborted due to missing checksums for {self.name}")
        self._checksums = checksums
        return checksums
