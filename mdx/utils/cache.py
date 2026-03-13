"""Cache implementation"""

from typing import Dict, Any, Optional
from collections import OrderedDict

class Cache:
    """Simple LRU cache implementation"""
    
    def __init__(self, max_size: int = 100):
        """Initialize cache with maximum size"""
        self.max_size = max_size
        self.cache = OrderedDict()
    
    def get(self, key: Any) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            # Move to end to mark as recently used
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def set(self, key: Any, value: Any) -> None:
        """Set value in cache"""
        if key in self.cache:
            # Move to end to mark as recently used
            self.cache.move_to_end(key)
        elif len(self.cache) >= self.max_size:
            # Remove least recently used item
            self.cache.popitem(last=False)
        self.cache[key] = value
    
    def clear(self) -> None:
        """Clear cache"""
        self.cache.clear()
    
    def __len__(self) -> int:
        """Get cache size"""
        return len(self.cache)