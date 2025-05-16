# MkDocs Protobuf Plugin Architecture

This document provides technical details about the internal architecture of the MkDocs Protobuf Plugin, useful for contributors and those who want to understand how the plugin works.

## Component Overview

The plugin is composed of four main components:

1. **Plugin Core** (`plugin.py`): Integrates with MkDocs and handles high-level operations
2. **Proto Converter** (`converter.py`): Parses proto files and converts them to Markdown
3. **Import Resolver** (`import_resolver.py`): Resolves imports between proto files
4. **Init Module** (`__init__.py`): Provides entry points and plugin registration

Here's a high-level diagram of how they interact:

```
                   ┌─────────────┐
                   │   MkDocs    │
                   └──────┬──────┘
                          │
                          ▼
┌───────────────────────────────────────────┐
│               plugin.py                   │
│                                           │
│  ┌─────────────────┐ ┌─────────────────┐  │
│  │  On_config()    │ │  On_files()     │  │
│  └─────────────────┘ └─────────────────┘  │
│                                           │
│  ┌─────────────────┐ ┌─────────────────┐  │
│  │  Watch Handler  │ │  Nav Builder    │  │
│  └─────────────────┘ └─────────────────┘  │
└───────────────────────┬───────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────┐
│             converter.py                  │
│                                           │
│  ┌─────────────────┐ ┌─────────────────┐  │
│  │  Proto Parser   │ │ Markdown Builder │  │
│  └─────────────────┘ └─────────────────┘  │
└────────────┬──────────────────────┬───────┘
             │                      │
             ▼                      ▼
┌────────────────────┐    ┌─────────────────────┐
│ import_resolver.py │    │ Generated Markdown  │
└────────────────────┘    └─────────────────────┘
```

## Execution Flow

1. **Initialization**:
   - Plugin registered via entry points in `setup.py`
   - MkDocs loads the plugin during startup

2. **Configuration**:
   - `on_config()` reads plugin configuration settings
   - Sets up proto paths and output directories

3. **Build Process**:
   - `on_files()` scans proto files in the configured paths
   - Initializes the import resolver with all proto files
   - Converts proto files to markdown using the converter
   - Adds generated markdown files to MkDocs file collection

4. **File Watching** (during `serve`):
   - Sets up file watchers for proto directories
   - When proto files change, regenerates the corresponding markdown
   - Updates the navigation structure as needed

## Key Classes and Functions

### Plugin Core (`plugin.py`)

```python
class ProtobufPlugin(BasePlugin):
    """Main plugin class that integrates with MkDocs."""
    
    # Configuration schema
    config_scheme = (
        ('proto_paths', Type(list, default=[])),
        ('output_dir', Type(str, default='api')),
        ('include_navbar', Type(bool, default=True)),
        # Additional config options...
    )
    
    def on_config(self, config):
        """Set up the plugin when MkDocs configuration loads."""
        # Initialize converter, paths, etc.
        
    def on_files(self, files, config):
        """Process proto files and generate markdown."""
        # Scan proto files, convert them, add to files collection
        
    def _update_navigation(self, config, output_dir, generated_files):
        """Update the navigation structure with generated files."""
        # Build navigation entries for the generated files
```

### Proto Converter (`converter.py`)

```python
class ProtoToMarkdownConverter:
    """Handles conversion from proto files to markdown."""
    
    def convert_proto_files(self, proto_files, output_dir):
        """Convert a list of proto files to markdown."""
        # Batch process multiple proto files
        
    def _convert_proto_file(self, proto_file, output_dir):
        """Convert a single proto file to markdown."""
        # Parse proto file and convert to markdown
        
    def _extract_package_info(self, content):
        """Extract package information from proto content."""
        # Parse package declaration
        
    def _extract_imports(self, content):
        """Extract import statements from proto content."""
        # Parse import declarations
        
    def _extract_messages(self, content):
        """Extract message definitions from proto content."""
        # Parse message declarations and nested messages
        
    def _extract_services(self, content):
        """Extract service definitions from proto content."""
        # Parse service declarations and methods
        
    def _build_markdown(self, proto_file, package, imports, messages, services):
        """Build markdown content from parsed proto elements."""
        # Construct the markdown document
```

### Import Resolver (`import_resolver.py`)

```python
class ProtoImportResolver:
    """Resolves imports between proto files."""
    
    def initialize(self, proto_files):
        """Initialize the resolver with a list of proto files."""
        # Build import and package maps
        
    def resolve_import_path(self, import_path, importing_file):
        """Resolve an import statement to an actual file path."""
        # Find the file corresponding to an import statement
        
    def get_package_file(self, package_name):
        """Get the file path for a package name."""
        # Find the file containing a package declaration
        
    def create_cross_reference_link(self, ref_type, current_file, target_file):
        """Create a markdown link between related proto elements."""
        # Generate relative links between files
```

## Code Parsing Strategy

The plugin uses regular expressions and string parsing to extract information from proto files. While not a full parser, it handles the most common proto constructs:

1. **Package Declaration**: 
   - Regex: `r'package\s+([a-zA-Z0-9_.]+)\s*;'`

2. **Import Statements**: 
   - Regex: `r'import\s+(?:"([^"]+)"|\'([^\']+)\')\s*;'`

3. **Message Definitions**: 
   - Multi-stage parsing with nested message handling

4. **Service Definitions**: 
   - Method extraction with request/response types

5. **Documentation Comments**:
   - Support for both `/** doc */` and `// doc` styles

## Directory Structure Handling

The plugin maintains the directory structure of proto files in the generated documentation:

1. Takes the proto file path relative to the proto base directory
2. Creates corresponding directories in the output location
3. Places markdown files in matching paths

For example:
- Proto: `proto/example/document/v1/service.proto`
- Markdown: `docs/api/example/document/v1/service.md`

This preserves the logical structure and helps with proper import resolution.

## Cross-Reference System

The cross-reference system creates clickable links between related proto elements:

1. **Link Generation**:
   - When a message references another type, creates a relative link
   - Computes proper path based on file locations

2. **Type Resolution**:
   - Maps fully qualified type names to their file locations
   - Handles both same-package and cross-package references

3. **Anchor Creation**:
   - Creates anchors for messages, enums, services, and methods
   - Uses element names as anchor points

## Future Architecture Improvements

1. **Proper Parser**: Replace regex parsing with a formal proto parser
2. **Component Decoupling**: Further separate concerns between components
3. **Caching**: Add file-based caching for improved performance
4. **Plugin Extension**: Add plugin hooks for customized proto handling
