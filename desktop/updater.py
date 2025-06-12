import json
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Optional


class UpdateChecker:
    def __init__(
        self,
        repo_url: str = "https://api.github.com/repos/voglster/quip/releases/latest",
    ):
        self.repo_url = repo_url
        self.current_version = "0.1.0"  # Will be read from pyproject.toml eventually
        self.install_dir = Path.home() / ".local" / "share" / "quip"

    def check_for_updates(self) -> Optional[dict]:
        """Check if updates are available. Returns update info or None."""
        try:
            with urllib.request.urlopen(self.repo_url, timeout=5) as response:
                data = json.loads(response.read())

            latest_version = data["tag_name"].lstrip("v")

            if self._is_newer_version(latest_version, self.current_version):
                return {
                    "version": latest_version,
                    "url": data["html_url"],
                    "description": data.get("body", ""),
                }

        except Exception:
            # Silently fail - don't interrupt user experience
            pass

        return None

    def _is_newer_version(self, latest: str, current: str) -> bool:
        """Compare version strings (simple semantic versioning)."""
        try:
            latest_parts = [int(x) for x in latest.split(".")]
            current_parts = [int(x) for x in current.split(".")]

            # Pad with zeros to make same length
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))

            return latest_parts > current_parts
        except ValueError:
            return False

    def update_available_message(self, update_info: dict) -> str:
        """Format update notification message."""
        return f"🎉 Quip v{update_info['version']} is available! Run: quip --update"

    def perform_update(self) -> bool:
        """Perform the actual update by running git pull in install directory."""
        if not self.install_dir.exists():
            print("❌ Quip installation directory not found")
            return False

        try:
            # Update the git repository
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=self.install_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                # Update dependencies
                desktop_dir = self.install_dir / "desktop"
                subprocess.run(["uv", "sync"], cwd=desktop_dir, check=True, timeout=60)

                print("✅ Quip updated successfully!")
                print("🔄 Restart any running instances to use the new version")
                return True
            else:
                print(f"❌ Update failed: {result.stderr}")
                return False

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            print(f"❌ Update failed: {e}")
            return False


def main():
    """CLI entry point for update checker."""
    if len(sys.argv) > 1 and sys.argv[1] == "--update":
        updater = UpdateChecker()
        success = updater.perform_update()
        sys.exit(0 if success else 1)
    else:
        # Just check for updates
        updater = UpdateChecker()
        update_info = updater.check_for_updates()
        if update_info:
            print(updater.update_available_message(update_info))
        else:
            print("✅ Quip is up to date")


if __name__ == "__main__":
    main()
