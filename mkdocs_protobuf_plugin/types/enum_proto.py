class EnumValue:

    def __init__(self, name: str, number: str, options: str, description: str):
        self.name = name
        self.number = number
        self.options = options
        self.description = description

    def get_name(self) -> str:
        return self.name

    def get_number(self) -> str:
        return self.number

    def get_options(self) -> str:
        return self.options

    def get_description(self) -> str:
        return self.description


class EnumProto:

    def __init__(self, name: str, body: str, values: list[EnumValue] = [],
                 comment: str = ""):
        self.name = name
        self.body = body
        self.values = values
        self.comment = comment

    def get_name(self) -> str:
        return self.name

    def get_body(self) -> str:
        return self.body

    def get_values(self) -> list[EnumValue]:
        return self.values

    def get_comment(self) -> str:
        return self.comment
