import pandas as pd, random, os, sys, json, urllib.request, zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ──────────────────────────── CONFIG ────────────────────────────
CSV_FILE           = "multilingual_data.csv"
OUT_DIR            = Path("data")
IMAGE_SIZE         = 128
IMAGES_PER_CHAR    = 5        # ⬅  change to 1, 5, 100 … whatever you like
FONTS = {
    "latin":      "NotoSans-Regular.ttf",
    "arabic":     "NotoNaskhArabic-Regular.ttf",
    "devanagari": "NotoSansDevanagari-Regular.ttf",
}
# Optional: multiple fonts per script (add extra TTFs to each list)
# FONTS["latin"] = ["NotoSans-Regular.ttf", "LiberationSans-Regular.ttf", …]

# ───────────────────── helper: download Noto if missing ─────────────────────
def ensure_font(path: str, url: str):
    if Path(path).exists():
        return path
    print(f"Downloading {path} …")
    urllib.request.urlretrieve(url, path)
    return path

URLS = {
    "NotoSans-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf",
    "NotoNaskhArabic-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoNaskhArabic/NotoNaskhArabic-Regular.ttf",
    "NotoSansDevanagari-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf",
}

for font in FONTS.values():
    # handle list vs str
    if isinstance(font, str):
        font_paths = [font]
    else:
        font_paths = font
    for p in font_paths:
        ensure_font(p, URLS.get(p, ""))

# ───────────────────────── load CSV & validate ───────────────────────────────
df = pd.read_csv(CSV_FILE, dtype=str)

def check_row(row):
    return int(row.Unicode, 16) == ord(row.Character)
bad = df[~df.apply(check_row, axis=1)]
if not bad.empty:
    print("Unicode ↔ glyph mismatch:\n", bad)
    sys.exit(1)

# ───────────────────────── font helpers ──────────────────────────────────────
def pick_font(char):
    cp = ord(char)
    if   0x0600 <= cp <= 0x06FF:
        pool = FONTS["arabic"]
    elif 0x0900 <= cp <= 0x097F or cp == 0x0950:
        pool = FONTS["devanagari"]
    else:
        pool = FONTS["latin"]
    if isinstance(pool, str):
        pool = [pool]
    return ImageFont.truetype(random.choice(pool), IMAGE_SIZE-28)

def render(char, font):
    img  = Image.new("L", (IMAGE_SIZE, IMAGE_SIZE), 255)
    draw = ImageDraw.Draw(img)
    w, h = draw.textbbox((0, 0), char, font=font)[2:]
    x, y = (IMAGE_SIZE-w)//2, (IMAGE_SIZE-h)//2 - 8
    draw.text((x, y), char, font=font, fill=0)
    return img

# ───────────────────────── generate images ───────────────────────────────────
OUT_DIR.mkdir(exist_ok=True)
rows_out = []

for r in df.itertuples(index=False):
    for idx in range(IMAGES_PER_CHAR):
        file_name = f"{r.Unicode}_{idx:03d}.png"
        img = render(r.Character, pick_font(r.Character))
        img.save(OUT_DIR / file_name)
        rows_out.append({
            "file_name": file_name,
            "caption":   r.caption
        })

# ───────────────────────── save CSV + JSONL ─────────────────────────────────
pd.DataFrame(rows_out).to_csv(OUT_DIR / "char_dataset.csv", index=False)
with open(OUT_DIR / "metadata.jsonl", "w", encoding="utf-8") as fh:
    for rec in rows_out:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

print(f"✅  {len(rows_out)} images written to {OUT_DIR}")