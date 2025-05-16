import os
import re
import logging

log = logging.getLogger("mkdocs.plugins.protobuf")


class ProtoImportResolver:
    """
    Class to handle resolving imports between proto files
    """

    def __init__(self, proto_dirs=None):
        """
        Initialize the import resolver

        Args:
            proto_dirs: List of directories containing proto files
        """
        self.proto_dirs = proto_dirs or []
        self.import_map = {}  # Maps import paths to actual file paths
        self.package_map = {}  # Maps package names to file paths
        self.cross_references = (
            {}
        )  # Maps message/service references to their file paths
        self.initialized = False

    def initialize(self, proto_files):
        """
        Initialize the resolver with a list of proto files

        Args:
            proto_files: List of absolute paths to proto files
        """
        log.debug("Initializing import resolver")

        # Reset maps
        self.import_map = {}
        self.package_map = {}
        self.cross_references = {}

        # Process all files to build import and package maps
        for proto_file in proto_files:
            self._process_proto_file(proto_file)

        self.initialized = True
        log.debug(
            f"Import resolver initialized with {len(self.import_map)} imports and {len(self.package_map)} packages"
        )

    def _process_proto_file(self, proto_file):
        """
        Process a single proto file to extract imports and package info

        Args:
            proto_file: Absolute path to a proto file
        """
        try:
            abs_file_path = os.path.abspath(proto_file)

            # Find the most specific proto directory that contains this file
            best_proto_dir = self._find_best_proto_dir(abs_file_path)

            # Extract import path for this file
            import_path = None
            if best_proto_dir:
                # Create an import path relative to the proto directory
                rel_path = os.path.relpath(abs_file_path, best_proto_dir)
                import_path = rel_path.replace("\\", "/")
            else:
                # Use the file name as import path
                import_path = os.path.basename(abs_file_path)

            # Add to import map
            self.import_map[import_path] = abs_file_path

            # Read the file to extract package and top-level definitions
            with open(abs_file_path, "r") as f:
                content = f.read()

            # Extract package name
            package_match = re.search(r"package\s+([^;]+);", content)
            if package_match:
                package = package_match.group(1)
                self.package_map[package] = abs_file_path

                # Extract message, enum, and service definitions
                self._extract_definitions(content, package, abs_file_path)

        except Exception as e:
            log.error(f"Error processing proto file {proto_file} for imports: {e}")

    def _find_best_proto_dir(self, file_path):
        """
        Find the most specific proto directory that contains this file

        Args:
            file_path: Absolute path to a proto file

        Returns:
            The absolute path to the best matching proto directory or None
        """
        best_proto_dir = None
        longest_common_path = ""

        for dir_path in self.proto_dirs:
            try:
                abs_dir_path = os.path.abspath(dir_path)
                # Check if the proto file is within this directory
                common_path = os.path.commonpath([abs_dir_path, file_path])
                if common_path == abs_dir_path and len(common_path) > len(
                    longest_common_path
                ):
                    best_proto_dir = abs_dir_path
                    longest_common_path = common_path
            except ValueError:
                # commonpath raises ValueError if paths are on different drives
                continue

        return best_proto_dir

    def _extract_definitions(self, content, package, file_path):
        """
        Extract top-level definitions from a proto file

        Args:
            content: Content of the proto file
            package: Package name
            file_path: Absolute path to the proto file
        """
        # Extract message definitions
        for match in re.finditer(r"message\s+(\w+)", content):
            message_name = match.group(1)
            qualified_name = f"{package}.{message_name}"
            self.cross_references[qualified_name] = file_path

        # Extract enum definitions
        for match in re.finditer(r"enum\s+(\w+)", content):
            enum_name = match.group(1)
            qualified_name = f"{package}.{enum_name}"
            self.cross_references[qualified_name] = file_path

        # Extract service definitions
        for match in re.finditer(r"service\s+(\w+)", content):
            service_name = match.group(1)
            qualified_name = f"{package}.{service_name}"
            self.cross_references[qualified_name] = file_path

    def resolve_import(self, import_path, importing_file=None):
        """
        Resolve an import path to an absolute file path

        Args:
            import_path: Import path from a proto file
            importing_file: Optional - the file doing the importing

        Returns:
            The absolute path to the imported proto file or None if not found
        """
        if not self.initialized:
            log.warning("Import resolver not initialized")
            return None

        # Direct lookup in import map
        if import_path in self.import_map:
            return self.import_map[import_path]

        # Try to resolve relative to the importing file
        if importing_file:
            importing_dir = os.path.dirname(os.path.abspath(importing_file))
            potential_path = os.path.normpath(os.path.join(importing_dir, import_path))

            if os.path.exists(potential_path):
                return potential_path

        # Try all proto directories
        for proto_dir in self.proto_dirs:
            potential_path = os.path.normpath(os.path.join(proto_dir, import_path))
            if os.path.exists(potential_path):
                return potential_path

        log.warning(f"Could not resolve import: {import_path}")
        return None

    def resolve_type_reference(self, type_ref):
        """
        Resolve a type reference to its file path

        Args:
            type_ref: Type reference like 'package.Message' or 'Message'

        Returns:
            The absolute path to the file containing the type or None if not found
        """
        if not self.initialized:
            log.warning("Import resolver not initialized")
            return None

        # Check if it's a qualified reference
        if "." in type_ref:
            if type_ref in self.cross_references:
                return self.cross_references[type_ref]

            # Try to match the package part
            parts = type_ref.split(".")
            for i in range(1, len(parts)):
                package = ".".join(parts[:i])
                if package in self.package_map:
                    return self.package_map[package]

        return None

    def get_markdown_link(self, type_ref, current_file_path, output_dir):
        """
        Generate a markdown link for a type reference

        Args:
            type_ref: Type reference like 'package.Message' or 'Message'
            current_file_path: The file path of the current markdown file
            output_dir: The output directory for markdown files

        Returns:
            A formatted markdown link or just the type reference if no link can be made
        """
        if not self.initialized or not type_ref or "." not in type_ref:
            return f"`{type_ref}`"

        target_file = self.resolve_type_reference(type_ref)
        if not target_file:
            return f"`{type_ref}`"

        # Determine the most specific proto dir for this target file
        best_proto_dir = self._find_best_proto_dir(target_file)

        if best_proto_dir:
            # Get the relative path from the proto directory
            rel_path = os.path.relpath(target_file, best_proto_dir)
            md_path = os.path.join(output_dir, os.path.splitext(rel_path)[0] + ".md")

            # Generate relative link from current markdown file to target markdown file
            current_dir = os.path.dirname(current_file_path)
            rel_link = os.path.relpath(md_path, current_dir)

            # Use just the type name for the link text
            type_name = type_ref.split(".")[-1]

            return f"[`{type_name}`]({rel_link.replace('\\', '/')})"

        return f"`{type_ref}`"
