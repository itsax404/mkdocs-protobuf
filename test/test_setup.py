#!/usr/bin/env python3
"""
Setup script for testing the MkDocs Protobuf Plugin.
This script creates sample proto files and sets up a test MkDocs project.
"""
import os
import sys
import subprocess
# Removed unused import: shutil, Path

# Sample proto file content
SAMPLE_USER_PROTO = """
syntax = "proto3";

package user;

/**
 * User service for managing user accounts.
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
  
  /**
   * Lists all users
   */
  rpc ListUsers(ListUsersRequest) returns (ListUsersResponse);
}

/**
 * User resource
 */
message User {
  /** Unique user ID */
  string id = 1;
  
  /** User's full name */
  string name = 2;
  
  /** User's email address */
  string email = 3;
  
  /** User's creation timestamp */
  int64 created_at = 4;
  
  /** User's last update timestamp */
  int64 updated_at = 5;
}

/**
 * Request to create a new user
 */
message CreateUserRequest {
  /** User's name */
  string name = 1;
  
  /** User's email */
  string email = 2;
}

/**
 * Request to get a user by ID
 */
message GetUserRequest {
  /** User ID */
  string id = 1;
}

/**
 * Request to list users
 */
message ListUsersRequest {
  /** Page size */
  int32 page_size = 1;
  
  /** Page token */
  string page_token = 2;
}

/**
 * Response to list users
 */
message ListUsersResponse {
  /** Users */
  repeated User users = 1;
  
  /** Next page token */
  string next_page_token = 2;
}
"""

SAMPLE_DATA_PROTO = """
syntax = "proto3";

package example.document.v1;

import "user.proto";

/**
 * Document data types for the document management service.
 */

/**
 * Document resource
 */
message Document {
  /** Unique document ID */
  string id = 1;
  
  /** Document title */
  string title = 2;
  
  /** Document content */
  string content = 3;
  
  /** Creator reference */
  user.User creator = 4;
  
  /** Document creation timestamp */
  int64 created_at = 5;
  
  /** Document last update timestamp */
  int64 updated_at = 6;
  
  /** Document tags */
  repeated string tags = 7;
  
  /** Document status */
  DocumentStatus status = 8;
  
  /** Document metadata */
  DocumentMetadata metadata = 9;
}

/**
 * Document status enum
 */
enum DocumentStatus {
  /** Status unknown */
  DOCUMENT_STATUS_UNSPECIFIED = 0;
  
  /** Document is a draft */
  DOCUMENT_STATUS_DRAFT = 1;
  
  /** Document is published */
  DOCUMENT_STATUS_PUBLISHED = 2;
  
  /** Document is archived */
  DOCUMENT_STATUS_ARCHIVED = 3;
}

/**
 * Document metadata
 */
message DocumentMetadata {
  /** Author information */
  string author_name = 1;
  
  /** Original filename */
  string original_filename = 2;
  
  /** File size in bytes */
  int64 size_bytes = 3;
  
  /** MIME type */
  string mime_type = 4;
  
  /** Language code (BCP-47) */
  string language_code = 5;
}

/**
 * Search request
 */
message SearchDocumentRequest {
  /** Search query */
  string query = 1;
  
  /** Maximum number of results */
  int32 max_results = 2;
  
  /** Filter by document status */
  DocumentStatus status_filter = 3;
  
  /** Filter by tags */
  repeated string tag_filters = 4;
}

/**
 * Search response
 */
message SearchDocumentResponse {
  /** Matching documents */
  repeated Document documents = 1;
  
  /** Total results count */
  int32 total_count = 2;
}
"""

SAMPLE_SERVICE_PROTO = """
syntax = "proto3";

package example.document.v1;

import "example/document/v1/data.proto";

/**
 * Document service for managing and searching documents.
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
  rpc DeleteDocument(DeleteDocumentRequest) returns (DeleteDocumentResponse);
  
  /**
   * Lists documents with filtering
   */
  rpc ListDocuments(ListDocumentsRequest) returns (ListDocumentsResponse);
  
  /**
   * Searches documents based on content and metadata
   */
  rpc SearchDocuments(SearchDocumentRequest) returns (SearchDocumentResponse);
}

/**
 * Request to create a document
 */
message CreateDocumentRequest {
  /** Document title */
  string title = 1;
  
  /** Document content */
  string content = 2;
  
  /** Creator ID */
  string creator_id = 3;
  
  /** Document tags */
  repeated string tags = 4;
  
  /** Document metadata */
  DocumentMetadata metadata = 5;
}

/**
 * Request to get a document
 */
message GetDocumentRequest {
  /** Document ID */
  string id = 1;
}

/**
 * Request to update a document
 */
message UpdateDocumentRequest {
  /** Document ID */
  string id = 1;
  
  /** Updated title */
  string title = 2;
  
  /** Updated content */
  string content = 3;
  
  /** Updated tags */
  repeated string tags = 4;
  
  /** Updated status */
  DocumentStatus status = 5;
  
  /** Updated metadata */
  DocumentMetadata metadata = 6;
}

/**
 * Request to delete a document
 */
message DeleteDocumentRequest {
  /** Document ID */
  string id = 1;
}

/**
 * Response to delete a document
 */
message DeleteDocumentResponse {
  /** Successful deletion */
  bool success = 1;
}

/**
 * Request to list documents
 */
message ListDocumentsRequest {
  /** Page size */
  int32 page_size = 1;
  
  /** Page token */
  string page_token = 2;
  
  /** Filter by document status */
  DocumentStatus status_filter = 3;
  
  /** Filter by creator ID */
  string creator_id = 4;
}

/**
 * Response to list documents
 */
message ListDocumentsResponse {
  /** Documents */
  repeated Document documents = 1;
  
  /** Next page token */
  string next_page_token = 2;
  
  /** Total count */
  int32 total_count = 3;
}
"""

SAMPLE_TEST_PROTO = """
syntax = "proto3";

package test;

/**
 * Test message
 */
message TestMessage {
  /** Sample string field */
  string name = 1;
  
  /** Sample integer field */
  int32 count = 2;
}
"""


def setup_test_project(project_dir):
    """
    Set up a test project with proto files in the given directory.

    Args:
        project_dir: The directory to set up the test project in
    """
    # Create proto directory
    proto_dir = os.path.join(project_dir, "proto")
    os.makedirs(proto_dir, exist_ok=True)

    # Create nested directory structure
    nested_proto_dir = os.path.join(proto_dir, "example", "document", "v1")
    os.makedirs(nested_proto_dir, exist_ok=True)

    # Create proto files
    with open(os.path.join(proto_dir, "user.proto"), "w") as f:
        f.write(SAMPLE_USER_PROTO)

    with open(os.path.join(proto_dir, "test.proto"), "w") as f:
        f.write(SAMPLE_TEST_PROTO)

    with open(os.path.join(nested_proto_dir, "data.proto"), "w") as f:
        f.write(SAMPLE_DATA_PROTO)

    with open(os.path.join(nested_proto_dir, "service.proto"), "w") as f:
        f.write(SAMPLE_SERVICE_PROTO)

    # Create docs directory
    docs_dir = os.path.join(project_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)

    # Create mkdocs.yml
    with open(os.path.join(project_dir, "mkdocs.yml"), "w") as f:
        f.write(
            """
site_name: MkDocs Protobuf Plugin Test
site_description: Test site for the MkDocs Protobuf Plugin

theme:
  name: material

plugins:
  - search
  - protobuf:
      proto_paths:
        - proto/
      output_dir: api

markdown_extensions:
  - admonition
  - pymdownx.highlight
  - pymdownx.superfences
"""
        )

    # Create index.md
    with open(os.path.join(docs_dir, "index.md"), "w") as f:
        f.write(
            """
# MkDocs Protobuf Plugin Test

This is a test site for the MkDocs Protobuf Plugin.

## API Reference

The API documentation is automatically generated from Proto files.

Check out the [API Reference](api/index.md) section.
"""
        )

    print(f"Test project set up in {project_dir}")
    return project_dir


def main():
    """
    Main function to set up a test project.
    """
    if len(sys.argv) < 2:
        project_dir = os.path.join(os.getcwd(), "test-project")
    else:
        project_dir = sys.argv[1]

    setup_test_project(project_dir)

    # Run mkdocs build
    try:
        subprocess.run(["mkdocs", "build"], cwd=project_dir, check=True)
        print("MkDocs build successful!")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error building MkDocs site: {e}")


if __name__ == "__main__":
    main()
