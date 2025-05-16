# MkDocs Protobuf Plugin

A MkDocs plugin that converts Protocol Buffer (`.proto`) files to Markdown documentation.

## Features

- Converts `.proto` files to Markdown documentation
- Watches `.proto` files for changes in serve mode and automatically updates the generated Markdown
- Preserves directory structure of proto files in the generated documentation
- Supports nested messages, enums, and services
- Extracts comments and field descriptions (block, line, and inline comments)
- Handles proto imports
- Creates clickable cross-references between message types and services
- Automatically updates MkDocs navigation with generated files
- Compatible with mkdocs-static-i18n for multi-language documentation
- Smart file caching to prevent unnecessary rebuilds
- Provides comprehensive error handling

## Installation

```bash
pip install mkdocs-protobuf-plugin
```

## Usage

Add the plugin to your `mkdocs.yml` file:

```yaml
plugins:
  - search
  - protobuf:
      proto_paths:
        - path/to/proto/files
        - path/to/another/proto/file.proto
      output_dir: docs/generated  # Optional, defaults to docs/generated
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `proto_paths` | List of paths to proto files or directories containing proto files | `[]` |
| `output_dir` | Directory where generated markdown files will be stored (relative to docs_dir) | `docs/generated` |

### Navigation Integration

The plugin automatically updates your MkDocs navigation configuration to include the generated documentation files. It preserves the directory structure of your proto files in the navigation. If your `mkdocs.yml` already has an "API Reference" or "API" section in the navigation, the plugin will update that section. Otherwise, it will add a new "API Reference" section.

### Internationalization Support

The plugin is compatible with [mkdocs-static-i18n](https://github.com/ultrabug/mkdocs-static-i18n) for multilingual documentation. When both plugins are used together, the protobuf plugin will:

1. Detect the presence of the i18n plugin
2. Extract language configuration from the mkdocs.yml
3. Organize proto documentation within each language's navigation structure
4. Respect custom translations specified in i18n configuration

Example configuration with i18n support:

```yaml
plugins:
  - search
  - i18n:
      default_language: en
      languages:
        en: English
        fr: Français
        es: Español
      nav_translations:
        fr:
          API Reference: Référence d'API
          Overview: Vue d'ensemble
        es:
          API Reference: Referencia de API
          Overview: Descripción general
  - protobuf:
      proto_paths:
        - proto/
      output_dir: api
```

A full example configuration can be found in the [examples/sample-auto-i18n-mkdocs.yml](./examples/sample-auto-i18n-mkdocs.yml).

## Generated Documentation Structure

The plugin generates Markdown files with the following structure:

- Protocol Documentation: filename
  - Package
  - Messages
    - Message fields with types, numbers, and descriptions
  - Enums
    - Enum values with numbers and descriptions
  - Services
    - Service methods with request/response types and descriptions

## Example

For a proto file like:

```protobuf
syntax = "proto3";

package example;

message Person {
  string name = 1;  // Person's full name
  int32 age = 2;    // Age in years
}

enum Status {
  UNKNOWN = 0;  // Status unknown
  ACTIVE = 1;   // User is active
  INACTIVE = 2; // User is inactive
}
```

The plugin will generate:

```markdown
# Protocol Documentation: example.proto

## Package: `example`

## Messages

### Person

| Field | Type | Number | Description |
|-------|------|--------|-------------|
| name | string | 1 | Person's full name |
| age | int32 | 2 | Age in years |

## Enums

### Status

| Name | Number | Description |
|------|--------|-------------|
| UNKNOWN | 0 | Status unknown |
| ACTIVE | 1 | User is active |
| INACTIVE | 2 | User is inactive |
```

## License

MIT
