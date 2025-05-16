class MessageField:

    def __init__(self, name: str, type: str, number: str, options: str, description: str):
        self.name = name
        self.type = type
        self.number = number
        self.options = options
        self.description = description

    def get_name(self) -> str:
        return self.name

    def get_type(self) -> str:
        return self.type

    def get_number(self) -> str:
        return self.number

    def get_options(self) -> str:
        return self.options

    def get_description(self) -> str:
        return self.description


class Message:

    def __init__(self, name: str, body: str, nested_message: list["Message"] = list(),
                 fields: list[MessageField] = list(), comment: str = "") -> None:
        self.name = name
        self.body = body
        self.nested_message: list[Message] = nested_message
        self.fields = fields
        self.comment = comment

    def get_name(self) -> str:
        return self.name

    def get_body(self) -> str:
        return self.body

    def get_nested_messages(self) -> list["Message"]:
        return self.nested_message

    def get_fields(self) -> list[MessageField]:
        return self.fields

    def get_comment(self) -> str:
        return self.comment
