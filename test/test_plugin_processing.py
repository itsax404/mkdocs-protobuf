import unittest
import tempfile
import os
import shutil
import time
from pathlib import Path

from mkdocs_protobuf_plugin.plugin import ProtobufPlugin

class TestPluginFileProcessing(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Create proto directory
        self.proto_dir = os.path.join(self.temp_dir, "proto")
        os.makedirs(self.proto_dir)
        
        # Create output directory
        self.output_dir = os.path.join(self.temp_dir, "docs", "api")
        os.makedirs(os.path.join(self.temp_dir, "docs"), exist_ok=True)
        
        # Create a test proto file
        self.test_proto_file = os.path.join(self.proto_dir, "test.proto")
        with open(self.test_proto_file, "w") as f:
            f.write("""
syntax = "proto3";
package test;
message TestMessage {
    string name = 1;
}
""")
        
        # Initialize plugin
        self.plugin = ProtobufPlugin()
        self.plugin.config = {
            'proto_paths': [self.proto_dir],
            'output_dir': 'api'
        }
        
        # Create a minimal MkDocs config
        self.mkdocs_config = {
            'docs_dir': os.path.join(self.temp_dir, "docs"),
            'nav': []
        }
        
    def tearDown(self):
        # Clean up
        shutil.rmtree(self.temp_dir)
        
    def test_initial_file_processing(self):
        """Test that files are processed on first run"""
        # Process files
        generated_files = self.plugin._process_proto_files(
            [self.proto_dir], 
            self.output_dir
        )
        
        # Check that output file was created
        expected_output = os.path.join(self.output_dir, "test.md")
        self.assertTrue(os.path.exists(expected_output))
        self.assertIn(expected_output, generated_files)
        
    def test_unchanged_file_skipping(self):
        """Test that unchanged files are skipped on subsequent runs"""
        # First run - should process the file
        generated_files1 = self.plugin._process_proto_files(
            [self.proto_dir], 
            self.output_dir
        )
        self.assertEqual(len(generated_files1), 1)
        
        # Get file modification time
        output_file = os.path.join(self.output_dir, "test.md")
        mtime1 = os.path.getmtime(output_file)
        
        # Wait a moment to ensure any new write would have a different timestamp
        time.sleep(0.1)
        
        # Second run - should skip the file since it hasn't changed
        generated_files2 = self.plugin._process_proto_files(
            [self.proto_dir], 
            self.output_dir
        )
        
        # Should return empty list since no files changed
        self.assertEqual(len(generated_files2), 0)
        
        # Output file should not have been modified
        mtime2 = os.path.getmtime(output_file)
        self.assertEqual(mtime1, mtime2)
        
    def test_changed_file_processing(self):
        """Test that changed files are processed on subsequent runs"""
        # First run - should process the file
        self.plugin._process_proto_files(
            [self.proto_dir], 
            self.output_dir
        )
        
        # Get file modification time
        output_file = os.path.join(self.output_dir, "test.md")
        mtime1 = os.path.getmtime(output_file)
        
        # Wait a moment to ensure any new write would have a different timestamp
        time.sleep(0.1)
        
        # Modify the proto file
        with open(self.test_proto_file, "w") as f:
            f.write("""
syntax = "proto3";
package test;
message TestMessage {
    string name = 1;
    string description = 2;  // Added a new field
}
""")
        
        # Second run - should process the file again
        generated_files2 = self.plugin._process_proto_files(
            [self.proto_dir], 
            self.output_dir
        )
        
        # Should return the output file since the proto file changed
        self.assertEqual(len(generated_files2), 1)
        
        # Output file should have been modified
        mtime2 = os.path.getmtime(output_file)
        self.assertNotEqual(mtime1, mtime2)
        
if __name__ == "__main__":
    unittest.main()
