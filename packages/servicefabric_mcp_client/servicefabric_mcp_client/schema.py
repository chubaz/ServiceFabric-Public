import hashlib,json
def normalized_schema(schema):return json.dumps(schema,sort_keys=True,separators=(",",":"),ensure_ascii=True)
def schema_digest(schema):return "sha256:"+hashlib.sha256(normalized_schema(schema).encode()).hexdigest()
