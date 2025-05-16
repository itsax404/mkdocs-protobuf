class ServiceMethod:

    def __init__(self, name: str, request: str, response: str, options: str, description: str):
        self.name = name
        self.request = request
        self.response = response
        self.options = options
        self.description = description

    def get_name(self) -> str:
        return self.name

    def get_request(self) -> str:
        return self.request

    def get_response(self) -> str:
        return self.response

    def get_options(self) -> str:
        return self.options

    def get_description(self) -> str:
        return self.description


class Service:

    def __init__(self, name: str, body: str, methods: list[ServiceMethod],
                 comment: str):
        self.name = name
        self.body = body
        self.methods = methods
        self.comment = comment

    def get_name(self) -> str:
        return self.name

    def get_body(self) -> str:
        return self.body

    def get_methods(self) -> list[ServiceMethod]:
        return self.methods

    def get_comment(self) -> str:
        return self.comment
