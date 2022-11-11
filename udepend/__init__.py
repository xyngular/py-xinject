"""
Used to lazily created shared singleton-like objects in a decoupled way.

"""

from .context import UContext
from .dependency import Dependency, PerThreadDependency
from .proxy import CurrentDependencyProxy
