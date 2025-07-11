jsonschema = coreschema.RefSpace({
    'Document': coreschema.Object(
        properties={
            '_type': coreschema.Enum(['document']),
            '_meta': coreschema.Object(
                properties={
                    'url': coreschema.String(),
                    'title': coreschema.String(),
                    'description': coreschema.String(),
                }
            )
        }
    ),
    'Link': coreschema.Object(
        properties={
            '_type': coreschema.Enum(['link'])
        }
    )
})
