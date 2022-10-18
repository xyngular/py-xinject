"""
Used to lazily created shared singleton-like objects in a decoupled way.

"""

from .context import GlazyContext
from .dependency import Dependency, PerThreadDependency
from .proxy import ActiveResourceProxy
