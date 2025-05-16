# Cross-Reference Feature

This document explains how to use the MkDocs Protobuf Plugin's cross-reference feature to create clickable links between message types, enums, and services across your Protocol Buffer documentation.

## Overview

The cross-reference feature automatically creates clickable links between related Protocol Buffer elements:

- Message types referenced in field definitions
- Message types used in service methods (requests and responses)
- Nested messages and enums
- Types from imported proto files
- Service methods and their request/response types
- Enum values used in message fields

This makes it easier to navigate through your API documentation, especially for complex proto file structures with many interdependencies. The feature works across multiple files and supports various directory structures, including deeply nested package hierarchies.

## How It Works

The plugin builds an import resolver that:

1. Maps all proto files in your project
2. Identifies package names and qualified type names
3. Tracks cross-references between proto files
4. Creates relative links between markdown files

When generating markdown files, the plugin automatically:

- Converts field types that reference other messages to clickable links
- Converts service method request/response types to clickable links
- Maintains proper relative paths between files

## Example

When you have a message that references another message:

```proto
message User {
  string id = 1;
  Profile profile = 2;
}

message Profile {
  string bio = 1;
}
```

The generated markdown will include a clickable link from the `profile` field in the `User` message to the `Profile` message definition.

Similarly, for service methods:

```proto
service UserService {
  rpc CreateUser(CreateUserRequest) returns (User);
}

message CreateUserRequest {
  string name = 1;
}

message User {
  string id = 1;
  string name = 2;
}
```

The `CreateUserRequest` and `User` in the service method will be clickable links to their respective message definitions.

## Cross-Package References

The plugin excels at handling references across different package namespaces. For example, when one proto file imports and references types from another package:

```proto
// In example/document/v1/data.proto
package example.document.v1;

import "user.proto";

message Document {
  string id = 1;
  string content = 2;
  user.User creator = 3;  // References a type from another package
}
```

The plugin generates a proper link to the `User` message in the `user.proto` file, maintaining the correct relative path between the markdown files.

### Nested Directory Structures

For more complex directory structures, the plugin maintains proper navigation hierarchy. For example:

```
proto/
├── user.proto                    (package: user)
└── example/
    ├── common/
    │   └── v1/
    │       └── common.proto      (package: example.common.v1)
    └── document/
        └── v1/
            ├── data.proto        (package: example.document.v1)
            └── service.proto     (package: example.document.v1)
```

When a message in `example/document/v1/data.proto` references a type from `example/common/v1/common.proto`, the plugin generates a link with the correct relative path: `../../common/v1/common.md#TypeName`.

## External Type References

The plugin handles references to well-known types (like those from `google.protobuf.*`) and external dependencies:

1. **Well-Known Types**: Special handling for common types like `google.protobuf.Timestamp`
2. **External Dependencies**: Graceful handling when referenced types can't be found
3. **Custom Import Paths**: Support for customized import paths used in your proto files

## Anchor Links

For more precise navigation, the plugin creates anchor links to specific elements within a page:

1. **Message Links**: Links to specific messages with `#MessageName` anchors
2. **Nested Messages**: Links to nested messages with `#ParentMessage.NestedMessage` anchors
3. **Fields**: Links to specific fields with `#MessageName.field_name` anchors (when supported)
4. **Methods**: Links to service methods with `#ServiceName.MethodName` anchors

## Usage in Markdown

The cross-references appear as clickable links in the generated markdown:

- Message field types: `string name = 1;` → `name` | `string` | `1` | Description
- Message references: `User user = 1;` → `name` | `User` | `1` | Description
- External package refs: `other.Type field = 1;` → `field` | `other.Type` | `1` | Description
