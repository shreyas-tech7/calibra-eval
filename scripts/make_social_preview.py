"""Draw docs/social-preview.png (1280 x 640) with numpy and a stdlib PNG encoder.
The numbers on it come from results/judge_calibration.json. Run: .venv/bin/python scripts/make_social_preview.py"""

import json
import struct
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
W, H = 1280, 640

FONT = {
    "A": "01110 10001 10001 11111 10001 10001 10001", "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110", "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111", "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111", "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110", "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001", "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001", "N": "10001 10001 11001 10101 10011 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110", "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101", "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110", "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110", "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010", "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100", "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110", "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111", "3": "11111 00010 00100 00010 00001 10001 01110",
    "4": "00010 00110 01010 10010 11111 00010 00010", "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110", "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110", "9": "01110 10001 10001 01111 00001 00010 01100",
    "-": "00000 00000 00000 11111 00000 00000 00000", ".": "00000 00000 00000 00000 00000 01100 01100",
    ",": "00000 00000 00000 00000 01100 00100 01000", ":": "00000 01100 01100 00000 01100 01100 00000",
    "(": "00010 00100 01000 01000 01000 00100 00010", ")": "01000 00100 00010 00010 00010 00100 01000",
    " ": "00000 00000 00000 00000 00000 00000 00000",
}

BG = (18, 24, 38)
FG = (236, 240, 247)
MUTED = (150, 162, 184)
ACCENT = (94, 190, 160)


def text(img, s: str, x: int, y: int, scale: int, color) -> None:
    for ch in s.upper():
        rows = FONT[ch].split()
        for r, bits in enumerate(rows):
            for c, b in enumerate(bits):
                if b == "1":
                    img[y + r * scale:y + (r + 1) * scale, x + c * scale:x + (c + 1) * scale] = color
        x += 6 * scale


def width(s: str, scale: int) -> int:
    return len(s) * 6 * scale - scale


def png_bytes(img: np.ndarray) -> bytes:
    h, w, _ = img.shape
    raw = b"".join(b"\x00" + img[y].tobytes() for y in range(h))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def main() -> None:
    res = json.loads((ROOT / "results" / "judge_calibration.json").read_text())
    agree = res["calibration"]["agreement"]["value"]
    kappa = res["calibration"]["kappa"]["value"]
    img = np.zeros((H, W, 3), dtype=np.uint8)
    img[:, :] = BG
    img[0:12, :] = ACCENT
    title = "CALIBRA-EVAL"
    text(img, title, (W - width(title, 14)) // 2, 150, 14, FG)
    sub = "OFFLINE EVALS THAT GRADE THEIR OWN JUDGE"
    text(img, sub, (W - width(sub, 5)) // 2, 300, 5, FG)
    line = "KAPPA, BIAS PROBES, PAIRED STATS, REPLAY"
    text(img, line, (W - width(line, 4)) // 2, 380, 4, MUTED)
    nums = f"SIMULATED JUDGE: AGREEMENT {agree:.3f}, KAPPA {kappa:.3f}"
    text(img, nums, (W - width(nums, 3)) // 2, 480, 3, ACCENT)
    (ROOT / "docs" / "social-preview.png").write_bytes(png_bytes(img))


if __name__ == "__main__":
    main()
