class ProtoTypes:

    types_list = [
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

    @staticmethod
    def isInTypesList(type: str) -> bool:
        return type in ProtoTypes.types_list
