"""Adapter layer: one BaseAdapter per image provider, registered by name."""

import os
import abc
import json
import urllib.request
import urllib.error


class BaseAdapter(abc.ABC):
    """Common interface for an image-generation provider."""

    name: str = ""
    env_key: str = ""

    def __init__(self, api_key=None, **kwargs):
        self.api_key = api_key or os.environ.get(self.env_key, "")
        self.options = kwargs

    def is_configured(self):
        return bool(self.api_key)

    @abc.abstractmethod
    def generate(self, prompt, out_path, **kwargs):
        """Generate an image for `prompt`, save to `out_path`. Return path."""


class OpenAIAdapter(BaseAdapter):
    name = "openai"
    env_key = "OPENAI_API_KEY"

    def generate(self, prompt, out_path, size="1024x1024", model="gpt-image-1", **kwargs):
        if not self.is_configured():
            raise RuntimeError("OPENAI_API_KEY not set")
        body = {"model": model, "prompt": prompt, "size": size, "n": 1}
        req = urllib.request.Request(
            "https://api.openai.com/v1/images/generations",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as r:
            data = json.load(r)
        url = data["data"][0].get("url")
        if url:
            urllib.request.urlretrieve(url, out_path)
        else:
            import base64
            with open(out_path, "wb") as f:
                f.write(base64.b64decode(data["data"][0]["b64_json"]))
        return out_path


class StabilityAdapter(BaseAdapter):
    name = "stability"
    env_key = "STABILITY_API_KEY"

    def generate(self, prompt, out_path, **kwargs):
        if not self.is_configured():
            raise RuntimeError("STABILITY_API_KEY not set")
        req = urllib.request.Request(
            "https://api.stability.ai/v2beta/stable-image/generate/sd3",
            data=None,
            headers={"Authorization": f"Bearer {self.api_key}", "Accept": "image/*"},
        )
        # Stability uses multipart; fall back to a clear error rather than fake data.
        raise NotImplementedError("Stability multipart upload not yet implemented")


class ReplicateAdapter(BaseAdapter):
    name = "replicate"
    env_key = "REPLICATE_API_TOKEN"

    def generate(self, prompt, out_path, model="black-forest-labs/flux-schnell", **kwargs):
        if not self.is_configured():
            raise RuntimeError("REPLICATE_API_TOKEN not set")
        body = {"input": {"prompt": prompt}}
        req = urllib.request.Request(
            f"https://api.replicate.com/v1/models/{model}/predictions",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Token {self.api_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as r:
            data = json.load(r)
        # Polling omitted for brevity; return prediction id.
        return data.get("id", "")


class AdapterRegistry:
    _adapters = {
        "openai": OpenAIAdapter,
        "stability": StabilityAdapter,
        "replicate": ReplicateAdapter,
    }

    @classmethod
    def get(cls, name, **kwargs):
        if name not in cls._adapters:
            raise ValueError(f"Unknown adapter: {name}")
        return cls._adapters[name](**kwargs)

    @classmethod
    def available(cls):
        out = []
        for name, klass in cls._adapters.items():
            a = klass()
            out.append({"name": name, "configured": a.is_configured()})
        return out