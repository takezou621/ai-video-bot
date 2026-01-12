"""
API Key Manager - Rotate multiple API keys to avoid rate limits
Implements the blog's strategy of using multiple API keys in parallel
"""
import os
import time
import json
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import threading


class APIKeyManager:
    """
    Manages multiple API keys with automatic rotation on rate limit errors.

    Features:
    - Round-robin key selection
    - Rate limit tracking
    - Automatic key blacklisting after failures
    - Thread-safe operations
    """

    def __init__(self, service_name: str, keys: List[str] = None):
        """
        Initialize API key manager.

        Args:
            service_name: Name of the service (e.g., 'GEMINI', 'OPENAI')
            keys: List of API keys. If None, loads from environment
        """
        self.service_name = service_name
        self.keys = keys or self._load_keys_from_env()
        self.current_index = 0
        self.lock = threading.Lock()

        # Track failures per key (key -> failure count)
        self.failures: Dict[str, int] = {key: 0 for key in self.keys}

        # Track rate limit cooldown (key -> cooldown_until timestamp)
        self.cooldowns: Dict[str, datetime] = {}

        # Statistics
        self.stats = {
            "total_requests": 0,
            "total_failures": 0,
            "key_switches": 0
        }

        # State file for persistence
        self.state_file = Path(f".api_key_state_{service_name.lower()}.json")
        self._load_state()

        if not self.keys:
            raise ValueError(f"No API keys found for {service_name}. Set {service_name}_API_KEY or {service_name}_API_KEYS")

        print(f"[API Key Manager] Initialized for {service_name} with {len(self.keys)} key(s)")

    def _load_keys_from_env(self) -> List[str]:
        """Load API keys from environment variables."""
        keys = []

        # Try multiple keys first (GEMINI_API_KEYS="key1,key2,key3")
        multi_key_var = f"{self.service_name}_API_KEYS"
        if os.getenv(multi_key_var):
            keys_str = os.getenv(multi_key_var, "")
            keys = [k.strip() for k in keys_str.split(",") if k.strip()]

        # Fallback to single key
        if not keys:
            single_key = os.getenv(f"{self.service_name}_API_KEY")
            if single_key:
                keys = [single_key]

        return keys

    def get_key(self) -> str:
        """
        Get next available API key.

        Returns:
            API key string

        Raises:
            RuntimeError: If all keys are on cooldown or failed
        """
        with self.lock:
            self.stats["total_requests"] += 1

            # Try to find an available key
            attempts = 0
            max_attempts = len(self.keys) * 2  # Try each key twice

            while attempts < max_attempts:
                key = self.keys[self.current_index]

                # Check if key is on cooldown
                if key in self.cooldowns:
                    if datetime.now() < self.cooldowns[key]:
                        # Still on cooldown, try next key
                        self.current_index = (self.current_index + 1) % len(self.keys)
                        attempts += 1
                        continue
                    else:
                        # Cooldown expired, remove it
                        del self.cooldowns[key]

                # Check if key has too many failures
                if self.failures.get(key, 0) >= 5:
                    # Key is blacklisted, try next
                    self.current_index = (self.current_index + 1) % len(self.keys)
                    attempts += 1
                    continue

                # Found a good key
                return key

            # All keys are unavailable - try the least-failed one
            best_key = min(self.keys, key=lambda k: self.failures.get(k, 0))
            print(f"[WARNING] All {self.service_name} keys on cooldown/failed, using least-failed key")
            return best_key

    def report_success(self, key: str):
        """
        Report successful API call.

        Args:
            key: The API key that was used
        """
        with self.lock:
            # Reset failure count on success
            if key in self.failures:
                self.failures[key] = 0

            # Move to next key for load balancing
            self.current_index = (self.current_index + 1) % len(self.keys)
            self._save_state()

    def report_failure(self, key: str, is_rate_limit: bool = False):
        """
        Report failed API call.

        Args:
            key: The API key that failed
            is_rate_limit: Whether failure was due to rate limiting
        """
        with self.lock:
            self.stats["total_failures"] += 1
            self.failures[key] = self.failures.get(key, 0) + 1

            if is_rate_limit:
                # Put key on 60-minute cooldown
                cooldown_until = datetime.now() + timedelta(minutes=60)
                self.cooldowns[key] = cooldown_until
                print(f"[API Key Manager] Rate limit hit for {self.service_name} key ...{key[-6:]}, cooldown until {cooldown_until.strftime('%H:%M')}")
            else:
                # Regular failure - just increment counter
                print(f"[API Key Manager] Failure #{self.failures[key]} for {self.service_name} key ...{key[-6:]}")

            # Switch to next key
            self.current_index = (self.current_index + 1) % len(self.keys)
            self.stats["key_switches"] += 1

            self._save_state()

    def get_stats(self) -> Dict:
        """Get usage statistics."""
        with self.lock:
            return {
                **self.stats,
                "total_keys": len(self.keys),
                "active_keys": len([k for k in self.keys if self.failures.get(k, 0) < 5]),
                "keys_on_cooldown": len(self.cooldowns)
            }

    def _save_state(self):
        """Save state to file for persistence."""
        try:
            state = {
                "failures": self.failures,
                "cooldowns": {k: v.isoformat() for k, v in self.cooldowns.items()},
                "stats": self.stats,
                "current_index": self.current_index
            }
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"[WARNING] Failed to save API key state: {e}")

    def _load_state(self):
        """Load state from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, "r") as f:
                    state = json.load(f)

                self.failures = state.get("failures", {})

                # Convert ISO format back to datetime
                cooldowns_iso = state.get("cooldowns", {})
                self.cooldowns = {
                    k: datetime.fromisoformat(v)
                    for k, v in cooldowns_iso.items()
                    if datetime.fromisoformat(v) > datetime.now()  # Only load active cooldowns
                }

                self.stats = state.get("stats", self.stats)
                self.current_index = state.get("current_index", 0)

                print(f"[API Key Manager] Loaded state: {len(self.cooldowns)} key(s) on cooldown")
        except Exception as e:
            print(f"[WARNING] Failed to load API key state: {e}")


# Global managers (initialized on first use)
_managers: Dict[str, APIKeyManager] = {}


def get_api_key(service_name: str) -> str:
    """
    Get API key for a service with automatic rotation.

    Args:
        service_name: Service name (e.g., 'GEMINI', 'OPENAI')

    Returns:
        API key string
    """
    global _managers

    if service_name not in _managers:
        _managers[service_name] = APIKeyManager(service_name)

    return _managers[service_name].get_key()


def report_api_success(service_name: str, key: str):
    """Report successful API call."""
    global _managers
    if service_name in _managers:
        _managers[service_name].report_success(key)


def report_api_failure(service_name: str, key: str, is_rate_limit: bool = False):
    """Report failed API call."""
    global _managers
    if service_name in _managers:
        _managers[service_name].report_failure(key, is_rate_limit)


def get_api_stats(service_name: str) -> Dict:
    """Get API usage statistics."""
    global _managers
    if service_name in _managers:
        return _managers[service_name].get_stats()
    return {}


if __name__ == "__main__":
    # Test
    print("API Key Manager Test\n")

    # Test with environment variable
    os.environ["TEST_API_KEYS"] = "key1,key2,key3"

    manager = APIKeyManager("TEST")

    print("\n1. Testing key rotation:")
    for i in range(5):
        key = manager.get_key()
        print(f"  Request {i+1}: {key}")
        manager.report_success(key)

    print("\n2. Testing failure handling:")
    key1 = manager.get_key()
    print(f"  Using key: {key1}")
    manager.report_failure(key1)

    key2 = manager.get_key()
    print(f"  Switched to key: {key2}")

    print("\n3. Testing rate limit cooldown:")
    manager.report_failure(key2, is_rate_limit=True)
    print(f"  Key {key2} on cooldown")

    key3 = manager.get_key()
    print(f"  Switched to key: {key3}")

    print("\n4. Statistics:")
    stats = manager.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n✓ Test complete")
