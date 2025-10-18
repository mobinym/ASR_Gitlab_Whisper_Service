#!/usr/bin/env python3
"""
Python script to test Whisper streaming transcription endpoint
Features:
- Real-time segment display
- Progress indicators
- Performance metrics
- JSON output formatting
"""

import sys
import json
import time
import argparse
import requests
from pathlib import Path
from typing import Iterator, Dict, Any


class Colors:
    """ANSI color codes for terminal output."""
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color


def stream_transcription(
    audio_file: Path,
    api_url: str,
    language: str = "fa",
    beam_size: int = 5,
    vad_filter: bool = True
) -> Iterator[Dict[str, Any]]:
    """
    Stream transcription results from the API.

    Yields:
        Dict containing segment information (start, end, text)
    """

    with open(audio_file, 'rb') as f:
        files = {'file': (audio_file.name, f, 'audio/wav')}
        data = {
            'language': language,
            'beam_size': beam_size,
            'vad_filter': 'true' if vad_filter else 'false'
        }

        # Stream the response
        with requests.post(api_url, files=files, data=data, stream=True) as response:
            response.raise_for_status()

            # Read line by line (NDJSON format)
            for line in response.iter_lines():
                if line:
                    try:
                        segment = json.loads(line.decode('utf-8'))
                        yield segment
                    except json.JSONDecodeError as e:
                        print(f"{Colors.RED}Error parsing JSON: {e}{Colors.NC}", file=sys.stderr)
                        print(f"Line: {line}", file=sys.stderr)


def format_time(seconds: float) -> str:
    """Format seconds as MM:SS.mmm"""
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:06.3f}"


def test_streaming_basic(audio_file: Path, api_url: str, language: str):
    """Test 1: Basic streaming with real-time display"""

    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"Test 1: Basic Streaming (Real-time Display)")
    print(f"{'='*60}{Colors.NC}\n")

    segments = []
    start_time = time.time()

    try:
        for i, segment in enumerate(stream_transcription(audio_file, api_url, language), 1):
            segments.append(segment)

            # Display segment in real-time
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '').strip()

            print(f"{Colors.CYAN}[Segment {i:02d}]{Colors.NC} "
                  f"{Colors.YELLOW}[{format_time(start)} - {format_time(end)}]{Colors.NC}")
            print(f"  {text}")
            print()

    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.NC}")
        return None

    elapsed = time.time() - start_time

    print(f"{Colors.GREEN}✅ Streaming completed!{Colors.NC}")
    print(f"  Total segments: {len(segments)}")
    print(f"  Total time: {elapsed:.2f}s")

    return segments


def test_streaming_with_metrics(audio_file: Path, api_url: str, language: str, beam_size: int):
    """Test 2: Streaming with performance metrics"""

    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"Test 2: Streaming with Performance Metrics")
    print(f"{'='*60}{Colors.NC}\n")

    print(f"Configuration:")
    print(f"  Audio file: {audio_file.name}")
    print(f"  Language: {language}")
    print(f"  Beam size: {beam_size}")
    print()

    segments = []
    first_segment_time = None
    start_time = time.time()
    total_audio_duration = 0

    try:
        for i, segment in enumerate(stream_transcription(audio_file, api_url, language, beam_size), 1):
            if first_segment_time is None:
                first_segment_time = time.time() - start_time
                print(f"{Colors.CYAN}⏱️  Time to first segment: {first_segment_time:.2f}s{Colors.NC}\n")

            segments.append(segment)
            total_audio_duration = max(total_audio_duration, segment.get('end', 0))

            # Show progress
            print(f"  Segment {i}: {len(segment.get('text', ''))} chars", end='\r')

    except requests.exceptions.RequestException as e:
        print(f"\n{Colors.RED}❌ Error: {e}{Colors.NC}")
        return None

    elapsed = time.time() - start_time

    print(f"\n")
    print(f"{Colors.GREEN}{'='*60}")
    print(f"📊 Performance Metrics")
    print(f"{'='*60}{Colors.NC}")
    print(f"  Total segments: {len(segments)}")
    print(f"  Audio duration: {total_audio_duration:.2f}s")
    print(f"  Processing time: {elapsed:.2f}s")
    print(f"  Real-time factor: {elapsed/total_audio_duration:.2f}x" if total_audio_duration > 0 else "  RTF: N/A")
    print(f"  Time to first segment: {first_segment_time:.2f}s" if first_segment_time else "  TTFS: N/A")
    print(f"  Throughput: {total_audio_duration/elapsed:.2f}x real-time" if elapsed > 0 else "  Throughput: N/A")

    return segments


def test_streaming_save_output(audio_file: Path, api_url: str, language: str, output_file: Path):
    """Test 3: Save streaming output to file"""

    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"Test 3: Save Streaming Output to File")
    print(f"{'='*60}{Colors.NC}\n")

    segments = []

    with open(output_file, 'w', encoding='utf-8') as f:
        try:
            for segment in stream_transcription(audio_file, api_url, language):
                segments.append(segment)
                # Write each segment as NDJSON
                f.write(json.dumps(segment, ensure_ascii=False) + '\n')
                f.flush()  # Ensure immediate write

                print(f"  Written segment {len(segments)}", end='\r')

        except requests.exceptions.RequestException as e:
            print(f"\n{Colors.RED}❌ Error: {e}{Colors.NC}")
            return None

    print(f"\n{Colors.GREEN}✅ Saved to: {output_file}{Colors.NC}")
    print(f"  Total segments: {len(segments)}")

    # Also save as readable JSON
    json_file = output_file.with_suffix('.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)

    print(f"{Colors.GREEN}✅ Saved formatted JSON to: {json_file}{Colors.NC}")

    return segments


def compare_with_non_streaming(audio_file: Path, base_url: str, language: str):
    """Test 4: Compare streaming vs non-streaming performance"""

    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"Test 4: Streaming vs Non-Streaming Comparison")
    print(f"{'='*60}{Colors.NC}\n")

    # Test streaming
    print(f"{Colors.CYAN}Testing streaming endpoint...{Colors.NC}")
    stream_url = f"{base_url}/transcribe/stream/"
    stream_start = time.time()
    stream_segments = list(stream_transcription(audio_file, stream_url, language))
    stream_time = time.time() - stream_start

    # Test non-streaming
    print(f"{Colors.CYAN}Testing non-streaming endpoint...{Colors.NC}")
    regular_url = f"{base_url}/transcribe/"

    with open(audio_file, 'rb') as f:
        files = {'file': (audio_file.name, f, 'audio/wav')}
        data = {'language': language}

        regular_start = time.time()
        response = requests.post(regular_url, files=files, data=data)
        regular_time = time.time() - regular_start

        if response.status_code == 200:
            result = response.json()
            regular_segments = result.get('segments', [])
        else:
            print(f"{Colors.RED}❌ Non-streaming request failed: {response.status_code}{Colors.NC}")
            return

    # Compare results
    print(f"\n{Colors.GREEN}{'='*60}")
    print(f"📊 Comparison Results")
    print(f"{'='*60}{Colors.NC}")
    print(f"Streaming:")
    print(f"  Time: {stream_time:.2f}s")
    print(f"  Segments: {len(stream_segments)}")
    print()
    print(f"Non-streaming:")
    print(f"  Time: {regular_time:.2f}s")
    print(f"  Segments: {len(regular_segments)}")
    print()
    print(f"Difference:")
    print(f"  Time delta: {abs(stream_time - regular_time):.2f}s")
    print(f"  Faster by: {abs(regular_time - stream_time) / regular_time * 100:.1f}%"
          if regular_time > stream_time else f"  Slower by: {abs(stream_time - regular_time) / stream_time * 100:.1f}%")


def main():
    parser = argparse.ArgumentParser(
        description='Test Whisper streaming transcription endpoint',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('audio_file', type=Path, help='Path to audio file')
    parser.add_argument('-u', '--url', default='http://services.aiopt.io:16000',
                        help='Base URL of the API')
    parser.add_argument('-l', '--language', default='fa',
                        help='Language code (fa, en, ar, etc.)')
    parser.add_argument('-b', '--beam-size', type=int, default=5,
                        help='Beam size for decoding')
    parser.add_argument('-o', '--output', type=Path,
                        help='Output file for streaming results (NDJSON format)')
    parser.add_argument('--test', choices=['all', 'basic', 'metrics', 'save', 'compare'],
                        default='all', help='Which test to run')

    args = parser.parse_args()

    # Check if audio file exists
    if not args.audio_file.exists():
        print(f"{Colors.RED}❌ Error: Audio file not found: {args.audio_file}{Colors.NC}")
        sys.exit(1)

    # Print header
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print(f"🎙️  Whisper Streaming Transcription Test")
    print(f"{'='*60}{Colors.NC}")
    print(f"\nConfiguration:")
    print(f"  Audio file: {args.audio_file}")
    print(f"  API URL: {args.url}")
    print(f"  Language: {args.language}")
    print(f"  Beam size: {args.beam_size}")

    stream_url = f"{args.url}/transcribe/stream/"

    # Run tests
    try:
        if args.test in ['all', 'basic']:
            test_streaming_basic(args.audio_file, stream_url, args.language)

        if args.test in ['all', 'metrics']:
            test_streaming_with_metrics(args.audio_file, stream_url, args.language, args.beam_size)

        if args.test in ['all', 'save']:
            output_file = args.output or Path(f"streaming_output_{int(time.time())}.ndjson")
            test_streaming_save_output(args.audio_file, stream_url, args.language, output_file)

        if args.test in ['all', 'compare']:
            compare_with_non_streaming(args.audio_file, args.url, args.language)

        print(f"\n{Colors.GREEN}{'='*60}")
        print(f"✅ All tests completed successfully!")
        print(f"{'='*60}{Colors.NC}\n")

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Tests interrupted by user{Colors.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error: {e}{Colors.NC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
