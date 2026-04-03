from config import config
from core.app import QuipApplication


def validate_llm_config():
    """Validate and test LLM configuration"""
    from llm import llm_client, LLMError

    print("=== LLM Configuration Test ===")
    print()

    # Show current config
    print("📋 Current Configuration:")
    print(f"  Enabled: {config.llm_enabled}")
    print(f"  Base URL: {config.llm_base_url}")
    print(f"  Model: {config.llm_model}")
    print(f"  API Key: {'Set' if config.llm_api_key else 'Not set'}")
    print(f"  Timeout: {config.llm_timeout_seconds}s")
    print(f"  Max Tokens: {config.llm_max_tokens}")
    print(f"  Temperature: {config.llm_temperature}")
    print()

    if not config.llm_enabled:
        print("❌ LLM is disabled in configuration")
        print("   Enable it by setting 'enabled = true' in ~/.config/quip/config.toml")
        return

    if (
        not config.llm_api_key
        and "localhost" not in config.llm_base_url
        and "10.0.6.16" not in config.llm_base_url
    ):
        print("❌ No API key configured for cloud provider")
        print("   Set your API key in ~/.config/quip/config.toml")
        return

    # Test with sample text
    test_text = "hello wrld this mesage has bad grammer and speling"

    print(f'🧪 Testing with: "{test_text}"')
    print()

    try:
        print("⏳ Sending request to LLM...")
        improved_text = llm_client.improve_note(test_text)

        print("✅ Success!")
        print(f'📝 Original:  "{test_text}"')
        print(f'✨ Improved:  "{improved_text}"')
        print()
        print("🎉 LLM configuration is working correctly!")
        print("   You can now use Ctrl+I in Quip to improve your notes.")

    except LLMError as e:
        print(f"❌ LLM Error: {e}")

        # Provide helpful suggestions based on error
        error_str = str(e).lower()
        if "404" in error_str:
            print("💡 Suggestions:")
            print("   - Check if the base_url is correct")
            print("   - Verify the model name exists")
            if "generativelanguage" in config.llm_base_url:
                print("   - For Gemini, try model 'gemini-1.5-flash'")
        elif "401" in error_str or "403" in error_str:
            print("💡 Suggestions:")
            print("   - Check if your API key is valid")
            print("   - Verify API key has proper permissions")
        elif "connection" in error_str or "timeout" in error_str:
            print("💡 Suggestions:")
            print("   - Check if the service is running")
            print("   - Verify network connectivity")
            if "ollama" in config.llm_base_url.lower():
                print("   - Is Ollama running? Try: ollama list")

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")


def get_version():
    """Get version from _version.py"""
    try:
        from _version import __version__

        return __version__
    except ImportError:
        return "unknown"


def main():
    import sys

    # Handle CLI arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--update":
            from updater import UpdateChecker

            updater = UpdateChecker()
            success = updater.perform_update()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "--check-update":
            from updater import UpdateChecker

            updater = UpdateChecker()
            update_info = updater.check_for_updates()
            if update_info:
                print(updater.update_available_message(update_info))
            else:
                print("✅ Quip is up to date")
            sys.exit(0)
        elif sys.argv[1] == "--version":
            print(f"Quip v{get_version()}")
            sys.exit(0)
        elif sys.argv[1] == "--validate-llm-config":
            validate_llm_config()
            sys.exit(0)
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Quip - Frictionless thought capture")
            print()
            print("Usage:")
            print("  quip                          Start GUI mode")
            print("  quip --validate-llm-config    Test LLM configuration")
            print("  quip --check-update           Check for updates")
            print("  quip --update                 Perform update")
            print("  quip --version                Show version")
            print("  quip --help                   Show this help")
            sys.exit(0)

    # Normal GUI mode
    app = QuipApplication()
    app.run()


if __name__ == "__main__":
    main()
