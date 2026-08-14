"""Record full-screen chess sessions for future detector development.

This tool only observes and saves screenshots. It never clicks, types, or
sends input to the underlying chess application.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import cv2

from chess_analyser.capture import ScreenCapture
from chess_analyser.detection import BoardDetector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record full-screen frames for Chess Analyser detector development"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=20.0,
        help="Seconds between captures (default: 20)",
    )
    parser.add_argument(
        "--initial-delay",
        type=float,
        default=5.0,
        help="Seconds to wait before the first capture (default: 5)",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=PROJECT_ROOT / "assets" / "training_sessions",
        help="Directory containing recorded sessions",
    )
    parser.add_argument(
        "--label",
        default="chesscom_green_session",
        help="Short label included in the session folder name",
    )
    parser.add_argument(
        "--no-board-detection",
        action="store_true",
        help="Save frames without running board detection metadata",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=0,
        help="Stop after this many frames; 0 means run until Ctrl+C",
    )
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be greater than zero")
    if args.initial_delay < 0:
        parser.error("--initial-delay must not be negative")
    if args.max_frames < 0:
        parser.error("--max-frames must not be negative")
    return args


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_label(label: str) -> str:
    return "".join(character if character.isalnum() or character in "-_" else "_" for character in label)


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    session_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_label(args.label)}"
    session_dir = args.output_root.expanduser() / session_name
    session_dir.mkdir(parents=True, exist_ok=False)
    metadata_path = session_dir / "metadata.jsonl"
    session_metadata = {
        "created_at": utc_timestamp(),
        "label": args.label,
        "interval_seconds": args.interval,
        "initial_delay_seconds": args.initial_delay,
        "board_detection_enabled": not args.no_board_detection,
        "notes": "Full-screen observation only; no input is sent to the chess application.",
    }
    (session_dir / "session.json").write_text(
        json.dumps(session_metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    detector = None if args.no_board_detection else BoardDetector()
    frame_count = 0
    logging.info("Recording session to %s", session_dir)
    logging.info("Waiting %.2f seconds before the first capture", args.initial_delay)
    logging.info("Capturing every %.2f seconds; press Ctrl+C to stop", args.interval)

    try:
        with ScreenCapture() as capture, metadata_path.open("a", encoding="utf-8") as metadata_file:
            monitors = [monitor.__dict__ for monitor in capture.monitors()]
            if args.initial_delay:
                time.sleep(args.initial_delay)
            while args.max_frames == 0 or frame_count < args.max_frames:
                captured_at = utc_timestamp()
                frame = capture.capture()
                frame_count += 1
                frame_name = f"frame_{frame_count:06d}.png"
                frame_path = session_dir / frame_name
                if not cv2.imwrite(str(frame_path), frame):
                    raise RuntimeError(f"Unable to save captured frame: {frame_path}")
                record = {
                    "frame": frame_name,
                    "captured_at": captured_at,
                    "width": int(frame.shape[1]),
                    "height": int(frame.shape[0]),
                    "channels": int(frame.shape[2]),
                    "monitors": monitors,
                }
                if detector is not None:
                    board = detector.detect(frame)
                    record["board"] = None if board is None else {
                        "x": board.x,
                        "y": board.y,
                        "width": board.width,
                        "height": board.height,
                        "square_size": board.square_size,
                        "confidence": board.confidence,
                        "orientation": board.orientation,
                    }
                metadata_file.write(json.dumps(record) + "\n")
                metadata_file.flush()
                logging.info("Saved %s", frame_path)
                if args.max_frames == 0 or frame_count < args.max_frames:
                    time.sleep(args.interval)
    except KeyboardInterrupt:
        logging.info("Recording stopped by user after %d frame(s)", frame_count)
    except Exception:
        logging.exception("Recording failed after %d frame(s)", frame_count)
        return 1

    logging.info("Session complete: %s", session_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
