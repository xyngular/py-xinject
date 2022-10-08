"""
Used to lazily created shared singleton-like objects in a decoupled way.

# How To Use

..include:: ../README.md
"""

from .context import Context
from .resource import Resource, PerThreadResource
from .proxy import ActiveResourceProxy
