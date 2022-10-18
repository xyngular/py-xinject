"""
Used to lazily created shared singleton-like objects in a decoupled way.

"""

from .context import GlazyContext
from .resource import Resource, PerThreadResource
from .proxy import ActiveResourceProxy
