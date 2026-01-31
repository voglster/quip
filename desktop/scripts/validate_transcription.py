#!/usr/bin/env python3
"""Validation script for transcription service initialization.

This script tests whether the transcription service properly initializes
and can be used for voice recording transcription.

Usage:
    cd desktop
    uv run python scripts/validate_transcription.py
"""

import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, ".")

from config import config


def test_transcription_service_direct():
    """Test the transcription service directly."""
    print("\n=== Testing TranscriptionService directly ===")

    from transcription import create_transcription_service

    print(f"Model size: {config.voice_model_size}")
    print(f"Language: {config.voice_language}")

    print("\n1. Creating transcription service...")
    start = time.time()
    service = create_transcription_service(
        model_size=config.voice_model_size, language=config.voice_language
    )
    print(f"   Created in {time.time() - start:.2f}s")

    print("\n2. Calling initialize_async()...")
    start = time.time()
    service.initialize_async()
    print(f"   Called in {time.time() - start:.4f}s")

    print("\n3. Checking is_initialized immediately...")
    print(f"   is_initialized = {service.is_initialized}")

    print("\n4. Waiting for initialization (timeout=30s)...")
    start = time.time()
    success = service.wait_for_initialization(timeout=30.0)
    elapsed = time.time() - start
    print(f"   wait_for_initialization returned: {success}")
    print(f"   Waited {elapsed:.2f}s")
    print(f"   is_initialized = {service.is_initialized}")

    if success:
        print("\n✓ Transcription service initialized successfully!")
    else:
        print("\n✗ Transcription service FAILED to initialize!")
        return False

    return True


def test_voice_handler():
    """Test the VoiceHandler's transcription loading."""
    print("\n=== Testing VoiceHandler ===")

    # Note: debug_mode is read-only from config file

    from voice.voice_handler import VoiceHandler

    print("\n1. Creating VoiceHandler (this starts background loading)...")
    start = time.time()
    handler = VoiceHandler()
    print(f"   Created in {time.time() - start:.4f}s")

    print("\n2. Checking initial state...")
    print(f"   transcription_service: {handler.transcription_service}")
    print(f"   transcription_loading: {handler.transcription_loading}")
    print(f"   transcription_failed: {handler.transcription_failed}")
    print(f"   status: {handler.get_transcription_status()}")

    print("\n3. Waiting for transcription to be ready (polling every 0.5s, max 60s)...")
    start = time.time()
    timeout = 60.0
    while time.time() - start < timeout:
        status = handler.get_transcription_status()
        elapsed = time.time() - start
        print(f"   [{elapsed:.1f}s] status = {status}")

        if status == "ready":
            print(f"\n✓ VoiceHandler transcription ready in {elapsed:.2f}s!")
            # debug_mode restored automatically (read-only)
            return True
        elif status == "failed":
            print(f"\n✗ VoiceHandler transcription FAILED after {elapsed:.2f}s!")
            # debug_mode restored automatically (read-only)
            return False

        time.sleep(0.5)

    print(f"\n✗ VoiceHandler transcription timed out after {timeout}s!")
    print("   Final state:")
    print(f"   transcription_service: {handler.transcription_service}")
    print(f"   transcription_loading: {handler.transcription_loading}")
    print(f"   transcription_failed: {handler.transcription_failed}")

    # debug_mode restored automatically (read-only)
    return False


def test_vosk_model():
    """Test if Vosk model is available."""
    print("\n=== Testing Vosk Model Availability ===")

    try:
        from vosk import SetLogLevel

        SetLogLevel(-1)  # Suppress Vosk logs
        print("✓ Vosk module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import vosk: {e}")
        return False

    # Check model paths
    from pathlib import Path

    model_paths = [
        Path.home() / ".cache" / "vosk",
        Path.home() / ".local" / "share" / "vosk",
        Path("/usr/share/vosk"),
    ]

    print("\nSearching for Vosk models...")
    for path in model_paths:
        if path.exists():
            print(f"  Checking {path}...")
            for item in path.iterdir():
                if item.is_dir() and "model" in item.name.lower():
                    print(f"    Found: {item}")

    return True


def main():
    print("=" * 60)
    print("Transcription Service Validation Script")
    print("=" * 60)

    results = {}

    # Test 1: Check Vosk availability
    results["vosk_model"] = test_vosk_model()

    # Test 2: Direct transcription service test
    results["direct_service"] = test_transcription_service_direct()

    # Test 3: VoiceHandler integration test
    if results["direct_service"]:
        results["voice_handler"] = test_voice_handler()
    else:
        print("\nSkipping VoiceHandler test since direct service test failed.")
        results["voice_handler"] = False

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for test, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test}: {status}")

    all_passed = all(results.values())
    print("\n" + ("All tests passed!" if all_passed else "Some tests FAILED!"))

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
