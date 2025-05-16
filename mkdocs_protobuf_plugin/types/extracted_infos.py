from .message import Message
from .enum_proto import EnumProto
from .service import Service


class ExtractedInfos:

    def __init__(self, package_name: str, imports: list[str],
                 messages: list[Message], enums: list[EnumProto],
                 services: list[Service]):
        self.package_name = package_name
        self.imports = imports
        self.messages = messages
        self.enums = enums
        self.services = services

    def get_package_name(self) -> str:
        return self.package_name

    def get_imports(self) -> list[str]:
        return self.imports

    def get_messages(self) -> list[Message]:
        return self.messages

    def get_enums(self) -> list[EnumProto]:
        return self.enums

    def get_services(self) -> list[Service]:
        return self.services
