from typing import Any


class BinarySerializer:
    def __init__(self, schema: dict):
        self.array = bytearray()
        self.schema = schema

    def serialize_num(self, value: int, n_bytes: int) -> None:
        orig_value = value
        assert value >= 0, "Can't serialize negative numbers %d" % value    # TODO: Need to replace to Exception
        for _i in range(n_bytes):
            self.array.append(value & 255)
            value //= 256
        assert value == 0, 'Value %d has more than %d bytes' % (orig_value, n_bytes)    # TODO: Need to replace to Exception

    def serialize_field(self, value: Any, field_type: str | list | dict | type) -> None:
        if isinstance(field_type, str):
            if field_type[0] == 'u':
                self.serialize_num(value, int(field_type[1:]) // 8)
                return

            if field_type == 'string':
                b = value.encode('utf8')
                self.serialize_num(len(b), 4)
                self.array += b
                return

            raise AssertionError(field_type)        # TODO: Need to replace to Exception

        elif isinstance(field_type, list):  # noqa: RET506
            assert len(field_type) == 1    # TODO: Need to replace to Exception
            if type(field_type[0]) == int:
                assert type(value) == bytes, f'type({value}) = {type(value)} != bytes'    # TODO: Need to replace to Exception
                assert len(value) == field_type[0], f'len({value!r}) = {len(value)} != {field_type[0]}' # TODO: Need to replace to Exception
                self.array += bytearray(value)
                return

            self.serialize_num(len(value), 4)
            for el in value:
                self.serialize_field(el, field_type[0])

        elif isinstance(field_type, dict):
            assert field_type['kind'] == 'option'    # TODO: Need to replace to Exception
            if value is None:
                self.serialize_num(0, 1)
            else:
                self.serialize_num(1, 1)
                self.serialize_field(value, field_type['type'])

        elif isinstance(field_type, type):
            assert type(value) == field_type, f'{field_type} != type({value})'    # TODO: Need to replace to Exception
            self.serialize_struct(value)

        else:
            raise TypeError(type(field_type))    # TODO: Need to replace to Exception

    def serialize_struct(self, obj: Any) -> None:
        struct_schema = self.schema[type(obj)]
        if struct_schema['kind'] == 'struct':
            for field_name, field_type in struct_schema['fields']:
                self.serialize_field(getattr(obj, field_name), field_type)
        elif struct_schema['kind'] == 'enum':
            idx = struct_schema['values'].index(type(obj.enum))
            self.serialize_num(idx, 1)
            self.serialize_field(obj.enum, type(obj.enum))
        else:
            raise AssertionError(struct_schema)     # TODO: Need to replace to Exception

    def serialize(self, obj: Any) -> bytes:
        self.serialize_struct(obj)
        return bytes(self.array)
