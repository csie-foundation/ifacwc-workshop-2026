"""
Export all 9 speaker posters as animated WebP + APNG.
Base poster captured at 2x via Chrome, Lanczos-downscaled, then
75 IFAC logo frames (4cs each) composited and saved in full color.
"""
import subprocess, os, sys
from PIL import Image

ROOT   = r"C:\Users\astgh\Dropbox\CSIE\Grants\Integration\Travel\Korea 2026\Workshop"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
MAGICK = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
TMP    = os.path.join(ROOT, "poster_exports", "_tmp")
OUT    = os.path.join(ROOT, "poster_exports")

# Logo position on 1080x1080: height=72px, aspect=650/300, right-pad=68, top-pad=56
LOGO_W, LOGO_H = 156, 72
LOGO_X, LOGO_Y = 856, 56

SPEAKERS = [
    "Navid_Azizan", "Lars_Lindemann", "Naira_Hovakimyan", "Astghik_Hakobyan",
    "Yongxin_Chen", "Calin_Belta", "Tigran_Bakaryan", "Gioele_Zardini", "Karl_Johansson",
]

def run(*args):
    subprocess.run(list(args), check=False)

# ── Step 1: prepare logo frames (once) ─────────────────────────────────────
print("Loading logo frames ...")
logo_frames = []
for f in range(75):
    p = os.path.join(TMP, f"logo_{f:05d}.png")
    if not os.path.exists(p):
        print(f"  logo frame {f} missing — re-extracting logo ...")
        run(MAGICK, os.path.join(ROOT, "assets", "IFAC_2026_Logo_gif.gif"),
            "-coalesce", f"-resize", f"{LOGO_W}x{LOGO_H}!",
            os.path.join(TMP, "logo_%05d.png"))
        break

for f in range(75):
    logo_frames.append(Image.open(os.path.join(TMP, f"logo_{f:05d}.png")).convert("RGBA"))
print(f"  {len(logo_frames)} logo frames loaded ({LOGO_W}x{LOGO_H})")

# ── Step 2: per-poster ──────────────────────────────────────────────────────
for i, name in enumerate(SPEAKERS, start=1):
    label = f"{i:02d}"
    webp_path = os.path.join(OUT, f"poster-{label}-{name}.webp")
    apng_path = os.path.join(OUT, f"poster-{label}-{name}.apng")
    if os.path.exists(webp_path) and os.path.exists(apng_path):
        print(f"[{label}] {name} already done, skipping.")
        continue
    print(f"\n[{label}] {name}")

    base_path = os.path.join(TMP, f"base_{i}.png")

    # 2a. Capture 2x if base not cached
    if not os.path.exists(base_path):
        print("  Capturing 2x via Chrome ...")
        png2x = os.path.join(TMP, f"base2x_{i}.png")
        run(CHROME,
            "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--window-size=1080,1080", "--force-device-scale-factor=2",
            f"--screenshot={png2x}",
            f"http://localhost:3001/posters.html?id={i}&nologin=1")
        print("  Lanczos downscale 2160→1080 ...")
        run(MAGICK, png2x, "-filter", "Lanczos", "-resize", "1080x1080!", base_path)
        os.remove(png2x)

    print("  Loading base poster ...")
    base = Image.open(base_path).convert("RGBA")

    # 2b. Composite logo onto each frame
    print(f"  Building {len(logo_frames)} composite frames ...")
    composited = []
    for logo_frame in logo_frames:
        frame = base.copy()
        frame.paste(logo_frame, (LOGO_X, LOGO_Y), logo_frame)
        composited.append(frame)

    # 2c. Save animated WebP (full color, lossy Q=92)
    print("  Saving animated WebP ...")
    composited[0].save(
        webp_path, save_all=True, append_images=composited[1:],
        loop=0, duration=40, lossless=False, quality=92, method=6
    )
    webp_kb = os.path.getsize(webp_path) // 1024

    # 2d. Save APNG (lossless, full color — LinkedIn fallback)
    print("  Saving APNG ...")
    composited[0].save(
        apng_path, save_all=True, append_images=composited[1:],
        loop=0, duration=40
    )
    apng_kb = os.path.getsize(apng_path) // 1024

    print(f"  -> .webp {webp_kb} KB   .apng {apng_kb} KB")

print("\nAll done.")
