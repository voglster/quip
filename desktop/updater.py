"""Update checking and management for Quip"""

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Optional, Dict, Any

# Handle tomli import for Python < 3.11
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class UpdateChecker:
    """Handles checking for and performing updates with rate limiting and caching"""

    def __init__(
        self,
        repo_url: str = "https://api.github.com/repos/voglster/quip/releases/latest",
    ):
        self.repo_url = repo_url
        self.current_version = self._get_current_version()
        self.install_dir = Path.home() / ".local" / "share" / "quip"
        self.cache_dir = Path.home() / ".cache" / "quip"
        self.cache_file = self.cache_dir / "update_check.json"
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_current_version(self) -> str:
        """Read current version from pyproject.toml"""
        try:
            # Try to find pyproject.toml in the current directory or parent directories
            current_dir = Path(__file__).parent
            pyproject_path = current_dir / "pyproject.toml"

            if not pyproject_path.exists():
                # Try parent directory (for installed version)
                pyproject_path = current_dir.parent / "pyproject.toml"

            if not pyproject_path.exists():
                # Try install directory
                if self.install_dir.exists():
                    pyproject_path = self.install_dir / "desktop" / "pyproject.toml"

            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    pyproject_data = tomllib.load(f)
                    return pyproject_data.get("project", {}).get("version", "0.1.0")
        except Exception:
            pass

        # Fallback version if we can't read pyproject.toml
        return "0.1.0"

    def _load_cache(self) -> Dict[str, Any]:
        """Load cached update check data"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, "r") as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
        return {}

    def _save_cache(self, data: Dict[str, Any]):
        """Save update check data to cache"""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            # Silently fail cache operations
            pass

    def _should_check_for_updates(self, check_interval_hours: int) -> bool:
        """Check if enough time has passed since last update check"""
        cache_data = self._load_cache()
        last_check = cache_data.get("last_check_timestamp", 0)
        current_time = time.time()

        # Convert interval to seconds
        interval_seconds = check_interval_hours * 3600

        return (current_time - last_check) >= interval_seconds

    def check_for_updates(
        self, check_interval_hours: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        Check if updates are available with rate limiting.

        Args:
            check_interval_hours: Minimum hours between checks

        Returns:
            Update info dict or None if no update available or rate limited
        """
        # Check rate limiting
        if not self._should_check_for_updates(check_interval_hours):
            cache_data = self._load_cache()
            cached_update = cache_data.get("cached_update_info")
            if cached_update and self._is_newer_version(
                cached_update["version"], self.current_version
            ):
                return cached_update
            return None

        try:
            # Make the API request
            request = urllib.request.Request(
                self.repo_url, headers={"User-Agent": f"Quip/{self.current_version}"}
            )

            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read())

            latest_version = data["tag_name"].lstrip("v")

            # Update cache with current timestamp
            cache_data = {
                "last_check_timestamp": time.time(),
                "latest_version": latest_version,
                "current_version": self.current_version,
            }

            # Check if there's an update
            if self._is_newer_version(latest_version, self.current_version):
                update_info = {
                    "version": latest_version,
                    "url": data["html_url"],
                    "description": data.get("body", ""),
                    "download_url": self._get_download_url(data),
                }
                cache_data["cached_update_info"] = update_info
                self._save_cache(cache_data)
                return update_info
            else:
                # No update available, clear cached update info
                cache_data.pop("cached_update_info", None)
                self._save_cache(cache_data)
                return None

        except Exception:
            # On error, try to return cached info if available and still valid
            cache_data = self._load_cache()
            cached_update = cache_data.get("cached_update_info")
            if cached_update and self._is_newer_version(
                cached_update["version"], self.current_version
            ):
                return cached_update

            # Silently fail - don't interrupt user experience
            # In debug mode, we might want to log this
            return None

    def _get_download_url(self, release_data: Dict[str, Any]) -> Optional[str]:
        """Extract the appropriate download URL from release data"""
        try:
            # Look for a tarball or zipball URL
            return release_data.get("tarball_url") or release_data.get("zipball_url")
        except Exception:
            return None

    def _is_newer_version(self, latest: str, current: str) -> bool:
        """Compare version strings (semantic versioning)"""
        try:
            # Handle pre-release versions by splitting on '-'
            latest_clean = latest.split("-")[0]
            current_clean = current.split("-")[0]

            latest_parts = [int(x) for x in latest_clean.split(".")]
            current_parts = [int(x) for x in current_clean.split(".")]

            # Pad with zeros to make same length
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))

            return latest_parts > current_parts
        except (ValueError, AttributeError):
            return False

    def update_available_message(self, update_info: Dict[str, Any]) -> str:
        """Format update notification message"""
        return f"🎉 Quip v{update_info['version']} is available! Run: quip --update"

    def perform_update(self) -> bool:
        """Perform the actual update by running git pull in install directory"""
        if not self.install_dir.exists():
            print("❌ Quip installation directory not found")
            print(f"Expected directory: {self.install_dir}")
            return False

        try:
            print("🔄 Updating Quip...")

            # Check if it's a git repository
            git_dir = self.install_dir / ".git"
            if not git_dir.exists():
                print(
                    "❌ Not a git repository. Please reinstall Quip using the installer."
                )
                return False

            # Update the git repository
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=self.install_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                print(f"❌ Git update failed: {result.stderr}")
                return False

            # Check if there were any changes
            if "Already up to date" in result.stdout:
                print("✅ Quip is already up to date!")
                return True

            # Update dependencies
            desktop_dir = self.install_dir / "desktop"
            if desktop_dir.exists():
                print("📦 Updating dependencies...")
                dep_result = subprocess.run(
                    ["uv", "sync"],
                    cwd=desktop_dir,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                if dep_result.returncode != 0:
                    print(f"⚠️  Warning: Dependency update failed: {dep_result.stderr}")
                    print(
                        "The update may still work, but some features might not function correctly."
                    )

            # Clear update cache to force a fresh check next time
            try:
                if self.cache_file.exists():
                    self.cache_file.unlink()
            except Exception:
                pass

            print("✅ Quip updated successfully!")
            print("🔄 Restart any running instances to use the new version")
            return True

        except subprocess.TimeoutExpired:
            print(
                "❌ Update timed out. Please check your internet connection and try again."
            )
            return False
        except subprocess.CalledProcessError as e:
            print(f"❌ Update failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error during update: {e}")
            return False

    def get_update_status(self) -> Dict[str, Any]:
        """Get current update status and cached information"""
        cache_data = self._load_cache()

        return {
            "current_version": self.current_version,
            "last_check": cache_data.get("last_check_timestamp", 0),
            "cached_update_available": bool(cache_data.get("cached_update_info")),
            "cached_update_info": cache_data.get("cached_update_info"),
            "cache_file": str(self.cache_file),
        }


def main():
    """CLI entry point for update checker"""
    updater = UpdateChecker()

    if len(sys.argv) > 1:
        if sys.argv[1] == "--update":
            success = updater.perform_update()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "--status":
            status = updater.get_update_status()
            print(f"Current version: {status['current_version']}")
            if status["cached_update_available"]:
                info = status["cached_update_info"]
                print(f"Update available: v{info['version']}")
            else:
                print("No updates available")
            sys.exit(0)
        elif sys.argv[1] == "--check":
            update_info = updater.check_for_updates(
                check_interval_hours=0
            )  # Force check
            if update_info:
                print(updater.update_available_message(update_info))
            else:
                print("✅ Quip is up to date")
            sys.exit(0)

    # Default behavior - check for updates with rate limiting
    update_info = updater.check_for_updates()
    if update_info:
        print(updater.update_available_message(update_info))
    else:
        print("✅ Quip is up to date")


if __name__ == "__main__":
    main()
