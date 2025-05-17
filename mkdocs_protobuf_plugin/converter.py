import os
import logging
from pathlib import Path
from mkdocs_protobuf_plugin.import_resolver import ProtoImportResolver
from mkdocs_protobuf_plugin.extractor import ProtoExtractor
from mkdocs_protobuf_plugin.types.proto_types import ProtoTypes
from mkdocs_protobuf_plugin.types.message import Message, MessageField
from mkdocs_protobuf_plugin.types.service import ServiceMethod, Service
from mkdocs_protobuf_plugin.types.enum_proto import EnumProto, EnumValue




class ProtoToMarkdownConverter:
    def __init__(self, proto_dirs: list[str] = []):
        # Initialize any parser configuration here
        self.import_resolver = ProtoImportResolver()
        self.output_dir = ""
        self.proto_dirs = proto_dirs
        self.log = logging.getLogger("mkdocs.plugins.protobuf")

    def convert_proto_files(self, proto_files: list[str], output_dir: str) -> list[str]:
        """
        Convert a list of proto files to markdown and save them in the output directory
        Returns a list of generated markdown files
        """
        self.log.debug(f"Start converting {proto_files} into {output_dir} directory")
        self.output_dir = output_dir

        # First, initialize the import resolver with all proto files
        if self.proto_dirs:
            self.import_resolver.proto_dirs = self.proto_dirs
        self.import_resolver.initialize(proto_files)

        # Then convert each file to markdown
        generated_files: list[str] = []
        for proto_file in proto_files:
            try:
                self.log.debug(f"Try to convert {proto_file} file")
                output_file = self.convert_proto_file(proto_file, output_dir)
                if output_file:
                    self.log.debug(f"Converted {proto_file} correctly")
                    generated_files.append(output_file)
            except Exception as e:
                self.log.error(f"Error converting proto file {proto_file}: {str(e)}")
                # Add more detailed error info for debugging
                import traceback

                self.log.debug(f"Traceback: {traceback.format_exc()}")
        return generated_files

    def convert_proto_file(self, proto_file: str, output_dir: str) -> str:
        """
        Convert a single proto file to markdown
        Returns the output file path
        """
        self.log.info(f"Converting proto file: {proto_file}")

        try:
            # Read the proto file
            with open(proto_file, "r") as f:
                proto_content = f.read()

            # Parse and convert to markdown
            proto_path = Path(proto_file)
            self.log.debug("Convert proto content into markdown")
            markdown_content = self.__proto_to_markdown__(
                proto_content, proto_path.name, proto_file, output_dir
            )

            self.log.debug("Get abosute path of the file")
            # Get absolute paths to work with
            abs_file_path = os.path.abspath(proto_file)

            # Find the most specific proto directory that contains this file
            best_proto_dir = ""
            longest_common_path = ""

            if self.proto_dirs:
                for dir_path in self.proto_dirs:
                    try:
                        self.log.debug("Try to get proto dir")
                        abs_dir_path = os.path.abspath(dir_path)
                        # Check if the proto file is within this directory
                        common_path = os.path.commonpath([abs_dir_path, abs_file_path])
                        if common_path == abs_dir_path and len(common_path) > len(
                            longest_common_path
                        ):
                            best_proto_dir = abs_dir_path
                            longest_common_path = common_path
                    except ValueError:
                        self.log.warning("Paths are differents")
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

            self.log.info(f"Generated markdown file: {output_file}")

            return output_file

        except Exception as e:
            self.log.error(f"Error converting {proto_file}: {str(e)}")
            return ""

    def __proto_to_markdown__(
        self, proto_content: str, filename: str, current_proto_file: str = "", output_dir: str = ""
    ):
        """
        Convert proto content to markdown format

        Args:
            proto_content: The content of the proto file
            filename: The filename (for display purposes)
            current_proto_file: The absolute path to the current proto file (for resolving imports)
            output_dir: The output directory for markdown files
        """
        self.log.debug(f"Start to converting proto content into markdown for {filename}")
        current_output_file: str = ""
        if current_proto_file and output_dir:
            # Determine the output file path for the current proto file
            best_proto_dir = self.__find_best_proto_dir__(current_proto_file)
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

        markdown = [f"# Protocol Documentation: {filename}\n\n"]

        extractor = ProtoExtractor(proto_content)
        infos = extractor.extract_infos()

        if (infos.get_package_name() != ""):
            markdown.append(f"## Package: `{infos.get_package_name()}`")

        if (len(infos.get_imports()) != 0):
            markdown.append("## Imports \n\n")
            markdown.extend([f"- `{imp}`\n" for imp in infos.get_imports()])
            markdown.append("\n")

        messages = infos.get_messages()
        if (len(messages) != 0):
            markdown.append("## Messages\n\n")
            for message in messages:
                markdown.append(self.__format_message_markdown__(message, current_output_file))

        enums = infos.get_enums()
        if (len(enums) != 0):
            markdown.append("## Enums\n\n")
            markdown.append(self.__create_enum_tables__(enums))

        # Extract services
        services = infos.get_services()
        if services:
            markdown.append(self.__get_services_string__(services, current_output_file))

        return "".join(markdown)

    def __get_services_string__(self, services: list[Service], current_output_file: str) -> str:
        markdown = ["## Services\n\n"]
        for service in sorted(services, key=lambda s: s.get_name()):
            markdown.append(f"### {service.get_name()}\n\n")

            # Extract service comment if available
            comment = service.get_comment()
            if comment:
                markdown.append(f"{comment}\n\n")

            methods = service.get_methods()
            if methods:
                markdown.append(self.__create_method_table__(methods, current_output_file))
        return "".join(markdown)

    def __create_method_table__(self, methods: list[ServiceMethod], current_output_file: str) -> str:
        markdown = ["| Method | Request | Response | Description |\n"]
        markdown.append("|--------|---------|----------|-------------|\n")
        for method in methods:
            request = method.get_request()
            response = method.get_response()

            # Use import resolver to create links if possible
            if (current_output_file and self.import_resolver.initialized):
                request = self.import_resolver.get_markdown_link(
                    request, current_output_file, self.output_dir
                )
                response = self.import_resolver.get_markdown_link(
                    response, current_output_file, self.output_dir
                )
            else:
                request = f"`{request}`"
                response = f"`{response}`"

            markdown.append(f"| {method.get_name()} | {request} | {response} | {method.get_description()} |\n")
        markdown.append("\n")
        return "".join(markdown)

    def __create_enum_tables__(self, enums: list[EnumProto]):
        markdown: list[str] = []
        for enum in sorted(enums, key=lambda en: en.get_name()):
            markdown.append(f"### {enum.get_name()}\n\n")

            comment = enum.get_comment()
            if (comment != ""):
                markdown.append(f"{comment}\n\n")

            values = enum.get_values()
            if (len(values) != 0):
                markdown.append(self.__create_enum_values_table__(values))
        return "".join(markdown)

    def __create_enum_values_table__(self, values: list[EnumValue]) -> str:
        markdown = ["| Name | Number | Description |\n"]
        markdown.append("|------|--------|-------------|\n")
        for value in values:
            markdown.append(f"| {value.get_name()} | {value.get_number()} | {value.get_description()} |\n")
        markdown.append("\n")
        return "".join(markdown)

    def __format_message_markdown__(
        self, message: Message, output_file: str = "", nested: bool = False
    ) -> str:
        """
        Format a message and its nested messages into markdown

        Args:
            name: The message name
            content: The message content
            all_messages: Dictionary of all messages in the proto file
            current_proto_file: The proto file containing this message, for resolving imports
            output_file: The output markdown file path, for creating proper links
        """
        if (not nested):
            markdown = [f"### {message.get_name()}\n\n"]
        else:
            markdown = []
        comment = message.get_comment()
        # Extract message comment if available
        if (comment != ""):
            markdown.append(f"{comment}\n\n")

        fields = message.get_fields()
        # Extract fields
        if (len(fields) != 0):
            markdown.append(self.__create_field_table__(fields, output_file))

        for nested_message in sorted(message.get_nested_messages(), key=lambda nest: nest.get_name()):
            markdown.append(f"#### {nested_message.get_name()} (nested in {message.get_name()})\n\n")
            markdown.append(self.__format_message_markdown__(nested_message, output_file, True))

        return "".join(markdown)

    def __create_field_table__(self, fields: list[MessageField], output_file: str) -> str:
        string = ["| Field | Type | Number | Description |\n"]
        string.append("|-------|------|--------|-------------|\n")
        for field in fields:
            # Format description to work with markdown tables - replace newlines with <br>
            description = field.get_description()
            if (description != "" and "\n" in description):
                # Replace newlines with HTML break for table compatibility
                formatted_desc = description.replace("\n\n", "<br><br>").replace(
                    "\n", "<br>"
                )
            else:
                formatted_desc = description

            # Get field type and try to create a link
            field_type = field.get_type()
            if (output_file and self.import_resolver.initialized):
                # Extract the core type (remove modifiers like repeated, optional)
                core_type = field_type
                if "repeated" in field_type:
                    core_type = field_type.replace("repeated ", "")
                elif "optional" in field_type:
                    core_type = field_type.replace("optional ", "")
                elif "required" in field_type:
                    core_type = field_type.replace("required ", "")

                if ((not ProtoTypes.isInTypesList(core_type)) and "." in core_type):
                    # Try to create a link to the referenced type
                    link = self.import_resolver.get_markdown_link(
                        core_type, output_file, self.output_dir
                    )
                    field_type = field_type.replace(core_type, link.replace("`", ""))
                else:
                    field_type = f"`{field_type}`"
            else:
                field_type = f"`{field_type}`"

            string.append(f"| {field.get_name()} | {field_type} | {field.get_number()} | {formatted_desc} |\n")
        string.append("\n")
        return "".join(string)

    def __find_best_proto_dir__(self, file_path: str) -> str:
        """
        Find the most specific proto directory that contains this file

        Args:
            file_path: Absolute path to a proto file

        Returns:
            The absolute path to the best matching proto directory or None
        """
        best_proto_dir = ""
        longest_common_path = ""

        if self.proto_dirs:
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
