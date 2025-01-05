# --------------------------------
# 1) Move Singleton to separate module (not auto-reloaded).
# 2) Maintain persistent object via st.cache_resource.
# 3) Disable dev reload watchers or pass --server.fileWatcherType="none" if needed.

# singleton_manager.py
import streamlit as st
from threading import Lock
from typing import Optional, Any, Dict

class SingletonManager:
    """
    Thread-safe singleton manager that persists across Streamlit's auto-reloading.
    Uses st.cache_resource to maintain state.
    """
    _instance: Optional['SingletonManager'] = None
    _lock: Lock = Lock()
    _registry: Dict[str, Any] = {}

    def __new__(cls) -> 'SingletonManager':
        with cls._lock:
            if not cls._instance:
                cls._instance = super(SingletonManager, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the singleton manager if not already initialized."""
        if not getattr(self, '_initialized', False):
            self._initialized = True
            self._registry = {}

    def register(self, key: str, instance: Any) -> None:
        """Register a singleton instance with a given key."""
        with self._lock:
            self._registry[key] = instance

    def get(self, key: str) -> Optional[Any]:
        """Get a registered singleton instance by key."""
        return self._registry.get(key)

    def remove(self, key: str) -> None:
        """Remove a registered singleton instance."""
        with self._lock:
            self._registry.pop(key, None)

    def clear(self) -> None:
        """Clear all registered singletons."""
        with self._lock:
            self._registry.clear()

@st.cache_resource
def get_manager() -> SingletonManager:
    """Get or create the cached singleton manager instance."""
    manager = SingletonManager()
    return manager

# Usage example:
# from backend.core.singleton_manager import get_manager
#
# def main():
#     manager = get_manager()
#     
#     # Register a singleton
#     if not manager.get('my_singleton'):
#         manager.register('my_singleton', MySingletonClass())
#     
#     # Get the singleton instance
#     my_singleton = manager.get('my_singleton')
