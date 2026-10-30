"""Universal integration compiler: compile integrations between systems."""
import json


def compile_integration(source, target, mapping):
    return {"source": source, "target": target, "mapping": mapping, "compiled": True}


def validate_mapping(mapping, source_schema, target_schema):
    missing_src = [k for k in mapping if k not in source_schema]
    missing_tgt = [v for v in mapping.values() if v not in target_schema]
    return {"valid": not missing_src and not missing_tgt, "missing_src": missing_src, "missing_tgt": missing_tgt}


def transform(data, mapping):
    out = {}
    for sk, tk in mapping.items():
        if sk in data:
            out[tk] = data[sk]
    return out


def integration_health(integrations):
    return {"integrations": len(integrations), "compiled": sum(1 for i in integrations if i.get("compiled"))}
