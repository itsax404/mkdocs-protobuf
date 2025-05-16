import os
import json
import logging
import hashlib
from pathlib import Path

log = logging.getLogger("mkdocs.plugins.protobuf")

__all__ = ["ProtoFileCache"]

__all__ = ["ProtoFileCache"]


class ProtoFileCache:
    """
    A cache system to track processed proto files and their hashes
    to avoid unnecessary rebuilds.
    """

    def __init__(self, cache_file=None):
        self.cache_file = cache_file or os.path.join(
            os.path.expanduser("~"), ".mkdocs_protobuf_cache.json"
        )
        self.file_hashes = {}
        self.load_cache()

    def load_cache(self):
        """Load the cache from disk if it exists"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r") as f:
                    self.file_hashes = json.load(f)
                log.debug(f"Loaded cache with {len(self.file_hashes)} entries")
        except Exception as e:
            log.warning(f"Failed to load cache: {str(e)}")
            self.file_hashes = {}

    def save_cache(self):
        """Save the cache to disk"""
        try:
            cache_dir = os.path.dirname(self.cache_file)
            if cache_dir and not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)

            with open(self.cache_file, "w") as f:
                json.dump(self.file_hashes, f)
            log.debug(f"Saved cache with {len(self.file_hashes)} entries")
        except Exception as e:
            log.warning(f"Failed to save cache: {str(e)}")

    def get_file_hash(self, file_path):
        """Calculate the hash of a file's contents"""
        try:
            with open(file_path, "rb") as f:
                file_content = f.read()
                return hashlib.md5(file_content).hexdigest()
        except Exception as e:
            log.warning(f"Failed to hash file {file_path}: {str(e)}")
            return None

    def is_file_changed(self, file_path):
        """Check if a file has changed since it was last processed"""
        abs_path = str(Path(file_path).absolute())

        # If file doesn't exist, consider it unchanged
        if not os.path.exists(abs_path):
            return False

        # Calculate current hash
        current_hash = self.get_file_hash(abs_path)

        # If we can't hash the file for some reason, consider it changed
        if not current_hash:
            return True

        # Compare with previous hash
        previous_hash = self.file_hashes.get(abs_path)

        # If no previous hash or hash changed, the file has changed
        return previous_hash != current_hash

    def update_file_hash(self, file_path):
        """Update the stored hash for a file"""
        abs_path = str(Path(file_path).absolute())
        current_hash = self.get_file_hash(abs_path)

        if current_hash:
            self.file_hashes[abs_path] = current_hash
            # Save the cache after each update to ensure persistence
            self.save_cache()
            return True
        return False
