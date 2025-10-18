#!/bin/bash
# Test script for streaming transcription endpoint
# Usage: bash test-streaming.sh [audio_file] [language] [port]

set -e

# Configuration
AUDIO_FILE="${1:-test.wav}"
LANGUAGE="${2:-fa}"
PORT="${3:-16000}"
API_URL="http://localhost:${PORT}/transcribe/stream/"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================="
echo "🎙️  Whisper Streaming Transcription Test"
echo -e "==================================================${NC}"
echo ""

# Check if audio file exists
if [ ! -f "$AUDIO_FILE" ]; then
    echo -e "${RED}❌ Error: Audio file not found: $AUDIO_FILE${NC}"
    echo ""
    echo "Usage: $0 <audio_file> [language] [port]"
    echo "Example: $0 test.wav fa 16000"
    exit 1
fi

echo -e "${GREEN}Configuration:${NC}"
echo "  Audio file: $AUDIO_FILE"
echo "  Language: $LANGUAGE"
echo "  API URL: $API_URL"
echo ""

# Get file info
FILE_SIZE=$(du -h "$AUDIO_FILE" | cut -f1)
echo -e "${BLUE}File info:${NC}"
echo "  Size: $FILE_SIZE"

# If ffprobe is available, show duration
if command -v ffprobe &> /dev/null; then
    DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO_FILE" 2>/dev/null || echo "unknown")
    echo "  Duration: ${DURATION}s"
fi

echo ""
echo -e "${YELLOW}Sending request to streaming endpoint...${NC}"
echo ""

# Record start time
START_TIME=$(date +%s.%N)

# Test 1: Simple curl with streaming output
echo -e "${BLUE}Test 1: Basic streaming (real-time display)${NC}"
echo "=========================================="

curl -X POST "$API_URL" \
    -F "file=@$AUDIO_FILE" \
    -F "language=$LANGUAGE" \
    -N 2>/dev/null | while IFS= read -r line; do
    # Parse JSON and display
    if [ -n "$line" ]; then
        echo "$line" | python3 -c "
import sys
import json
try:
    data = json.loads(sys.stdin.read())
    print(f\"[{data['start']:.2f}s - {data['end']:.2f}s] {data['text']}\")
except:
    print(sys.stdin.read())
" 2>/dev/null || echo "$line"
    fi
done

# Record end time
END_TIME=$(date +%s.%N)
ELAPSED=$(echo "$END_TIME - $START_TIME" | bc 2>/dev/null || echo "N/A")

echo ""
echo -e "${GREEN}✅ Streaming completed!${NC}"
echo "  Total time: ${ELAPSED}s"
echo ""

# Test 2: Save raw JSON output
echo -e "${BLUE}Test 2: Saving raw NDJSON output${NC}"
echo "=========================================="

OUTPUT_FILE="streaming_output_$(date +%Y%m%d_%H%M%S).ndjson"

curl -X POST "$API_URL" \
    -F "file=@$AUDIO_FILE" \
    -F "language=$LANGUAGE" \
    -F "beam_size=5" \
    -F "vad_filter=true" \
    -N -o "$OUTPUT_FILE" 2>/dev/null

if [ -f "$OUTPUT_FILE" ]; then
    LINE_COUNT=$(wc -l < "$OUTPUT_FILE")
    echo -e "${GREEN}✅ Saved to: $OUTPUT_FILE${NC}"
    echo "  Segments: $LINE_COUNT"
    echo ""

    # Show first few segments
    echo -e "${BLUE}First 3 segments:${NC}"
    head -n 3 "$OUTPUT_FILE" | python3 -m json.tool 2>/dev/null || head -n 3 "$OUTPUT_FILE"
fi

echo ""
echo -e "${BLUE}Test 3: Parallel requests test${NC}"
echo "=========================================="

# Test concurrent streaming (if file exists)
if [ -f "$AUDIO_FILE" ]; then
    echo "Sending 3 concurrent streaming requests..."

    for i in {1..3}; do
        {
            START=$(date +%s.%N)
            RESULT=$(curl -s -X POST "$API_URL" \
                -F "file=@$AUDIO_FILE" \
                -F "language=$LANGUAGE" \
                -N 2>/dev/null | wc -l)
            END=$(date +%s.%N)
            DURATION=$(echo "$END - $START" | bc 2>/dev/null || echo "N/A")
            echo "  Request $i: $RESULT segments in ${DURATION}s"
        } &
    done

    wait
    echo -e "${GREEN}✅ All concurrent requests completed${NC}"
fi

echo ""
echo -e "${BLUE}=================================================="
echo "📊 Test Summary"
echo -e "==================================================${NC}"
echo ""
echo "All streaming tests completed successfully!"
echo ""
echo "Next steps:"
echo "  - Check output file: $OUTPUT_FILE"
echo "  - Try with different audio files"
echo "  - Test with different beam_size values (5, 10, 15)"
echo "  - Compare with non-streaming endpoint (/transcribe/)"
echo ""
