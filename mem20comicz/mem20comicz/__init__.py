"""mem20comicz — comic creation adapters, connectors, tools, pipelines and skills.

Provides a unified interface over popular comic-creation image generators
(Midjourney, Stable Diffusion, DALL-E, Ideogram, Flux, Leonardo) plus a
pipeline that turns a Z Corps shooting script into illustrated pages.
"""

__version__ = "1.0.0"

from .adapters import AdapterRegistry, BaseAdapter
from .pipeline import ComicPipeline

__all__ = ["AdapterRegistry", "BaseAdapter", "ComicPipeline", "__version__"]