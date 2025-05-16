import unittest
import tempfile
import os
import json
import hashlib
import shutil

from mkdocs_protobuf_plugin.file_cache import ProtoFileCache

class TestProtoFileCache(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the cache and test files
        self.temp_dir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self.temp_dir, "test_cache.json")
        
        # Create a test file
        self.test_file = os.path.join(self.temp_dir, "test.proto")
        with open(self.test_file, "w") as f:
            f.write("""
syntax = "proto3";

package test;

message TestMessage {
    string name = 1;
}
""")
            
        # Initialize cache
        self.cache = ProtoFileCache(cache_file=self.cache_file)
        
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir)
        
    def test_cache_initialization(self):
        """Test that the cache initializes correctly"""
        self.assertEqual(self.cache.cache_file, self.cache_file)
        self.assertEqual(self.cache.file_hashes, {})
        
    def test_file_hash_calculation(self):
        """Test that file hash is calculated correctly"""
        file_hash = self.cache.get_file_hash(self.test_file)
        self.assertIsNotNone(file_hash)
        
        # Calculate expected hash manually
        with open(self.test_file, 'rb') as f:
            content = f.read()
            expected_hash = hashlib.md5(content).hexdigest()
            
        self.assertEqual(file_hash, expected_hash)
        
    def test_file_change_detection(self):
        """Test that file changes are detected correctly"""
        # Initially, the file should be considered changed (not in cache)
        self.assertTrue(self.cache.is_file_changed(self.test_file))
        
        # Update the cache
        self.cache.update_file_hash(self.test_file)
        
        # Now the file should not be considered changed
        self.assertFalse(self.cache.is_file_changed(self.test_file))
        
        # Modify the file
        with open(self.test_file, "w") as f:
            f.write("""
syntax = "proto3";

package test;

message TestMessage {
    string name = 1;
    string description = 2;  // Added a new field
}
""")
            
        # The file should now be considered changed
        self.assertTrue(self.cache.is_file_changed(self.test_file))
        
    def test_cache_persistence(self):
        """Test that the cache is persisted to disk"""
        # Update the cache
        self.cache.update_file_hash(self.test_file)
        
        # Check if cache file was created
        self.assertTrue(os.path.exists(self.cache_file))
        
        # Load the cache directly and verify contents
        with open(self.cache_file, 'r') as f:
            cache_data = json.load(f)
            
        abs_path = os.path.abspath(self.test_file)
        self.assertIn(abs_path, cache_data)
        
        # Create a new cache instance that should load from the existing file
        new_cache = ProtoFileCache(cache_file=self.cache_file)
        self.assertIn(abs_path, new_cache.file_hashes)
        
        # The file should not be considered changed with the new cache instance
        self.assertFalse(new_cache.is_file_changed(self.test_file))
        
if __name__ == "__main__":
    unittest.main()
