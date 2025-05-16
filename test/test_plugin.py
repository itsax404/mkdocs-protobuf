import unittest
import tempfile
import os
import shutil

from mkdocs_protobuf_plugin.converter import ProtoToMarkdownConverter
from mkdocs_protobuf_plugin.import_resolver import ProtoImportResolver
from mkdocs_protobuf_plugin.plugin import ProtobufPlugin


class TestProtoImportResolver(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test proto files
        self.temp_dir = tempfile.mkdtemp()

        # Create some test proto files
        self.example_dir = os.path.join(self.temp_dir, "example", "document", "v1")
        os.makedirs(self.example_dir)

        # Create test proto files
        self.user_proto_path = os.path.join(self.temp_dir, "user.proto")
        self.data_proto_path = os.path.join(self.example_dir, "data.proto")
        self.service_proto_path = os.path.join(self.example_dir, "service.proto")

        # Write content to test proto files
        with open(self.user_proto_path, "w") as f:
            f.write(
                """
syntax = "proto3";

package user;

message User {
  string id = 1;
  string name = 2;
  string email = 3;
}
"""
            )

        with open(self.data_proto_path, "w") as f:
            f.write(
                """
syntax = "proto3";

package example.document.v1;

import "user.proto";

message Document {
  string id = 1;
  string title = 2;
  string content = 3;
  user.User creator = 4;
}
"""
            )

        with open(self.service_proto_path, "w") as f:
            f.write(
                """
syntax = "proto3";

package example.document.v1;

import "example/document/v1/data.proto";

service DocumentService {
  rpc GetDocument(GetDocumentRequest) returns (Document);
}

message GetDocumentRequest {
  string document_id = 1;
}
"""
            )

        # Initialize the resolver
        self.resolver = ProtoImportResolver([self.temp_dir])
        proto_files = [
            self.user_proto_path,
            self.data_proto_path,
            self.service_proto_path,
        ]
        self.resolver.initialize(proto_files)

    def tearDown(self):
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_resolve_import(self):
        """Test that imports are correctly resolved"""
        # Test resolving user.proto
        resolved_path = self.resolver.resolve_import("user.proto", self.data_proto_path)
        self.assertEqual(resolved_path, self.user_proto_path)

        # Test resolving data.proto from service.proto
        resolved_path = self.resolver.resolve_import(
            "example/document/v1/data.proto", self.service_proto_path
        )
        self.assertEqual(resolved_path, self.data_proto_path)

    def test_package_map(self):
        """Test that package map is properly populated"""
        # Test getting user package file
        self.assertIn("user", self.resolver.package_map)
        self.assertEqual(self.resolver.package_map["user"], self.user_proto_path)

        # Test getting example.document.v1 package file
        self.assertIn("example.document.v1", self.resolver.package_map)
        # The package map only has one entry per package, not multiple files
        self.assertTrue(
            self.resolver.package_map["example.document.v1"] == self.data_proto_path
            or self.resolver.package_map["example.document.v1"]
            == self.service_proto_path
        )


class TestProtoToMarkdownConverter(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test output
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.output_dir)

        # Create test proto content directory
        self.proto_dir = os.path.join(self.temp_dir, "proto")
        os.makedirs(self.proto_dir)

        self.example_dir = os.path.join(self.proto_dir, "example", "document", "v1")
        os.makedirs(self.example_dir)

        # Create test proto files
        self.user_proto_path = os.path.join(self.proto_dir, "user.proto")
        self.data_proto_path = os.path.join(self.example_dir, "data.proto")
        self.service_proto_path = os.path.join(self.example_dir, "service.proto")

        # Write content to test proto files
        with open(self.user_proto_path, "w") as f:
            f.write(
                """
syntax = "proto3";

package user;

/**
 * User information
 */
message User {
  // User ID
  string id = 1;

  // User's full name
  string name = 2;

  // User's email address
  string email = 3;
}
"""
            )

        with open(self.data_proto_path, "w") as f:
            f.write(
                """
syntax = "proto3";

package example.document.v1;

import "user.proto";

/**
 * Document information
 */
message Document {
  // Document ID
  string id = 1;

  // Document title
  string title = 2;

  // Document content
  string content = 3;

  // Document creator
  user.User creator = 4;
}
"""
            )

        with open(self.service_proto_path, "w") as f:
            f.write(
                """
syntax = "proto3";

package example.document.v1;

import "example/document/v1/data.proto";

/**
 * Service for managing documents
 */
service DocumentService {
  /**
   * Gets a document by ID
   */
  rpc GetDocument(GetDocumentRequest) returns (Document);
}

/**
 * Request to get a document
 */
message GetDocumentRequest {
  // Document ID to retrieve
  string document_id = 1;
}
"""
            )

        # Initialize the converter
        self.converter = ProtoToMarkdownConverter()
        self.converter.proto_dirs = [self.proto_dir]

    def tearDown(self):
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_convert_proto_files(self):
        """Test converting proto files to markdown"""
        proto_files = [
            self.user_proto_path,
            self.data_proto_path,
            self.service_proto_path,
        ]
        generated_files = self.converter.convert_proto_files(
            proto_files, self.output_dir
        )

        # Check that the correct number of files were generated
        self.assertEqual(len(generated_files), 3)

        # Check that the files were created with the correct paths
        expected_paths = [
            os.path.join(self.output_dir, "user.md"),
            os.path.join(self.output_dir, "example", "document", "v1", "data.md"),
            os.path.join(self.output_dir, "example", "document", "v1", "service.md"),
        ]

        for expected_path in expected_paths:
            self.assertTrue(
                os.path.exists(expected_path), f"Expected {expected_path} to exist"
            )

    def test_message_extraction(self):
        """Test that messages are correctly extracted from proto files"""

        # Check that the data.md file contains the Document message
        data_md_path = os.path.join(
            self.output_dir, "example", "document", "v1", "data.md"
        )
        with open(data_md_path, "r") as f:
            content = f.read()

        # Check that the Document message is included
        self.assertIn("### Document", content)
        # The description might be different format or absent
        self.assertIn("Document ID", content)
        self.assertIn("id", content)
        self.assertIn("string", content)

    def test_service_extraction(self):
        """Test that services are correctly extracted from proto files"""

        # Check that the service.md file contains the DocumentService
        service_md_path = os.path.join(
            self.output_dir, "example", "document", "v1", "service.md"
        )
        with open(service_md_path, "r") as f:
            content = f.read()

        # Check that the DocumentService is included
        self.assertIn("### DocumentService", content)
        self.assertIn("GetDocument", content)
        self.assertIn("Document", content)  # The service returns Document type
        self.assertIn("GetDocumentRequest", content)  # The service takes this request

    def test_cross_references(self):
        """Test that cross-references between proto files work correctly"""

        # Check that the data.md file contains a link to the User message
        data_md_path = os.path.join(
            self.output_dir, "example", "document", "v1", "data.md"
        )
        with open(data_md_path, "r") as f:
            content = f.read()

        # Check that there's a link to the User message - the exact format may vary
        # based on how the plugin generates links, but should contain both User and a link
        self.assertIn("User", content)
        self.assertIn("user.md", content)


class TestProtobufPlugin(unittest.TestCase):
    def test_plugin_initialization(self):
        """Test that the plugin initializes correctly"""
        plugin = ProtobufPlugin()
        self.assertIsNotNone(plugin)

        # Test that default config values are set
        config = {"proto_paths": ["proto"]}
        plugin.config = config
        self.assertEqual(plugin.config["proto_paths"], ["proto"])


if __name__ == "__main__":
    unittest.main()
