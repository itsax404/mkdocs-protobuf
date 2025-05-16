import os
import re
import logging
from pathlib import Path
from .import_resolver import ProtoImportResolver

METHOD_PATTERN = r"rpc\s+(\w+)\s*\(\s*(\w+(?:\.\w+)*)\s*\)\s*returns\s*\(\s*(\w+(?:\.\w+)*)\s*\)(?:\s*{(.*?)})?;(?:\s*//\s*(.*))?"  # noqa: E501

log = logging.getLogger("mkdocs.plugins.protobuf")

FIELD_PATTERN = r"(optional|required|repeated)?\s*(\w+(?:\.\w+)*)\s+(\w+)\s*=\s*(\d+)(?:\s*\[(.*?)\])?;(?:\s*//\s*(.*))?"


class ProtoToMarkdownConverter:
    def __init__(self):
        # Initialize any parser configuration here
        self.import_resolver = ProtoImportResolver()
        self.output_dir = None

    def convert_proto_files(self, proto_files, output_dir):
        """
        Convert a list of proto files to markdown and save them in the output directory
        Returns a list of generated markdown files
        """
        self.output_dir = output_dir

        # First, initialize the import resolver with all proto files
        if hasattr(self, "proto_dirs"):
            self.import_resolver.proto_dirs = self.proto_dirs
        self.import_resolver.initialize(proto_files)

        # Then convert each file to markdown
        generated_files = []
        for proto_file in proto_files:
            try:
                output_file = self.convert_proto_file(proto_file, output_dir)
                if output_file:
                    generated_files.append(output_file)
            except Exception as e:
                log.error(f"Error converting proto file {proto_file}: {str(e)}")
                # Add more detailed error info for debugging
                import traceback

                log.debug(f"Traceback: {traceback.format_exc()}")
        return generated_files

    def convert_proto_file(self, proto_file, output_dir):
        """
        Convert a single proto file to markdown
        Returns the output file path
        """
        log.info(f"Converting proto file: {proto_file}")

        try:
            # Read the proto file
            with open(proto_file, "r") as f:
                proto_content = f.read()

            # Parse and convert to markdown
            proto_path = Path(proto_file)
            markdown_content = self._proto_to_markdown(
                proto_content, proto_path.name, proto_file, output_dir
            )

            # Get absolute paths to work with
            abs_file_path = os.path.abspath(proto_file)

            # Find the most specific proto directory that contains this file
            best_proto_dir = None
            longest_common_path = ""

            if hasattr(self, "proto_dirs"):
                for dir_path in self.proto_dirs:
                    try:
                        abs_dir_path = os.path.abspath(dir_path)
                        # Check if the proto file is within this directory
                        common_path = os.path.commonpath([abs_dir_path, abs_file_path])
                        if common_path == abs_dir_path and len(common_path) > len(
                            longest_common_path
                        ):
                            best_proto_dir = abs_dir_path
                            longest_common_path = common_path
                    except ValueError:
                        # commonpath raises ValueError if paths are on different drives
                        continue

            # Determine output file path, preserving directory structure
            if best_proto_dir:
                # Get the relative path from the proto directory to maintain structure
                rel_path = os.path.relpath(abs_file_path, best_proto_dir)
                # Create the output file path with the preserved directory structure
                output_file = os.path.join(
                    output_dir, os.path.splitext(rel_path)[0] + ".md"
                )
            else:
                # If not in a watched directory, put it in the root of output_dir
                filename = os.path.basename(proto_file)
                base_name = os.path.splitext(filename)[0]
                output_file = os.path.join(output_dir, base_name + ".md")

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # Write markdown content
            with open(output_file, "w") as f:
                f.write(markdown_content)

            log.info(f"Generated markdown file: {output_file}")

            return output_file

        except Exception as e:
            log.error(f"Error converting {proto_file}: {str(e)}")
            return None

    def _proto_to_markdown(
        self, proto_content, filename, current_proto_file=None, output_dir=None
    ):
        """
        Convert proto content to markdown format

        Args:
            proto_content: The content of the proto file
            filename: The filename (for display purposes)
            current_proto_file: The absolute path to the current proto file (for resolving imports)
            output_dir: The output directory for markdown files
        """
        current_output_file = None
        if current_proto_file and output_dir:
            # Determine the output file path for the current proto file
            best_proto_dir = self._find_best_proto_dir(current_proto_file)
            if best_proto_dir:
                # Get the relative path from the proto directory
                rel_path = os.path.relpath(current_proto_file, best_proto_dir)
                current_output_file = os.path.join(
                    output_dir, os.path.splitext(rel_path)[0] + ".md"
                )
            else:
                # If not in a watched directory, just use the basename
                basename = os.path.basename(current_proto_file)
                current_output_file = os.path.join(
                    output_dir, os.path.splitext(basename)[0] + ".md"
                )

        markdown = f"# Protocol Documentation: {filename}\n\n"

        # Extract package name
        package_match = re.search(r"package\s+([^;]+);", proto_content)
        if package_match:
            package = package_match.group(1)
            markdown += f"## Package: `{package}`\n\n"

        # Extract imports
        imports = self._extract_imports(proto_content)
        if imports:
            markdown += "## Imports\n\n"
            for imp in imports:
                markdown += f"- `{imp}`\n"
            markdown += "\n"

        # Extract messages
        messages = self._extract_messages(proto_content)
        if messages:
            markdown += "## Messages\n\n"
            # First process top-level messages (those without a dot in the name)
            for name, content in sorted(messages.items()):
                if "." not in name:  # Only top-level messages
                    markdown += self._format_message_markdown(
                        name, content, messages, current_proto_file, current_output_file
                    )

        # Extract enums
        enums = self._extract_enums(proto_content)
        if enums:
            markdown += "## Enums\n\n"
            for name, content in sorted(enums.items()):
                markdown += f"### {name}\n\n"

                # Extract enum comment if available
                comment_match = re.search(r"/\*\*(.*?)\*/", content, re.DOTALL)
                if comment_match:
                    comment = comment_match.group(1).strip()
                    markdown += f"{comment}\n\n"

                # Extract enum values
                values = self._extract_enum_values(content)
                if values:
                    markdown += "| Name | Number | Description |\n"
                    markdown += "|------|--------|-------------|\n"
                    for value in values:
                        markdown += f"| {value['name']} | {value['number']} | {value.get('description', '')} |\n"
                    markdown += "\n"

        # Extract services
        services = self._extract_services(proto_content)
        if services:
            markdown += "## Services\n\n"
            for name, content in sorted(services.items()):
                markdown += f"### {name}\n\n"

                # Extract service comment if available
                comment_match = re.search(r"/\*\*(.*?)\*/", content, re.DOTALL)
                if comment_match:
                    comment = comment_match.group(1).strip()
                    markdown += f"{comment}\n\n"

                # Extract service methods with a simpler approach
                methods = []

                # First, preprocess content to find comments
                service_content_lines = content.splitlines()
                # commented_lines dictionary was unused - removing

                doc_comment = None
                for i, line in enumerate(service_content_lines):
                    # Check for doc comments start
                    if "/**" in line:
                        doc_comment = line
                        j = i + 1
                        # Collect all comment lines
                        while (
                            j < len(service_content_lines)
                            and "*/" not in service_content_lines[j]
                        ):
                            doc_comment += service_content_lines[j]
                            j += 1
                        if j < len(service_content_lines):
                            doc_comment += service_content_lines[j]

                    # Check for rpc method
                    if "rpc " in line and "(" in line and "returns" in line:
                        method_line = line
                        # If the line doesn't end with a semicolon, collect all parts
                        if ";" not in line:
                            j = i + 1
                            while (
                                j < len(service_content_lines)
                                and ";" not in service_content_lines[j]
                            ):
                                method_line += " " + service_content_lines[j]
                                j += 1
                            if j < len(service_content_lines):
                                method_line += " " + service_content_lines[j]

                        # Now parse the method line
                        method_match = re.search(
                            r"rpc\s+(\w+)\s*\(\s*(\w+(?:\.\w+)*)\s*\)\s*returns\s*\(\s*(\w+(?:\.\w+)*)\s*\)",
                            method_line,
                        )
                        if method_match:
                            method_name = method_match.group(1)
                            request_type = method_match.group(2)
                            response_type = method_match.group(3)

                            # Get comment from doc comment or inline comment
                            description = ""
                            if doc_comment:
                                doc_text = re.search(
                                    r"/\*\*(.*?)\*/", doc_comment, re.DOTALL
                                )
                                if doc_text:
                                    description = (
                                        doc_text.group(1).strip().replace("\n", " ")
                                    )
                                    description = re.sub(r"^\s*\*\s*", "", description)
                                # Reset doc comment after use
                                doc_comment = None

                            # Check for inline comment
                            inline_match = re.search(r";\s*//\s*(.*)$", method_line)
                            if inline_match and not description:
                                description = inline_match.group(1).strip()

                            methods.append(
                                {
                                    "name": method_name,
                                    "request": request_type,
                                    "response": response_type,
                                    "description": description,
                                }
                            )

                if methods:
                    markdown += self._create_method_table(methods, current_output_file, current_proto_file)

        return markdown

    def _create_method_table(self, methods, current_proto_file, current_output_file):
        markdown = "| Method | Request | Response | Description |\n"
        markdown += "|--------|---------|----------|-------------|\n"
        for method in methods:
            request = method["request"]
            response = method["response"]

            # Use import resolver to create links if possible
            if (
                current_proto_file
                and current_output_file
                and self.import_resolver.initialized
            ):
                request = self.import_resolver.get_markdown_link(
                    request, current_output_file, self.output_dir
                )
                response = self.import_resolver.get_markdown_link(
                    response, current_output_file, self.output_dir
                )
            else:
                request = f"`{request}`"
                response = f"`{response}`"

            markdown += f"| {method['name']} | {request} | {response} | {method['description']} |\n"
        markdown += "\n"
        return markdown

    def _format_message_markdown(
        self, name, content, all_messages, current_proto_file=None, output_file=None
    ):
        """
        Format a message and its nested messages into markdown

        Args:
            name: The message name
            content: The message content
            all_messages: Dictionary of all messages in the proto file
            current_proto_file: The proto file containing this message, for resolving imports
            output_file: The output markdown file path, for creating proper links
        """
        markdown = f"### {name}\n\n"

        # Extract message comment if available
        comment_match = re.search(r"/\*\*(.*?)\*/", content, re.DOTALL)
        if comment_match:
            comment = comment_match.group(1).strip()
            # Clean up multi-line comments by removing * prefixes and normalizing whitespace
            comment = re.sub(r"\n\s*\*\s*", " ", comment)
            comment = re.sub(r"\s+", " ", comment).strip()
            markdown += f"{comment}\n\n"

        # Extract fields
        fields = self._extract_fields(content, current_proto_file)
        if fields:
            markdown += "| Field | Type | Number | Description |\n"
            markdown += "|-------|------|--------|-------------|\n"
            for field in fields:
                # Format description to work with markdown tables - replace newlines with <br>
                description = field.get("description", "")
                if description and "\n" in description:
                    # Replace newlines with HTML break for table compatibility
                    formatted_desc = description.replace("\n\n", "<br><br>").replace(
                        "\n", "<br>"
                    )
                else:
                    formatted_desc = description

                # Get field type and try to create a link
                field_type = field["type"]
                if (
                    current_proto_file
                    and output_file
                    and self.import_resolver.initialized
                ):
                    # Extract the core type (remove modifiers like repeated, optional)
                    core_type = field_type
                    if "repeated" in field_type:
                        core_type = field_type.replace("repeated ", "")
                    elif "optional" in field_type:
                        core_type = field_type.replace("optional ", "")
                    elif "required" in field_type:
                        core_type = field_type.replace("required ", "")

                    # Check if it's a primitive type or a reference to another message/enum
                    primitive_types = [
                        "double",
                        "float",
                        "int32",
                        "int64",
                        "uint32",
                        "uint64",
                        "sint32",
                        "sint64",
                        "fixed32",
                        "fixed64",
                        "sfixed32",
                        "sfixed64",
                        "bool",
                        "string",
                        "bytes",
                    ]

                    if core_type not in primitive_types and "." in core_type:
                        # Try to create a link to the referenced type
                        link = self.import_resolver.get_markdown_link(
                            core_type, output_file, self.output_dir
                        )
                        field_type = field_type.replace(
                            core_type, link.replace("`", "")
                        )
                    else:
                        field_type = f"`{field_type}`"
                else:
                    field_type = f"`{field_type}`"

                markdown += f"| {field['name']} | {field_type} | {field['number']} | {formatted_desc} |\n"
            markdown += "\n"

        # Process nested messages
        nested_prefix = f"{name}."
        nested_messages = {
            k: v for k, v in all_messages.items() if k.startswith(nested_prefix)
        }
        for nested_name, nested_content in sorted(nested_messages.items()):
            if "." in nested_name:  # This is a nested message
                nested_simple_name = nested_name.split(".")[-1]
                markdown += f"#### {nested_simple_name} (nested in {name})\n\n"

                # Extract nested message comment if available
                comment_match = re.search(r"/\*\*(.*?)\*/", nested_content, re.DOTALL)
                if comment_match:
                    comment = comment_match.group(1).strip()
                    # Clean up multi-line comments by removing * prefixes and normalizing whitespace
                    comment = re.sub(r"\n\s*\*\s*", " ", comment)
                    comment = re.sub(r"\s+", " ", comment).strip()
                    markdown += f"{comment}\n\n"

                # Extract fields from nested message
                nested_fields = self._extract_fields(nested_content, current_proto_file)
                if nested_fields:
                    markdown += "| Field | Type | Number | Description |\n"
                    markdown += "|-------|------|--------|-------------|\n"
                    for field in nested_fields:
                        # Format description to work with markdown tables - replace newlines with <br>
                        description = field.get("description", "")
                        if description and "\n" in description:
                            # Replace newlines with HTML break for table compatibility
                            formatted_desc = description.replace(
                                "\n\n", "<br><br>"
                            ).replace("\n", "<br>")
                        else:
                            formatted_desc = description

                        # Get field type and try to create a link
                        field_type = field["type"]
                        if (
                            current_proto_file
                            and output_file
                            and self.import_resolver.initialized
                        ):
                            # Extract the core type (remove modifiers like repeated, optional)
                            core_type = field_type
                            if "repeated" in field_type:
                                core_type = field_type.replace("repeated ", "")
                            elif "optional" in field_type:
                                core_type = field_type.replace("optional ", "")
                            elif "required" in field_type:
                                core_type = field_type.replace("required ", "")

                            # Check if it's a primitive type or a reference to another message/enum
                            primitive_types = [
                                "double",
                                "float",
                                "int32",
                                "int64",
                                "uint32",
                                "uint64",
                                "sint32",
                                "sint64",
                                "fixed32",
                                "fixed64",
                                "sfixed32",
                                "sfixed64",
                                "bool",
                                "string",
                                "bytes",
                            ]

                            if core_type not in primitive_types and "." in core_type:
                                # Try to create a link to the referenced type
                                link = self.import_resolver.get_markdown_link(
                                    core_type, output_file, self.output_dir
                                )
                                field_type = field_type.replace(
                                    core_type, link.replace("`", "")
                                )
                            else:
                                field_type = f"`{field_type}`"
                        else:
                            field_type = f"`{field_type}`"

                        markdown += f"| {field['name']} | {field_type} | {field['number']} | {formatted_desc} |\n"
                    markdown += "\n"

        return markdown

    def _extract_messages(self, content):
        """
        Extract message definitions from proto content
        """
        messages = {}
        # Pattern to match message definitions at the top level
        message_pattern = (
            r"message\s+(\w+)\s*{([^{}]*(?:{[^{}]*(?:{[^{}]*}[^{}]*)*}[^{}]*)*)}"
        )

        # Find all message blocks
        for match in re.finditer(message_pattern, content, re.DOTALL):
            name = match.group(1)
            body = match.group(2)
            messages[name] = body

            # Find nested messages
            nested_pattern = (
                r"message\s+(\w+)\s*{([^{}]*(?:{[^{}]*(?:{[^{}]*}[^{}]*)*}[^{}]*)*)}"
            )
            for nested_match in re.finditer(nested_pattern, body, re.DOTALL):
                nested_name = nested_match.group(1)
                nested_body = nested_match.group(2)
                messages[f"{name}.{nested_name}"] = nested_body

        return messages

    def _extract_fields(self, message_content, current_proto_file=None):
        """
        Extract fields from a message block

        Args:
            message_content: The content of the message block
            current_proto_file: The proto file containing this message, for resolving imports
        """
        fields = []

        # First, remove any nested message or enum blocks to avoid field extraction within them
        clean_content = re.sub(r"(message|enum)\s+\w+\s*{[^}]*}", "", message_content)

        # Find block comments associated with fields
        block_comments = {}
        block_pattern = r"/\*\*(.*?)\*/\s*(?:optional|required|repeated)?\s*\w+(?:\.\w+)*\s+(\w+)\s*="
        for match in re.finditer(block_pattern, clean_content, re.DOTALL):
            comment = match.group(1).strip()
            # Clean up multi-line comments by removing * prefixes and normalizing whitespace
            # but preserve paragraph breaks
            paragraphs = re.split(r"\n\s*\*\s*\n", comment)
            formatted_paragraphs = []
            for paragraph in paragraphs:
                # Replace line breaks with spaces within paragraphs
                paragraph = re.sub(r"\n\s*\*\s*", " ", paragraph)
                paragraph = re.sub(r"\s+", " ", paragraph).strip()
                formatted_paragraphs.append(paragraph)

            # Join paragraphs back with line breaks
            comment = "\n\n".join(formatted_paragraphs)
            field_name = match.group(2)
            block_comments[field_name] = comment

        # Process field definitions line by line to capture comments
        lines = clean_content.splitlines()
        line_comments = {}
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            comment_lines = []

            # Collect consecutive comment lines
            while i < len(lines) and line.startswith("//"):
                comment_line = line[2:].strip()
                if comment_line:
                    comment_lines.append(comment_line)
                i += 1
                if i < len(lines):
                    line = lines[i].strip()
                else:
                    break

            # Check if next non-comment line is a field definition
            if i < len(lines) and "=" in line and ";" in line:
                field_match = re.search(r"(\w+)\s*=", line)
                if field_match and comment_lines:
                    field_name = field_match.group(1)
                    if (
                        field_name not in block_comments
                    ):  # Don't override block comments
                        # Check for paragraph breaks in comments
                        # A blank comment line indicates a paragraph break
                        paragraphs = []
                        current_paragraph = []

                        for comment_line in comment_lines:
                            if comment_line == "":
                                if current_paragraph:  # Only add non-empty paragraphs
                                    paragraphs.append(" ".join(current_paragraph))
                                    current_paragraph = []
                            else:
                                current_paragraph.append(comment_line)

                        # Add the last paragraph if there is one
                        if current_paragraph:
                            paragraphs.append(" ".join(current_paragraph))

                        # Join paragraphs with double newline to preserve formatting
                        line_comments[field_name] = "\n\n".join(paragraphs)

            if i < len(lines):
                i += 1

        # Pattern to match field definitions

        for match in re.finditer(FIELD_PATTERN, clean_content):
            modifier = match.group(1) or ""
            field_type = match.group(2)
            name = match.group(3)
            number = match.group(4)
            options = match.group(5) or ""
            inline_comment = match.group(6) or ""

            # Get the description from block comments, line comments, or inline comment
            comment = (
                block_comments.get(name, "")
                or line_comments.get(name, "")
                or inline_comment
            )

            if modifier:
                field_type = f"{modifier} {field_type}"

            fields.append(
                {
                    "name": name,
                    "type": field_type,
                    "number": number,
                    "options": options,
                    "description": comment,
                }
            )

        return fields

    def _extract_enums(self, content):
        """
        Extract enum definitions from proto content
        """
        enums = {}
        # Pattern to match enum definitions
        enum_pattern = r"enum\s+(\w+)\s*{([^}]*)}"

        # Find all enum blocks
        for match in re.finditer(enum_pattern, content, re.DOTALL):
            name = match.group(1)
            body = match.group(2)
            enums[name] = body

        return enums

    def _extract_enum_values(self, enum_content):
        """
        Extract values from an enum block
        """
        values = []
        # Pattern to match enum value definitions
        value_pattern = r"(\w+)\s*=\s*(\d+)(?:\s*\[(.*?)\])?;(?:\s*//\s*(.*))?"

        for match in re.finditer(value_pattern, enum_content):
            name = match.group(1)
            number = match.group(2)
            options = match.group(3) or ""
            comment = match.group(4) or ""

            values.append(
                {
                    "name": name,
                    "number": number,
                    "options": options,
                    "description": comment,
                }
            )

        return values

    def _extract_services(self, content):
        """
        Extract service definitions from proto content
        """
        services = {}
        # Pattern to match service definitions
        service_pattern = r"service\s+(\w+)\s*{([^}]*)}"

        # Find all service blocks
        for match in re.finditer(service_pattern, content, re.DOTALL):
            name = match.group(1)
            body = match.group(2)
            services[name] = body

        return services

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

        if hasattr(self, "proto_dirs"):
            for dir_path in self.proto_dirs:
                try:
                    abs_dir_path = os.path.abspath(dir_path)
                    abs_file_path = os.path.abspath(file_path)
                    # Check if the proto file is within this directory
                    common_path = os.path.commonpath([abs_dir_path, abs_file_path])
                    if common_path == abs_dir_path and len(common_path) > len(
                        longest_common_path
                    ):
                        best_proto_dir = abs_dir_path
                        longest_common_path = common_path
                except ValueError:
                    # commonpath raises ValueError if paths are on different drives
                    continue

        return best_proto_dir

    def _extract_imports(self, proto_content):
        """
        Extract import statements from proto content
        """
        imports = []
        # Pattern to match import statements
        import_pattern = r'import\s+"([^"]+)";'

        # Check for both single line imports and imports with comments
        lines = proto_content.splitlines()
        for i, line in enumerate(lines):
            match = re.search(import_pattern, line)
            if match:
                import_path = match.group(1)
                imports.append(import_path)

        return imports

    def _extract_methods(self, service_content):
        """
        Extract methods from a service block
        """
        methods = []

        # First find all comment blocks - more comprehensive to handle different styles
        comments = {}

        # Block comments (/** ... */)
        comment_pattern = r"/\*\*(.*?)\*/\s*rpc\s+(\w+)"
        for match in re.finditer(comment_pattern, service_content, re.DOTALL):
            comment = match.group(1).strip()
            # Clean up multi-line comments by removing * prefixes and normalizing whitespace
            comment = re.sub(r"\n\s*\*\s*", " ", comment)
            comment = re.sub(r"\s+", " ", comment).strip()
            method_name = match.group(2)
            comments[method_name] = comment

        # Line comments (// ...) before rpc definitions
        lines = service_content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            comment_lines = []

            # Collect consecutive comment lines
            while i < len(lines) and line.startswith("//"):
                comment_line = line[2:].strip()
                if comment_line:
                    comment_lines.append(comment_line)
                i += 1
                if i < len(lines):
                    line = lines[i].strip()
                else:
                    break

            # Check if next non-comment line is an rpc definition
            if i < len(lines) and "rpc " in line:
                rpc_match = re.search(r"rpc\s+(\w+)", line)
                if rpc_match and comment_lines:
                    method_name = rpc_match.group(1)
                    if method_name not in comments:  # Don't override block comments
                        comments[method_name] = " ".join(comment_lines)

            if i < len(lines):
                i += 1

        # Now extract all methods

        for match in re.finditer(METHOD_PATTERN, service_content):
            name = match.group(1)
            request = match.group(2)
            response = match.group(3)
            options = match.group(4) or ""
            inline_comment = match.group(5) or ""

            # Get the description from comments dict or inline comment
            description = comments.get(name, "") or inline_comment

            methods.append(
                {
                    "name": name,
                    "request": request,
                    "response": response,
                    "options": options,
                    "description": description,
                }
            )

        return methods
