from coreschema.compat import text_types
import coreschema
import re


jsonschema = coreschema.RefSpace({
    'Schema': coreschema.Object(
        properties={
            # Meta
            'id': coreschema.String(format='uri'),
            '$schema': coreschema.String(format='uri'),
            'title': coreschema.String(),
            'description': coreschema.String(),
            'default': coreschema.Anything(),
            'definitions': coreschema.Ref('SchemaMap'),
            # Type
            'type': coreschema.Ref('SimpleTypes') | coreschema.Array(items=coreschema.Ref('SimpleTypes'), min_items=1, unique_items=True),
            # Number validators
            'minimum': coreschema.Number(),
            'maximum': coreschema.Number(),
            'exclusiveMinimum': coreschema.Boolean(default=False),
            'exclusiveMaximum': coreschema.Boolean(default=False),
            'multipleOf': coreschema.Number(minimum=0, exclusive_minimum=True),
            # String validators
            'minLength': coreschema.Integer(minimum=0, default=0),
            'maxLength': coreschema.Integer(minimum=0),
            'pattern': coreschema.String(format='regex'),
            'format': coreschema.String(),
            # Array validators
            'items': coreschema.Ref('Schema') | coreschema.Ref('SchemaArray'), # TODO: default={}
            'additionalItems': coreschema.Boolean() | coreschema.Ref('Schema'),  # TODO: default={}
            'minItems': coreschema.Integer(minimum=0, default=0),
            'maxItems': coreschema.Integer(minimum=0),
            'uniqueItems': coreschema.Boolean(default=False),
            # Object validators
            'properties': coreschema.Ref('SchemaMap'),
            'patternProperties': coreschema.Ref('SchemaMap'),
            'additionalProperties': coreschema.Boolean() | coreschema.Ref('Schema'),
            'minProperties': coreschema.Integer(minimum=0, default=0),
            'maxProperties': coreschema.Integer(minimum=0),
            'required': coreschema.Ref('StringArray'),
            'dependancies': coreschema.Object(additional_properties=coreschema.Ref('Schema') | coreschema.Ref('StringArray')),
            # Enum validators
            'enum': coreschema.Array(min_items=1, unique_items=True),
            # Composites
            'allOf': coreschema.Ref('SchemaArray'),
            'anyOf': coreschema.Ref('SchemaArray'),
            'oneOf': coreschema.Ref('SchemaArray'),
            'not': coreschema.Ref('Schema')
        },
        # dependancies=..., TODO
        default={},
    ),
    'SchemaArray': coreschema.Array(
        items=coreschema.Ref('Schema'),
        min_items=1,
    ),
    'SchemaMap': coreschema.Object(
        additional_properties=coreschema.Ref('Schema'),
        default={},
    ),
    'SimpleTypes': coreschema.Enum(
        enum=['array', 'boolean', 'integer', 'null', 'number', 'object', 'string']
    ),
    'StringArray': coreschema.Array(
        items=coreschema.String(),
        min_items=1,
        unique_items=True,
    )
}, root='Schema')


KEYWORD_TO_TYPE = {
    'minimum': 'number',
    'maximum': 'number',
    'exclusiveMinimum': 'number',
    'exclusiveMaximum': 'number',
    'multipleOf': 'number',
    #
    'minLength': 'string',
    'maxLength': 'string',
    'pattern': 'string',
    'format': 'string',
    #
    'items': 'array',
    'maxItems': 'array',
    'minItems': 'array',
    'uniqueItems': 'array',
    'additionalItems': 'array',
    #
    'properties': 'object',
    'maxProperties': 'object',
    'minProperties': 'object',
    'additionalProperties': 'object',
    'patternProperties': 'object',
    'required': 'object',
}
TYPE_NAMES = [
    'array', 'boolean', 'integer', 'null', 'number', 'object', 'string'
]
CLS_MAP = {
    'array': coreschema.Array,
    'boolean': coreschema.Boolean,
    'integer': coreschema.Integer,
    'null': coreschema.Null,
    'number': coreschema.Number,
    'object': coreschema.Object,
    'string': coreschema.String,
}


def camelcase_to_snakecase(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def get_typed_schemas(data):
    """
    Return a list of schemas for any primitive type restrictions.
    """
    has_type = False
    type_kwargs = {type_name: {} for type_name in TYPE_NAMES}
    for keyword, value in data.items():
        if keyword not in KEYWORD_TO_TYPE:
            continue

        # Load any nested schemas
        if keyword == 'items' and isinstance(value, dict):
            value = load_jsonschema(value)
        elif keyword == 'items' and isinstance(value, list):
            value = [load_jsonschema(item) for item in value]
        elif keyword == 'additionalItems' and isinstance(value, dict):
            value = load_jsonschema(value)
        elif keyword == 'properties' and isinstance(value, dict):
            value = {key: load_jsonschema(item) for key, item in value.items()}
        elif keyword == 'additionalProperties' and isinstance(value, dict):
            value = load_jsonschema(value)
        elif keyword == 'patternProperties' and isinstance(value, dict):
            value = {key: load_jsonschema(item) for key, item in value.items()}

        type_name = KEYWORD_TO_TYPE[keyword]
        has_type = True
        argument_name = camelcase_to_snakecase(keyword)
        type_kwargs[type_name][argument_name] = value

    type_kwargs['integer'] = type_kwargs['number']

    if 'type' in data:
        has_type = True
        types = data.get('type')
        types = types if isinstance(types, list) else [types]
        for type_name in list(type_kwargs.keys()):
            if type_name not in types:
                type_kwargs.pop(type_name)

    schemas = []
    if has_type:
        for type_name, kwargs in type_kwargs.items():
            cls = CLS_MAP[type_name]
            schemas.append(cls(**kwargs))

    return schemas


def get_composite_schemas(data):
    schemas = []
    if 'anyOf' in data:
        value = data['anyOf']
        schema = coreschema.Union([
            load_jsonschema(item) for item in value
        ])
        schemas.append(schema)
    if 'allOf' in data:
        value = data['allOf']
        schema = coreschema.Intersection([
            load_jsonschema(item) for item in value
        ])
        schemas.append(schema)
    if 'oneOf' in data:
        value = data['oneOf']
        schema = coreschema.ExclusiveUnion([
            load_jsonschema(item) for item in value
        ])
        schemas.append(schema)
    if 'not' in data:
        value = data['not']
        schema = coreschema.Not(load_jsonschema(value))
        schemas.append(schema)
    return schemas



def load_jsonschema(data):
    schemas = get_typed_schemas(data)
    if len(schemas) > 1:
        schemas = [coreschema.Union(schemas)]
    schemas += get_composite_schemas(data)

    if not schemas:
        schema = coreschema.Anything()
    elif len(schemas) == 1:
        schema = schemas[0]
    else:
        schema = coreschema.Intersection(schemas)

    if 'enum' in data:
        # Restrict enum values by any existing type constraints,
        # and then use an Enum type.
        enum_values = [
            value for value in data['enum']
            if schema.validate(value) == []
        ]
        return coreschema.Enum(enum_values)

    return schema
