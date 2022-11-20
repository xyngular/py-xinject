"""
Used to lazily created shared singleton-like objects in a decoupled way.

"""

from .context import XContext
from .dependency import Dependency, DependencyPerThread
from .proxy import CurrentDependencyProxy
