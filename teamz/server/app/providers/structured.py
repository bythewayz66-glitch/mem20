"""Structured output enforcement (JSON Schema → Pydantic)."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel, ValidationError, create_model
from pydantic.json_schema import model_json_schema

from ..models import StructuredOutputConfig

T = TypeVar("T", bound=BaseModel)


class StructuredOutputEnforcer:
    """Enforces structured output from LLM responses using JSON Schema validation."""

    def __init__(self, config: Optional[StructuredOutputConfig] = None) -> None:
        self.config = config or StructuredOutputConfig()

    def create_schema_model(self, schema: Dict[str, Any], model_name: str = "StructuredOutput") -> Type[BaseModel]:
        """Create a Pydantic model from a JSON Schema."""
        return create_model(model_name, **self._schema_to_fields(schema))

    def _schema_to_fields(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert JSON Schema properties to Pydantic fields."""
        fields = {}
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))

        for prop_name, prop_schema in properties.items():
            field_type = self._json_type_to_python(prop_schema)
            is_required = prop_name in required

            if not is_required:
                field_type = Optional[field_type]
                default = prop_schema.get("default", None)
            else:
                default = ...

            fields[prop_name] = (field_type, default)

        return fields

    def _json_type_to_python(self, schema: Dict[str, Any]) -> Any:
        """Convert JSON Schema type to Python type."""
        json_type = schema.get("type", "string")

        if json_type == "string":
            if schema.get("format") == "date-time":
                from datetime import datetime
                return datetime
            if schema.get("format") == "date":
                from datetime import date
                return date
            if schema.get("format") == "email":
                from pydantic import EmailStr
                return EmailStr
            if schema.get("format") == "uuid":
                from uuid import UUID
                return UUID
            if "enum" in schema:
                return Union[tuple(schema["enum"])]
            return str
        elif json_type == "integer":
            return int
        elif json_type == "number":
            return float
        elif json_type == "boolean":
            return bool
        elif json_type == "array":
            items = schema.get("items", {})
            item_type = self._json_type_to_python(items)
            return List[item_type]
        elif json_type == "object":
            # Nested object - create a sub-model
            sub_model_name = f"Nested{hash(str(schema)) & 0xFFFFFFFF:08X}"
            return self.create_schema_model(schema, sub_model_name)
        else:
            return Any

    def validate(self, response_text: str, schema: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate response against JSON schema.
        Returns: (is_valid, parsed_data, error_message)
        """
        # Try to extract JSON from response
        json_data = self._extract_json(response_text)
        if json_data is None:
            return False, None, "No valid JSON found in response"

        # Create model and validate
        try:
            model_class = self.create_schema_model(schema)
            validated = model_class(**json_data)
            return True, validated.model_dump(), None
        except ValidationError as e:
            return False, None, str(e)
        except Exception as e:
            return False, None, f"Validation error: {e}"

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON object from text response."""
        # Try direct JSON parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON in code blocks
        json_block_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
        matches = re.findall(json_block_pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        # Try to find JSON object in text (greedy match)
        brace_count = 0
        start_idx = -1
        for i, char in enumerate(text):
            if char == "{":
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    try:
                        return json.loads(text[start_idx:i+1])
                    except json.JSONDecodeError:
                        start_idx = -1

        return None

    def enforce(self, response_text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enforce structured output, with fallback behavior based on config.
        Returns the validated data or raises if strict mode.
        """
        is_valid, data, error = self.validate(response_text, schema)

        if is_valid:
            return data

        if self.config.strict_mode:
            raise ValueError(f"Structured output validation failed: {error}")

        if self.config.fallback_to_text:
            return {"raw_text": response_text, "validation_error": error}

        raise ValueError(f"Structured output validation failed: {error}")

    def get_json_schema(self, model_class: Type[T]) -> Dict[str, Any]:
        """Get JSON Schema from a Pydantic model."""
        return model_json_schema(model_class, mode="serialization")


# Provider-specific schema modifiers
def adapt_schema_for_provider(schema: Dict[str, Any], provider: str) -> Dict[str, Any]:
    """Adapt schema for provider-specific requirements."""
    adapted = schema.copy()

    if provider == "ollama":
        # Ollama prefers simpler schemas
        adapted = _simplify_schema(adapted)
    elif provider == "anthropic":
        # Anthropic supports full JSON Schema
        pass
    elif provider == "openai":
        # OpenAI function calling format
        adapted = _to_openai_function_schema(adapted)
    elif provider == "vllm":
        # vLLM supports OpenAI-compatible function calling
        adapted = _to_openai_function_schema(adapted)

    return adapted


def _simplify_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Simplify schema for providers with limited schema support."""
    simplified = schema.copy()
    props = simplified.get("properties", {})

    for prop_name, prop_schema in props.items():
        # Remove complex validations
        prop_schema.pop("format", None)
        prop_schema.pop("pattern", None)
        prop_schema.pop("minimum", None)
        prop_schema.pop("maximum", None)
        prop_schema.pop("minLength", None)
        prop_schema.pop("maxLength", None)

        # Simplify enums to strings
        if "enum" in prop_schema:
            prop_schema["type"] = "string"

    return simplified


def _to_openai_function_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Convert to OpenAI function calling schema format."""
    return {
        "type": "function",
        "function": {
            "name": schema.get("title", "structured_output"),
            "description": schema.get("description", "Structured output"),
            "parameters": {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", []),
            },
        },
    }


# Pre-built schema models for common use cases
COMMON_SCHEMAS = {
    "code_generation": {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Generated code"},
            "language": {"type": "string", "description": "Programming language"},
            "explanation": {"type": "string", "description": "Explanation of the code"},
            "dependencies": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["code", "language"],
    },
    "task_plan": {
        "type": "object",
        "properties": {
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "step": {"type": "integer"},
                        "description": {"type": "string"},
                        "tool": {"type": "string"},
                        "args": {"type": "object"},
                    },
                    "required": ["step", "description", "tool"],
                },
            },
            "estimated_duration_minutes": {"type": "integer"},
        },
        "required": ["steps"],
    },
    "bug_analysis": {
        "type": "object",
        "properties": {
            "root_cause": {"type": "string"},
            "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
            "affected_files": {"type": "array", "items": {"type": "string"}},
            "fix_suggestion": {"type": "string"},
            "test_case": {"type": "string"},
        },
        "required": ["root_cause", "severity", "fix_suggestion"],
    },
}


def get_common_schema(name: str) -> Optional[Dict[str, Any]]:
    """Get a common schema by name."""
    return COMMON_SCHEMAS.get(name)