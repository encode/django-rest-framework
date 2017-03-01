let codec = new window.coreapi.codecs.CoreJSONCodec()
let coreJSON = window.atob('{{ schema }}')
window.schema = codec.decode(coreJSON)
