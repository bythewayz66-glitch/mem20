"""Model-specific prompt templates (system prompts per provider)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..models import ModelPromptTemplate


# Built-in prompt templates for popular models
BUILTIN_TEMPLATES: Dict[str, ModelPromptTemplate] = {
    # Ollama templates
    "ollama:llama3": ModelPromptTemplate(
        provider_id="ollama",
        model="llama3",
        system_template="<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>",
        user_template="<|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|>",
        assistant_template="<|start_header_id|>assistant<|end_header_id|>\n\n{assistant_prompt}<|eot_id|>",
        function_calling_template=(
            "<|start_header_id|>system<|end_header_id|>\n\n"
            "You are a helpful assistant with access to functions. "
            "Use them when appropriate.<|eot_id|>"
        ),
        variables={
            "system_prompt": "You are a helpful AI assistant.",
        },
    ),
    "ollama:llama3.1": ModelPromptTemplate(
        provider_id="ollama",
        model="llama3.1",
        system_template="<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>",
        user_template="<|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|>",
        assistant_template="<|start_header_id|>assistant<|end_header_id|>\n\n{assistant_prompt}<|eot_id|>",
        function_calling_template=(
            "<|start_header_id|>system<|end_header_id|>\n\n"
            "You are a helpful assistant with access to functions. "
            "Use them when appropriate.<|eot_id|>"
        ),
        variables={
            "system_prompt": "You are a helpful AI assistant.",
        },
    ),
    "ollama:codellama": ModelPromptTemplate(
        provider_id="ollama",
        model="codellama",
        system_template="<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>",
        user_template="<|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|>",
        assistant_template="<|start_header_id|>assistant<|end_header_id|>\n\n{assistant_prompt}<|eot_id|>",
        variables={
            "system_prompt": "You are an expert programmer. Write clean, efficient code.",
        },
    ),
    "ollama:mistral": ModelPromptTemplate(
        provider_id="ollama",
        model="mistral",
        system_template="<s>[INST] {system_prompt} [/INST]",
        user_template="[INST] {user_prompt} [/INST]",
        assistant_template="{assistant_prompt}</s>",
        variables={
            "system_prompt": "You are a helpful AI assistant.",
        },
    ),
    "ollama:mixtral": ModelPromptTemplate(
        provider_id="ollama",
        model="mixtral",
        system_template="<s>[INST] {system_prompt} [/INST]",
        user_template="[INST] {user_prompt} [/INST]",
        assistant_template="{assistant_prompt}</s>",
        variables={
            "system_prompt": "You are a helpful AI assistant.",
        },
    ),
    "ollama:gemma": ModelPromptTemplate(
        provider_id="ollama",
        model="gemma",
        system_template="<start_of_turn>system\n{system_prompt}<end_of_turn>\n",
        user_template="<start_of_turn>user\n{user_prompt}<end_of_turn>\n",
        assistant_template="<start_of_turn>model\n{assistant_prompt}<end_of_turn>\n",
        variables={
            "system_prompt": "You are a helpful AI assistant.",
        },
    ),
    "ollama:qwen": ModelPromptTemplate(
        provider_id="ollama",
        model="qwen",
        system_template="<|im_start|>system\n{system_prompt}<|im_end|>\n",
        user_template="<|im_start|>user\n{user_prompt}<|im_end|>\n",
        assistant_template="<|im_start|>assistant\n{assistant_prompt}<|im_end|>\n",
        variables={
            "system_prompt": "You are a helpful AI assistant.",
        },
    ),
    "ollama:phi3": ModelPromptTemplate(
        provider_id="ollama",
        model="phi3",
        system_template="<|system|>\n{system_prompt}<|end|>\n",
        user_template="<|user|>\n{user_prompt}<|end|>\n",
        assistant_template="<|assistant|>\n{assistant_prompt}<|end|>\n",
        variables={
            "system_prompt": "You are a helpful AI assistant.",
        },
    ),

    # llama.cpp templates (same as Ollama for GGUF models)
    "llamacpp:llama3": ModelPromptTemplate(
        provider_id="llamacpp",
        model="llama3",
        system_template="<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>",
        user_template="<|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|>",
        assistant_template="<|start_header_id|>assistant<|end_header_id|>\n\n{assistant_prompt}<|eot_id|>",
        variables={
            "system_prompt": "You are a helpful AI assistant.",
        },
    ),
    "llamacpp:mistral": ModelPromptTemplate(
        provider_id="llamacpp",
        model="mistral",
        system_template="<s>[INST] {system_prompt} [/INST]",
        user_template="[INST] {user_prompt} [/INST]",
        assistant_template="{assistant_prompt}</s>",
        variables={
            "system_prompt": "You are a helpful AI assistant.",
        },
    ),

    # vLLM templates (OpenAI-compatible, but some models need specific formats)
    "vllm:meta-llama/Meta-Llama-3-8B-Instruct": ModelPromptTemplate(
        provider_id="vllm",
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        system_template="<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>",
        user_template="<|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|>",
        assistant_template="<|start_header_id|>assistant<|end_header_id|>\n\n{assistant_prompt}<|eot_id|>",
        variables={
            "system_prompt": "You are a helpful AI assistant.",
        },
    ),
    "vllm:meta-llama/Meta-Llama-3-70B-Instruct": ModelPromptTemplate(
        provider_id="vllm",
        model="meta-llama/Meta-Llama-3-70B-Instruct",
        system_template="<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>",
        user_template="<|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|>",
        assistant_template="<|start_header_id|>assistant<|end_header_id|>\n\n{assistant_prompt}<|eot_id|>",
        variables={
            "system_prompt": "You are a helpful AI assistant.",
        },
    ),
    "vllm:mistralai/Mistral-7B-Instruct-v0.3": ModelPromptTemplate(
        provider_id="vllm",
        model="mistralai/Mistral-7B-Instruct-v0.3",
        system_template="<s>[INST] {system_prompt} [/INST]",
        user_template="[INST] {user_prompt} [/INST]",
        assistant_template="{assistant_prompt}</s>",
        variables={
            "system_prompt": "You are a helpful AI assistant.",
        },
    ),
    "vllm:mistralai/Mixtral-8x7B-Instruct-v0.1": ModelPromptTemplate(
        provider_id="vllm",
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        system_template="<s>[INST] {system_prompt} [/INST]",
        user_template="[INST] {user_prompt} [/INST]",
        assistant_template="{assistant_prompt}</s>",
        variables={
            "system_prompt": "You are a helpful AI assistant.",
        },
    ),

    # TGI templates
    "tgi:default": ModelPromptTemplate(
        provider_id="tgi",
        model="tgi-model",
        system_template="<|system|>\n{system_prompt}\n",
        user_template="<|user|>\n{user_prompt}\n",
        assistant_template="<|assistant|>\n{assistant_prompt}\n",
        variables={
            "system_prompt": "You are a helpful AI assistant.",
        },
    ),
    "tgi:llama3": ModelPromptTemplate(
        provider_id="tgi",
        model="llama3",
        system_template="<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>",
        user_template="<|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|>",
        assistant_template="<|start_header_id|>assistant<|end_header_id|>\n\n{assistant_prompt}<|eot_id|>",
        variables={
            "system_prompt": "You are a helpful AI assistant.",
        },
    ),
}


class PromptTemplateManager:
    """Manages model-specific prompt templates."""

    def __init__(self) -> None:
        self._templates: Dict[str, ModelPromptTemplate] = dict(BUILTIN_TEMPLATES)
        self._custom_templates: Dict[str, ModelPromptTemplate] = {}

    def get_template(self, provider_id: str, model: str) -> Optional[ModelPromptTemplate]:
        """Get template for a provider/model combination."""
        key = f"{provider_id}:{model}"
        return self._templates.get(key) or self._custom_templates.get(key)

    def get_template_flexible(self, provider_id: str, model: str) -> Optional[ModelPromptTemplate]:
        """Get template with flexible matching (e.g., partial model name)."""
        key = f"{provider_id}:{model}"
        if key in self._templates:
            return self._templates[key]
        if key in self._custom_templates:
            return self._custom_templates[key]

        # Try partial match on model name
        for template_key, template in self._templates.items():
            if template_key.startswith(f"{provider_id}:") and model in template_key:
                return template
        for template_key, template in self._custom_templates.items():
            if template_key.startswith(f"{provider_id}:") and model in template_key:
                return template

        return None

    def register_template(self, template: ModelPromptTemplate) -> None:
        """Register a custom template."""
        key = f"{template.provider_id}:{template.model}"
        self._custom_templates[key] = template

    def unregister_template(self, provider_id: str, model: str) -> bool:
        """Unregister a custom template."""
        key = f"{provider_id}:{model}"
        if key in self._custom_templates:
            del self._custom_templates[key]
            return True
        return False

    def list_templates(self, provider_id: Optional[str] = None) -> List[ModelPromptTemplate]:
        """List all templates, optionally filtered by provider."""
        all_templates = list(self._templates.values()) + list(self._custom_templates.values())
        if provider_id:
            return [t for t in all_templates if t.provider_id == provider_id]
        return all_templates

    def format_messages(
        self,
        provider_id: str,
        model: str,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Format messages using the model's template."""
        template = self.get_template_flexible(provider_id, model)
        if not template:
            return messages  # No template, return as-is

        vars_dict = dict(template.variables)
        if system_prompt:
            vars_dict["system_prompt"] = system_prompt

        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                if template.system_template:
                    formatted.append({
                        "role": "system",
                        "content": template.system_template.format(
                            system_prompt=vars_dict.get("system_prompt", ""),
                            user_prompt=content,
                            assistant_prompt="",
                        ),
                    })
            elif role == "user":
                if template.user_template:
                    formatted.append({
                        "role": "user",
                        "content": template.user_template.format(
                            system_prompt=vars_dict.get("system_prompt", ""),
                            user_prompt=content,
                            assistant_prompt="",
                        ),
                    })
            elif role == "assistant":
                if template.assistant_template:
                    formatted.append({
                        "role": "assistant",
                        "content": template.assistant_template.format(
                            system_prompt=vars_dict.get("system_prompt", ""),
                            user_prompt="",
                            assistant_prompt=content,
                        ),
                    })

        return formatted

    def format_prompt(
        self,
        provider_id: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        assistant_prompt: str = "",
    ) -> str:
        """Format a complete prompt using the template."""
        template = self.get_template_flexible(provider_id, model)
        if not template:
            return f"System: {system_prompt}\nUser: {user_prompt}\nAssistant: {assistant_prompt}"

        vars_dict = dict(template.variables)
        vars_dict.update({
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "assistant_prompt": assistant_prompt,
        })

        parts = []
        if template.system_template:
            parts.append(template.system_template.format(**vars_dict))
        if template.user_template:
            parts.append(template.user_template.format(**vars_dict))
        if assistant_prompt and template.assistant_template:
            parts.append(template.assistant_template.format(**vars_dict))

        return "\n".join(parts)


# Global template manager
_template_manager: Optional[PromptTemplateManager] = None


def get_template_manager() -> PromptTemplateManager:
    """Get the global template manager instance."""
    global _template_manager
    if _template_manager is None:
        _template_manager = PromptTemplateManager()
    return _template_manager