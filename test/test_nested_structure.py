import unittest
import tempfile
import os
import shutil

from mkdocs_protobuf_plugin.converter import ProtoToMarkdownConverter
from mkdocs_protobuf_plugin.import_resolver import ProtoImportResolver


class TestNestedStructure(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test proto files
        self.temp_dir = tempfile.mkdtemp()

        # Create a nested directory structure for proto files
        self.example_dir = os.path.join(
            self.temp_dir, "proto", "example", "document", "v1"
        )
        os.makedirs(self.example_dir)

        self.user_dir = os.path.join(self.temp_dir, "proto", "example", "user", "v1")
        os.makedirs(self.user_dir)

        self.common_dir = os.path.join(
            self.temp_dir, "proto", "example", "common", "v1"
        )
        os.makedirs(self.common_dir)

        # Create output directory
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.output_dir)

        # Create proto files
        self.common_proto_path = os.path.join(self.common_dir, "common.proto")
        with open(self.common_proto_path, "w") as f:
            f.write(
                """
syntax = "proto3";

package example.common.v1;

/**
 * Common types used across services
 */

message Timestamp {
  // Seconds since epoch
  int64 seconds = 1;

  // Nanoseconds
  int32 nanos = 2;
}

message Status {
  // Status code
  int32 code = 1;

  // Status message
  string message = 2;
}
"""
            )

        self.user_proto_path = os.path.join(self.user_dir, "user.proto")
        with open(self.user_proto_path, "w") as f:
            f.write(
                """
syntax = "proto3";

package example.user.v1;

import "example/common/v1/common.proto";

/**
 * User profile information
 */
message User {
  // User ID
  string id = 1;

  // User's full name
  string name = 2;

  // User's email address
  string email = 3;

  // User creation time
  example.common.v1.Timestamp created_at = 4;
}

/**
 * User service for managing user profiles
 */
service UserService {
  /**
   * Creates a new user
   */
  rpc CreateUser(CreateUserRequest) returns (User);

  /**
   * Gets a user by ID
   */
  rpc GetUser(GetUserRequest) returns (User);
}

message CreateUserRequest {
  // User to create
  User user = 1;
}

message GetUserRequest {
  // User ID to retrieve
  string user_id = 1;
}
"""
            )

        self.document_proto_path = os.path.join(self.example_dir, "document.proto")
        with open(self.document_proto_path, "w") as f:
            f.write(
                """
syntax = "proto3";

package example.document.v1;

import "example/user/v1/user.proto";
import "example/common/v1/common.proto";

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
  example.user.v1.User creator = 4;

  // Creation time
  example.common.v1.Timestamp created_at = 5;

  // Last modified time
  example.common.v1.Timestamp updated_at = 6;
}

/**
 * Document service for managing documents
 */
service DocumentService {
  /**
   * Creates a new document
   */
  rpc CreateDocument(CreateDocumentRequest) returns (Document);

  /**
   * Gets a document by ID
   */
  rpc GetDocument(GetDocumentRequest) returns (Document);

  /**
   * Updates an existing document
   */
  rpc UpdateDocument(UpdateDocumentRequest) returns (Document);

  /**
   * Deletes a document
   */
  rpc DeleteDocument(DeleteDocumentRequest) returns (DeleteResponse);
}

message CreateDocumentRequest {
  // Document to create
  Document document = 1;
}

message GetDocumentRequest {
  // Document ID to retrieve
  string document_id = 1;
}

message UpdateDocumentRequest {
  // Document to update
  Document document = 1;
}

message DeleteDocumentRequest {
  // Document ID to delete
  string document_id = 1;
}

message DeleteResponse {
  // Operation status
  example.common.v1.Status status = 1;
}
"""
            )

        # Initialize converter
        self.converter = ProtoToMarkdownConverter()
        self.converter.proto_dirs = [os.path.join(self.temp_dir, "proto")]

    def tearDown(self):
        # Clean up temp directory
        shutil.rmtree(self.temp_dir)

    def test_nested_imports_resolution(self):
        """Test that imports in nested directories are correctly resolved"""
        # Initialize the import resolver
        resolver = ProtoImportResolver([os.path.join(self.temp_dir, "proto")])
        proto_files = [
            self.common_proto_path,
            self.user_proto_path,
            self.document_proto_path,
        ]
        resolver.initialize(proto_files)

        # Test resolving imports from document.proto
        user_import = resolver.resolve_import(
            "example/user/v1/user.proto", self.document_proto_path
        )
        self.assertEqual(user_import, self.user_proto_path)

        common_import = resolver.resolve_import(
            "example/common/v1/common.proto", self.document_proto_path
        )
        self.assertEqual(common_import, self.common_proto_path)

    def test_nested_directory_conversion(self):
        """Test that proto files in nested directories are converted correctly"""
        proto_files = [
            self.common_proto_path,
            self.user_proto_path,
            self.document_proto_path,
        ]
        generated_files = self.converter.convert_proto_files(
            proto_files, self.output_dir
        )

        # Check that the correct number of files were generated
        self.assertEqual(len(generated_files), 3)

        # Check that the files were created with the correct paths
        expected_paths = [
            os.path.join(self.output_dir, "example", "common", "v1", "common.md"),
            os.path.join(self.output_dir, "example", "user", "v1", "user.md"),
            os.path.join(self.output_dir, "example", "document", "v1", "document.md"),
        ]

        for expected_path in expected_paths:
            self.assertTrue(
                os.path.exists(expected_path), f"Expected {expected_path} to exist"
            )

    def test_nested_cross_references(self):
        """Test that cross-references between nested proto files work correctly"""

        # Check that document.md has proper links to user.md and common.md
        document_md_path = os.path.join(
            self.output_dir, "example", "document", "v1", "document.md"
        )
        with open(document_md_path, "r") as f:
            content = f.read()

        # Check for references to the User and Timestamp messages
        # The exact format of links may vary, but they should include references to the user and common directories
        self.assertIn("User", content)
        self.assertIn("user.md", content)
        self.assertIn(
            "common/v1/common", content.lower()
        )  # Check for any reference to the common proto

        # Check that user.md has proper links to common.md
        user_md_path = os.path.join(self.output_dir, "example", "user", "v1", "user.md")
        with open(user_md_path, "r") as f:
            content = f.read()

        # Check for references to the Timestamp message
        self.assertIn("Timestamp", content)

    def test_navigation_structure(self):
        """Test that the navigation structure is built correctly"""

        # Check that all necessary directories were created
        expected_dirs = [
            os.path.join(self.output_dir, "example"),
            os.path.join(self.output_dir, "example", "common"),
            os.path.join(self.output_dir, "example", "common", "v1"),
            os.path.join(self.output_dir, "example", "user"),
            os.path.join(self.output_dir, "example", "user", "v1"),
            os.path.join(self.output_dir, "example", "document"),
            os.path.join(self.output_dir, "example", "document", "v1"),
        ]

        for expected_dir in expected_dirs:
            self.assertTrue(
                os.path.isdir(expected_dir),
                f"Expected directory {expected_dir} to exist",
            )


if __name__ == "__main__":
    unittest.main()
