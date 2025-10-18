#!/usr/bin/env python3
"""
Convert HuggingFace Whisper model to CTranslate2 format

Usage:
    python convert_to_ctranslate2.py

This will convert your 203-final model from HuggingFace format to CTranslate2.
"""

import os
import sys

def main():
    # Configuration
    source_model = "D:/data/models/203-final"
    output_dir = "D:/data/models/203-final-ct2"
    quantization = "int8_float16"  # Options: float16, int8_float16, int8, int16

    print("=" * 60)
    print("🔄 Converting Whisper Model to CTranslate2")
    print("=" * 60)
    print(f"Source: {source_model}")
    print(f"Output: {output_dir}")
    print(f"Quantization: {quantization}")
    print()

    # Check if source exists
    if not os.path.isdir(source_model):
        print(f"❌ Error: Source model not found at {source_model}")
        sys.exit(1)

    # Check if ctranslate2 is installed
    try:
        import ctranslate2
        print(f"✅ CTranslate2 version: {ctranslate2.__version__}")
    except ImportError:
        print("❌ CTranslate2 not installed!")
        print("\n📦 Installing CTranslate2...")
        os.system(f"{sys.executable} -m pip install ctranslate2")
        print()

    # Import converter
    try:
        import ctranslate2
        print("✅ CTranslate2 imported successfully")
    except ImportError:
        print("❌ Failed to import CTranslate2 after installation")
        sys.exit(1)

    # Convert model
    print("\n🔄 Converting model (this may take a few minutes)...")
    print(f"   This will create optimized model files in: {output_dir}")
    print()

    try:
        converter_command = f"ct2-transformers-converter --model {source_model} --output_dir {output_dir} --quantization {quantization} --force"
        print(f"Running: {converter_command}")
        print()

        result = os.system(converter_command)

        if result == 0:
            print()
            print("=" * 60)
            print("✅ Conversion successful!")
            print("=" * 60)
            print()

            # Copy necessary files from source to output
            print("📁 Copying additional files (tokenizer, preprocessor, etc.)...")
            import shutil

            files_to_copy = [
                "preprocessor_config.json",
                "tokenizer.json",
                "tokenizer_config.json",
                "special_tokens_map.json",
                "normalizer.json",
                "merges.txt",
                "vocab.json",
                "added_tokens.json",
                "generation_config.json"
            ]

            copied_files = []
            for filename in files_to_copy:
                src_file = os.path.join(source_model, filename)
                dst_file = os.path.join(output_dir, filename)

                if os.path.exists(src_file):
                    try:
                        shutil.copy2(src_file, dst_file)
                        copied_files.append(filename)
                        print(f"   ✅ Copied: {filename}")
                    except Exception as e:
                        print(f"   ⚠️  Failed to copy {filename}: {e}")
                else:
                    print(f"   ⏭️  Skipped: {filename} (not found in source)")

            print(f"\n   Total files copied: {len(copied_files)}/{len(files_to_copy)}")
            print()
            print("📊 Model Statistics:")

            # Get model sizes
            import subprocess
            try:
                # Original size
                orig_size = subprocess.check_output(
                    f'du -sh "{source_model}"',
                    shell=True,
                    text=True
                ).split()[0]

                # Converted size
                ct2_size = subprocess.check_output(
                    f'du -sh "{output_dir}"',
                    shell=True,
                    text=True
                ).split()[0]

                print(f"   Original (HuggingFace): {orig_size}")
                print(f"   Converted (CTranslate2): {ct2_size}")
            except:
                pass

            print()
            print("📝 Next Steps:")
            print("   1. Update your .env file:")
            print(f"      DEFAULT_MODEL_NAME=203-final-ct2")
            print()
            print("   2. Restart the service:")
            print("      docker-compose restart whisper-gpu")
            print("      # or")
            print("      python faster-whisper-service.py")
            print()
            print("🚀 Expected improvements:")
            print("   - Speed: 4x faster")
            print("   - VRAM: ~2-3 GB (down from 8.8 GB)")
            print("   - Better chunking support")
            print()
        else:
            print("❌ Conversion failed!")
            print("\nTroubleshooting:")
            print("1. Make sure the source model is valid HuggingFace format")
            print("2. Check disk space")
            print("3. Try manual conversion:")
            print(f"   ct2-transformers-converter --model {source_model} --output_dir {output_dir} --quantization {quantization}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
