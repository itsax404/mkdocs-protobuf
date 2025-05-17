from re import Match
import re
import logging
from mkdocs_protobuf_plugin.types.message import Message, MessageField
from mkdocs_protobuf_plugin.types.enum_proto import EnumProto, EnumValue
from mkdocs_protobuf_plugin.types.service import ServiceMethod, Service
from mkdocs_protobuf_plugin.types.extracted_infos import ExtractedInfos

PACKAGE_REGEX = r"package\s+([^;]+);"
COMMENT_REGEX = r"/\*\*(.*?)\*/"
MESSAGE_REGEX = r"message\s+(\w+)\s*{([^{}]*(?:{[^{}]*(?:{[^{}]*}[^{}]*)*}[^{}]*)*)}"
CLEAN_NESTED_REGEX = r"(message|enum)\s+\w+\s*{[^}]*}"
FIELD_PATTERN = r"(optional|required|repeated)?\s*(\w+(?:\.\w+)*)\s+(\w+)\s*=\s*(\d+)(?:\s*\[(.*?)\])?;(?:\s*//\s*(.*))?"
BLOCK_COMMENTS_PATTERN = r"/\*\*(.*?)\*/\s*(?:optional|required|repeated)?\s*\w+(?:\.\w+)*\s+(\w+)\s*="
METHOD_PATTERN = r"rpc\s+(\w+)\s*\(\s*(\w+(?:\.\w+)*)\s*\)\s*returns\s*\(\s*(\w+(?:\.\w+)*)\s*\)(?:\s*{(.*?)})?;(?:\s*//\s*(.*))?"  # noqa: E501



class ProtoExtractor:

    

    def __init__(self, file_content: str):
        self.file_content = file_content
        self.log = logging.getLogger(f"mkdocs.plugins.{__name__}")

    def extract_infos(self):
        return ExtractedInfos(
            self.__extract_package__name__(),
            self.__extract_imports__(),
            self.__extract_messages__(),
            self.__extract_enums__(),
            self.__extract_services__()
        )

    def __extract_package__name__(self) -> str:
        package_match = re.search(PACKAGE_REGEX, self.file_content)
        result = package_match.group(1) if package_match else ""
        self.log.debug(f"Extracted package name : {result}")
        return result

    def __extract_messages__(self) -> list[Message]:
        """
        Extract message definitions from proto content
        """
        messages: list[Message] = []

        # Find all message blocks
        for match in re.finditer(MESSAGE_REGEX, self.file_content, re.DOTALL):
            name = match.group(1)
            body = match.group(2)
            comment = self.__extract_message_comment__(body)
            fields = self.__extract_fields__(body)
            nested_messages: list[Message] = list()

            for nested_match in re.finditer(MESSAGE_REGEX, body, re.DOTALL):
                nested_name = nested_match.group(1)
                nested_body = nested_match.group(2)
                nested_fields = self.__extract_fields__(nested_body)
                nested_messages.append(Message(nested_name, nested_body, list(), nested_fields))
            messages.append(Message(name, body, nested_messages, fields, comment))
        self.log.debug(f"Extract messages : {messages}")
        return messages

    def __extract_message_comment__(self, message_content: str) -> str:
        comment_match = re.search(r"/\*\*(.*?)\*/", message_content, re.DOTALL)
        final_comment = ""
        if comment_match:
            comment = comment_match.group(1).strip()
            # Clean up multi-line comments by removing * prefixes and normalizing whitespace
            comment = re.sub(r"\n\s*\*\s*", " ", comment)
            final_comment = re.sub(r"\s+", " ", comment).strip()
        self.log.debug(f"Extracted message comment {final_comment} from {message_content}")
        return final_comment

    def __extract_fields__(self, message_content: str) -> list[MessageField]:
        """
        Extract fields from a message block

        Args:
            message_content: The content of the message block
            current_proto_file: The proto file containing this message, for resolving imports
        """
        # First, remove any nested message or enum blocks to avoid field extraction within them
        clean_content = re.sub(CLEAN_NESTED_REGEX, "", message_content)

        formatted_paragraphs: list[str] = []

        # Find block comments associated with fields
        block_comments: dict[str, str] = {}
        for match in re.finditer(BLOCK_COMMENTS_PATTERN, clean_content, re.DOTALL):
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

        line_comments = self.__extract_line_comments__(clean_content, block_comments)

        # Pattern to match field definitions

        fields: list[MessageField] = list()
        for match in re.finditer(FIELD_PATTERN, clean_content):
            fields.append(self.__extract_field__(match, block_comments, line_comments))
        self.log.debug(f"Extracted fields {fields} from {message_content}")
        return fields

    def __extract_field__(self, match: Match[str], block_comments: dict[str, str],
                          line_comments: dict[str, str]) -> MessageField:
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
        
        field = MessageField(name, field_type, number, options, comment)
        self.log.debug(f"Extract field : {field} from match : {match} and block comments {block_comments}")
        return field

    def __extract_line_comments__(self, clean_content: str, block_comments: dict[str, str]) -> dict[str, str]:
        # Process field definitions line by line to capture comments
        lines = clean_content.splitlines()
        line_comments: dict[str, str] = {}
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            comment_lines: list[str] = []

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
            field_name = ""
            value = ""

            # Check if next non-comment line is a field definition
            if (i < len(lines) and "=" in line and ";" in line):
                field_name, value = self.__logic_line_comments_fields__(line, block_comments, comment_lines)
            elif (i < len(lines) and "rpc " in line):
                field_name, value = self.__logic_line_comments_methods__(line, block_comments, comment_lines)
            if (field_name != "" and value != ""):
                line_comments[field_name] = value

            if (i < len(lines)):
                i += 1
        self.log.debug(f"Extracted line comments {line_comments} from clean content : {clean_content} and block comments {block_comments}")
        return line_comments

    def __logic_line_comments_fields__(self, line: str, block_comments: dict[str, str],
                                       comment_lines: list[str]) -> tuple[str, str]:
        field_match = re.search(r"(\w+)\s*=", line)
        result = ("", "")
        if field_match and comment_lines:
            field_name = field_match.group(1)
            if (
                field_name not in block_comments
            ):  # Don't override block comments
                # Check for paragraph breaks in comments
                # A blank comment line indicates a paragraph break
                paragraphs: list[str] = []
                current_paragraph: list[str] = []

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
                result = (field_name, "\n\n".join(paragraphs))
        self.log.info(f"Extract line comment {result} from a field : {line} with block comments {block_comments}")
        return result

    def __logic_line_comments_methods__(self, line: str, block_comments: dict[str, str],
                                        comment_lines: list[str]) -> tuple[str, str]:
        rpc_match = re.search(r"rpc\s+(\w+)", line)
        result = ("", "")
        if rpc_match and block_comments:
            method_name = rpc_match.group(1)
            if method_name not in block_comments:  # Don't override block comments
                result = (method_name, " ".join(comment_lines))

        self.log.info(f"Extract line comment {result} from a method : {line} with comment_lines {comment_lines} and block comments {block_comments}")
        return result

    def __extract_enums__(self) -> list[EnumProto]:
        """
        Extract enum definitions from proto content
        """
        enums: list[EnumProto] = list()
        # Pattern to match enum definitions
        enum_pattern = r"enum\s+(\w+)\s*{([^}]*)}"

        # Find all enum blocks
        for match in re.finditer(enum_pattern, self.file_content, re.DOTALL):
            name = match.group(1)
            body = match.group(2)
            comment = self.__extract_main_comment__(body)
            enum_values = self.__extract_enum_values__(body)
            enums.append(EnumProto(name, body, enum_values, comment))
        self.log.debug(f"Extracted enums : {enums}")
        return enums

    def __extract_main_comment__(self, content: str) -> str:
        comment_match = re.search(COMMENT_REGEX, content, re.DOTALL)
        result = ""
        if comment_match:
            result = comment_match.group(1).strip()
        self.log.info(f"Extract main comment of {content} : {result}")
        return result

    def __extract_enum_values__(self, enum_content: str) -> list[EnumValue]:
        """
        Extract values from an enum block
        """
        values: list[EnumValue] = []
        # Pattern to match enum value definitions
        value_pattern = r"(\w+)\s*=\s*(\d+)(?:\s*\[(.*?)\])?;(?:\s*//\s*(.*))?"

        for match in re.finditer(value_pattern, enum_content):
            name = match.group(1)
            number = match.group(2)
            options = match.group(3) or ""
            comment = match.group(4) or ""

            values.append(EnumValue(name, number, options, comment))
        self.log.debug(f"Extracted enum values {values} from {enum_content}")
        return values

    def __extract_imports__(self) -> list[str]:
        """
        Extract import statements from proto content
        """
        imports: list[str] = []
        # Pattern to match import statements
        import_pattern = r'import\s+"([^"]+)";'

        # Check for both single line imports and imports with comments
        lines = self.file_content.splitlines()
        for line in lines:
            match = re.search(import_pattern, line)
            if match:
                import_path = match.group(1)
                imports.append(import_path)

        self.log.debug(f"Extracted import {imports}")
        return imports

    def __extract_methods__(self, service_content: str) -> list[ServiceMethod]:
        """
        Extract methods from a service block
        """
        methods: list[ServiceMethod] = []

        # First find all comment blocks - more comprehensive to handle different styles
        comments: dict[str, str] = {}

        # Block comments (/** ... */)
        comment_pattern = r"/\*\*(.*?)\*/\s*rpc\s+(\w+)"
        for match in re.finditer(comment_pattern, service_content, re.DOTALL):
            comment = match.group(1).strip()
            # Clean up multi-line comments by removing * prefixes and normalizing whitespace
            comment = re.sub(r"\n\s*\*\s*", " ", comment)
            comment = re.sub(r"\s+", " ", comment).strip()
            method_name = match.group(2)
            comments[method_name] = comment

        inline_comments = self.__extract_line_comments__(service_content, comments)

        for key, value in inline_comments.items():
            comments[key] = value

        # Now extract all methods

        for match in re.finditer(METHOD_PATTERN, service_content):
            name = match.group(1)
            request = match.group(2)
            response = match.group(3)
            options = match.group(4) or ""
            inline_comment = match.group(5) or ""

            # Get the description from comments dict or inline comment
            description = comments.get(name, "") or inline_comment

            methods.append(ServiceMethod(name, request, response, options, description))
        self.log.debug(f"Extracted methods {methods} from {service_content}")
        return methods

    def __extract_services__(self) -> list[Service]:
        """
        Extract service definitions from proto content
        """
        services: list[Service] = list()
        # Pattern to match service definitions
        service_pattern = r"service\s+(\w+)\s*{([^}]*)}"

        # Find all service blocks
        for match in re.finditer(service_pattern, self.file_content, re.DOTALL):
            name = match.group(1)
            body = match.group(2)
            comment = self.__extract_main_comment__(body)
            methods = self.__extract_methods__(body)
            services.append(Service(name, body, methods, comment))

        self.log.debug(f"Extracted services {services}")
        return services
