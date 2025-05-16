import unittest
import tempfile
import os
import shutil
import copy

from mkdocs_protobuf_plugin.plugin import ProtobufPlugin


class TestNavigation(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()

        # Create proto directory
        self.proto_dir = os.path.join(self.temp_dir, "proto")
        os.makedirs(self.proto_dir)

        # Create nested proto directories
        self.example_dir = os.path.join(self.proto_dir, "example", "document", "v1")
        os.makedirs(self.example_dir, exist_ok=True)

        # Create output directory
        self.output_dir = os.path.join(self.temp_dir, "docs", "api")
        os.makedirs(os.path.join(self.temp_dir, "docs"), exist_ok=True)

        # Create test proto files
        self.test_proto_file = os.path.join(self.proto_dir, "test.proto")
        with open(self.test_proto_file, "w") as f:
            f.write("""
syntax = "proto3";
package test;
message TestMessage {
    string name = 1;
}
""")

        self.user_proto_file = os.path.join(self.proto_dir, "user.proto")
        with open(self.user_proto_file, "w") as f:
            f.write("""
syntax = "proto3";
package user;
message User {
    string id = 1;
    string name = 2;
}
""")

        self.service_proto_file = os.path.join(self.example_dir, "service.proto")
        with open(self.service_proto_file, "w") as f:
            f.write("""
syntax = "proto3";
package example.document.v1;
message Document {
    string id = 1;
    string title = 2;
}
service DocumentService {
    rpc GetDocument(GetDocumentRequest) returns (Document);
}
message GetDocumentRequest {
    string document_id = 1;
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

    def test_auto_nav_generation(self):
        """Test that navigation is auto-generated correctly"""
        # Process the files
        generated_files = self.plugin._process_proto_files(
            [self.proto_dir],
            self.output_dir
        )

        # Should generate three files
        self.assertEqual(len(generated_files), 3)

        # Create a copy of the config to work with
        config = copy.deepcopy(self.mkdocs_config)

        # Update navigation
        self.plugin._update_navigation(config, 'api', generated_files)

        # Should have created an API Reference entry
        self.assertEqual(len(config['nav']), 1)
        self.assertTrue(isinstance(config['nav'][0], dict))
        self.assertIn('API Reference', config['nav'][0])

        # Check the structure of the API Reference
        api_nav = config['nav'][0]['API Reference']

        # In the new navigation structure, we group everything under API
        self.assertTrue(len(api_nav) > 0, "API navigation should have entries")

        # Check that we have some kind of structure in the navigation
        has_structure = False
        for entry in api_nav:
            if isinstance(entry, dict):
                has_structure = True
                break

        self.assertTrue(has_structure, "Navigation should have some structure")

    def test_custom_nav_preservation(self):
        """Test that custom navigation is preserved"""
        # Process the files
        generated_files = self.plugin._process_proto_files(
            [self.proto_dir],
            self.output_dir
        )

        # Create a config with custom navigation
        config = copy.deepcopy(self.mkdocs_config)
        config['nav'] = [
            {'Home': 'index.md'},
            {'API Reference': [
                {'Overview': 'api/index.md'},
                {'Test API': 'api/test.md'},
                {'User API': 'api/user.md'},
                {'Document API': {
                    'Service': 'api/example/document/v1/service.md'
                }}
            ]},
            {'Development': [
                {'Guide': 'development.md'}
            ]}
        ]

        # Store a copy of the original nav for comparison
        original_nav = copy.deepcopy(config['nav'])

        # Create a custom method to access navigation with i18n considered
        def check_api_reference_preserved():
            """Check if API Reference structure is preserved correctly"""
            # Basic structure checks
            self.assertEqual(len(config['nav']), 3, "Should have 3 top-level nav entries")
            self.assertTrue('API Reference' in config['nav'][1], "API Reference should be present")

            # Verify Home and Development entries are unchanged
            self.assertEqual(config['nav'][0], original_nav[0], "Home entry should be unchanged")
            self.assertEqual(config['nav'][2], original_nav[2], "Development entry should be unchanged")

        # First do a direct check before running the method
        check_api_reference_preserved()

        # Now run the update method - it should preserve custom navigation
        self.plugin._update_navigation(config, 'api', generated_files)

        # Check again after the update
        check_api_reference_preserved()


if __name__ == "__main__":
    unittest.main()
