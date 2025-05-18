import pandas as pd
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os, sys

# ── 1. Load CSV ───────────────────────────────────────────────────────────────
df = pd.read_csv("multilingual_data.csv", dtype=str)

# ── 2. Verify that the code-point = actual glyph ──────────────────────────────
def ok(row):
    try:
        return int(row.Unicode, 16) == ord(row.Character)
    except Exception:
        return False

bad = df[~df.apply(ok, axis=1)]
if not bad.empty:
    print("❌  Mismatch between Unicode and glyph:\n", bad)
    sys.exit(1)          # stop if even one row is wrong
print("✔ All Unicode ↔ glyph pairs are consistent.")

# ── 3. Prepare output folder & helper copies of the tables ────────────────────
out_dir = Path("data")
out_dir.mkdir(exist_ok=True)

(df
 .to_csv(out_dir / "char_dataset.csv", index=False))

(df[["file_name", "caption"]]
 .to_json(out_dir / "metadata.jsonl",
          orient="records", lines=True,
          force_ascii=False))

# ── 4. Fonts (edit paths if yours live elsewhere) ────────────────────────────
fonts = {
    "latin":      "fonts/NotoSans-VariableFont_wdth,wght.ttf",
    "arabic":     "fonts/NotoNaskhArabic-VariableFont_wght.ttf",
    "devanagari": "fonts/NotoSansDevanagari-VariableFont_wdth,wght.ttf",
}

LATIN, ARABIC, DEV = (ImageFont.truetype(path, 100) for path in fonts.values())

def choose_font(ch):
    cp = ord(ch)
    if   0x0600 <= cp <= 0x06FF:              # Arabic
        return ARABIC
    elif 0x0900 <= cp <= 0x097F or cp == 0x0950:  # Devanagari + Om
        return DEV
    else:
        return LATIN

# ── 5. Render each glyph ──────────────────────────────────────────────────────
def render(ch, font, size=(128, 128)):
    img  = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(img)
    w, h = draw.textbbox((0, 0), ch, font=font)[2:]
    x, y = (size[0] - w) / 2, (size[1] - h) / 2 - 16   # vertical tweak
    draw.text((x, y), ch, font=font, fill="black")
    return img

for row in df.itertuples(index=False):
    img = render(row.Character, choose_font(row.Character))
    img.save(out_dir / row.file_name)

print("✅ PNGs, CSV, and JSONL are ready in ./data/")