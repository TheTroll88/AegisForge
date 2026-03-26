"""
AegisForge Brand Asset Generator
Creates desktop wallpaper and GitHub profile logo using Aegis brand identity.
Brand: #00ffc8 (Aegis cyan) on dark, shield motif, NoiseAsset texture.
"""

import math
import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# === Brand constants ===
AEGIS_CYAN = (0, 255, 200)       # #00ffc8
AEGIS_DARK = (8, 10, 15)         # Near-black background
AEGIS_MID = (12, 18, 28)         # Slightly lighter dark
AEGIS_DIM = (0, 80, 64)          # Dimmed cyan for subtle elements
AEGIS_GLOW = (0, 200, 160)       # Softer glow variant

OUTPUT_DIR = Path(os.environ.get("BRAND_OUTPUT_DIR", str(Path(__file__).resolve().parent.parent / "assets" / "brand")))
NOISE_ASSET = Path(os.environ.get("NOISE_ASSET_PATH", str(Path(__file__).resolve().parent.parent / "assets" / "NoiseAsset_256x256_PNG.png")))

# Screen resolution
WALL_W, WALL_H = 1920, 1080  # Generate at 1080p regardless of current display
LOGO_SIZE = 500  # GitHub profile pic (will look good at any smaller size)


def draw_shield(draw, cx, cy, size, outline_color, fill_color=None, width=3):
    """Draw a shield shape centered at (cx, cy) with given size."""
    s = size
    # Shield vertices: pointed bottom, curved top
    top_y = cy - s * 0.5
    mid_y = cy + s * 0.1
    bot_y = cy + s * 0.6
    left_x = cx - s * 0.42
    right_x = cx + s * 0.42

    # Shield path: top-left, top-right, right-mid, bottom-point, left-mid
    points = [
        (left_x, top_y),
        (cx, top_y - s * 0.08),  # Slight top arch
        (right_x, top_y),
        (right_x, mid_y),
        (cx, bot_y),
        (left_x, mid_y),
    ]

    if fill_color:
        draw.polygon(points, fill=fill_color, outline=outline_color, width=width)
    else:
        draw.polygon(points, outline=outline_color, width=width)

    return points


def draw_hex_grid(draw, width, height, cell_size, color, opacity_range=(10, 35)):
    """Draw a subtle hexagonal grid pattern."""
    hex_h = cell_size * math.sqrt(3)
    for row in range(int(height / hex_h) + 2):
        for col in range(int(width / cell_size) + 2):
            offset_x = (cell_size * 0.75) if row % 2 else 0
            cx = col * cell_size * 1.5 + offset_x
            cy = row * hex_h * 0.5
            if 0 <= cx <= width and 0 <= cy <= height:
                opacity = random.randint(*opacity_range)
                r, g, b = color
                hex_color = (r, g, b, opacity)
                # Draw small hexagon
                hex_points = []
                for i in range(6):
                    angle = math.pi / 3 * i - math.pi / 6
                    hx = cx + (cell_size * 0.3) * math.cos(angle)
                    hy = cy + (cell_size * 0.3) * math.sin(angle)
                    hex_points.append((hx, hy))
                draw.polygon(hex_points, outline=hex_color, width=1)


def draw_scan_lines(draw, width, height, spacing=4, color=(0, 255, 200), opacity=8):
    """Draw subtle horizontal scan lines for CRT/terminal aesthetic."""
    r, g, b = color
    for y in range(0, height, spacing):
        draw.line([(0, y), (width, y)], fill=(r, g, b, opacity), width=1)


def draw_radial_glow(img, cx, cy, radius, color, max_alpha=60):
    """Draw a radial glow effect centered at (cx, cy)."""
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    r, g, b = color
    for i in range(radius, 0, -2):
        alpha = int(max_alpha * (1 - (i / radius) ** 1.5))
        if alpha > 0:
            glow_draw.ellipse(
                [cx - i, cy - i, cx + i, cy + i],
                fill=(r, g, b, alpha),
            )
    return Image.alpha_composite(img, glow)


def draw_circuit_lines(draw, width, height, num_lines=15, color=(0, 255, 200), opacity=25):
    """Draw subtle circuit-board-style lines."""
    r, g, b = color
    line_color = (r, g, b, opacity)
    for _ in range(num_lines):
        x = random.randint(0, width)
        y = random.randint(0, height)
        segments = random.randint(3, 8)
        for _ in range(segments):
            direction = random.choice(["h", "v"])
            length = random.randint(30, 150)
            if direction == "h":
                nx = x + random.choice([-1, 1]) * length
                draw.line([(x, y), (nx, y)], fill=line_color, width=1)
                x = nx
            else:
                ny = y + random.choice([-1, 1]) * length
                draw.line([(x, y), (x, ny)], fill=line_color, width=1)
                y = ny
            # Draw node dot at corner
            draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=line_color)


def generate_wallpaper():
    """Generate Aegis-branded desktop wallpaper."""
    print("Generating wallpaper...")
    img = Image.new("RGBA", (WALL_W, WALL_H), AEGIS_DARK + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    # Layer 1: Subtle gradient from center
    img = draw_radial_glow(img, WALL_W // 2, WALL_H // 2, 700, AEGIS_DIM, max_alpha=30)
    draw = ImageDraw.Draw(img, "RGBA")

    # Layer 2: Hex grid background
    draw_hex_grid(draw, WALL_W, WALL_H, cell_size=80, color=AEGIS_CYAN, opacity_range=(8, 22))

    # Layer 3: Circuit lines
    draw_circuit_lines(draw, WALL_W, WALL_H, num_lines=20, color=AEGIS_CYAN, opacity=18)

    # Layer 4: Scan lines
    draw_scan_lines(draw, WALL_W, WALL_H, spacing=3, color=AEGIS_CYAN, opacity=6)

    # Layer 5: NoiseAsset as subtle texture overlay
    if NOISE_ASSET.exists():
        noise = Image.open(NOISE_ASSET).convert("L")
        # Tile it across the wallpaper at reduced opacity
        noise_layer = Image.new("RGBA", (WALL_W, WALL_H), (0, 0, 0, 0))
        for y in range(0, WALL_H, noise.height):
            for x in range(0, WALL_W, noise.width):
                # Convert noise to very low alpha overlay
                tile = noise.copy()
                rgba_tile = Image.new("RGBA", tile.size, (0, 0, 0, 0))
                for py in range(tile.height):
                    for px in range(tile.width):
                        v = tile.getpixel((px, py))
                        # Very subtle - just 3-8% opacity based on noise value
                        a = int(v * 0.03)
                        rgba_tile.putpixel((px, py), (v, v, v, a))
                noise_layer.paste(rgba_tile, (x, y))
        img = Image.alpha_composite(img, noise_layer)
        draw = ImageDraw.Draw(img, "RGBA")
        print("  NoiseAsset texture applied")

    # Layer 6: Center shield
    shield_size = 280
    cx, cy = WALL_W // 2, WALL_H // 2 - 30

    # Glow behind shield
    img = draw_radial_glow(img, cx, cy + 20, 200, AEGIS_CYAN, max_alpha=25)
    draw = ImageDraw.Draw(img, "RGBA")

    # Shield - outer
    draw_shield(draw, cx, cy, shield_size, outline_color=AEGIS_CYAN + (180,), width=3)
    # Shield - inner
    draw_shield(draw, cx, cy, shield_size * 0.85, outline_color=AEGIS_CYAN + (80,), width=2)

    # Inner vertical line (sword/pillar motif)
    draw.line([(cx, cy - shield_size * 0.3), (cx, cy + shield_size * 0.45)],
              fill=AEGIS_CYAN + (120,), width=2)

    # Cross guard
    cg_y = cy - shield_size * 0.05
    draw.line([(cx - shield_size * 0.2, cg_y), (cx + shield_size * 0.2, cg_y)],
              fill=AEGIS_CYAN + (120,), width=2)

    # "A" letterform inside shield (geometric)
    a_top = cy - shield_size * 0.22
    a_bot = cy + shield_size * 0.2
    a_left = cx - shield_size * 0.15
    a_right = cx + shield_size * 0.15
    a_mid_y = cy + shield_size * 0.02
    # Left leg
    draw.line([(cx, a_top), (a_left, a_bot)], fill=AEGIS_CYAN + (140,), width=3)
    # Right leg
    draw.line([(cx, a_top), (a_right, a_bot)], fill=AEGIS_CYAN + (140,), width=3)
    # Crossbar
    draw.line([(a_left + shield_size * 0.05, a_mid_y), (a_right - shield_size * 0.05, a_mid_y)],
              fill=AEGIS_CYAN + (140,), width=2)

    # Layer 7: Text
    try:
        font_large = ImageFont.truetype("arial.ttf", 52)
        font_small = ImageFont.truetype("arial.ttf", 18)
        font_tag = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_tag = ImageFont.load_default()

    # "AEGIS" text below shield
    text_y = cy + shield_size * 0.55 + 20
    aegis_text = "A E G I S"
    bbox = draw.textbbox((0, 0), aegis_text, font=font_large)
    tw = bbox[2] - bbox[0]
    draw.text((cx - tw // 2, text_y), aegis_text, fill=AEGIS_CYAN + (220,), font=font_large)

    # Subtitle
    sub_text = "FORGE"
    bbox2 = draw.textbbox((0, 0), sub_text, font=font_small)
    tw2 = bbox2[2] - bbox2[0]
    draw.text((cx - tw2 // 2, text_y + 60), sub_text, fill=AEGIS_GLOW + (120,), font=font_small)

    # Corner tags
    draw.text((30, WALL_H - 40), "aegissignal.io", fill=AEGIS_DIM + (80,), font=font_tag)
    draw.text((WALL_W - 200, WALL_H - 40), "SYSTEM ONLINE", fill=AEGIS_DIM + (60,), font=font_tag)

    # Flatten to RGB
    final = Image.new("RGB", (WALL_W, WALL_H), AEGIS_DARK)
    final.paste(img, mask=img.split()[3])

    # Save
    wallpaper_path = OUTPUT_DIR / "aegis_wallpaper_1080p.png"
    final.save(wallpaper_path, "PNG", optimize=True)
    print(f"  Wallpaper saved: {wallpaper_path}")
    return wallpaper_path


def generate_logo():
    """Generate Aegis logo for GitHub profile picture."""
    print("Generating logo...")
    size = LOGO_SIZE
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")

    cx, cy = size // 2, size // 2 + 10
    shield_size = size * 0.75

    # Background circle with dark fill
    margin = 10
    draw.ellipse([margin, margin, size - margin, size - margin],
                 fill=AEGIS_DARK + (255,), outline=AEGIS_CYAN + (200,), width=3)

    # Subtle radial glow
    img = draw_radial_glow(img, cx, cy, int(size * 0.35), AEGIS_DIM, max_alpha=40)
    draw = ImageDraw.Draw(img, "RGBA")

    # NoiseAsset texture in circle
    if NOISE_ASSET.exists():
        noise = Image.open(NOISE_ASSET).convert("L").resize((size, size))
        mask = Image.new("L", (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse([margin + 5, margin + 5, size - margin - 5, size - margin - 5], fill=255)
        noise_rgba = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        for py in range(size):
            for px in range(size):
                v = noise.getpixel((px, py))
                m = mask.getpixel((px, py))
                if m > 0:
                    a = int(v * 0.02)
                    noise_rgba.putpixel((px, py), (v, v, v, a))
        img = Image.alpha_composite(img, noise_rgba)
        draw = ImageDraw.Draw(img, "RGBA")
        print("  NoiseAsset texture applied to logo")

    # Shield
    draw_shield(draw, cx, cy, shield_size, outline_color=AEGIS_CYAN + (220,), width=4)
    draw_shield(draw, cx, cy, shield_size * 0.82, outline_color=AEGIS_CYAN + (90,), width=2)

    # "A" letterform inside shield
    a_size = shield_size * 0.55
    a_top = cy - a_size * 0.4
    a_bot = cy + a_size * 0.35
    a_left = cx - a_size * 0.28
    a_right = cx + a_size * 0.28
    a_mid_y = cy + a_size * 0.0

    # Stylized A
    draw.line([(cx, a_top), (a_left, a_bot)], fill=AEGIS_CYAN + (200,), width=5)
    draw.line([(cx, a_top), (a_right, a_bot)], fill=AEGIS_CYAN + (200,), width=5)
    draw.line([(a_left + a_size * 0.08, a_mid_y), (a_right - a_size * 0.08, a_mid_y)],
              fill=AEGIS_CYAN + (200,), width=3)

    # Top point accent
    draw.ellipse([cx - 4, a_top - 4, cx + 4, a_top + 4], fill=AEGIS_CYAN + (255,))

    # Flatten
    logo_path = OUTPUT_DIR / "aegis_logo_500.png"
    final = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    final = Image.alpha_composite(final, img)
    final.save(logo_path, "PNG", optimize=True)

    # Also save a smaller GitHub-ready version (400x400)
    gh_logo = final.resize((400, 400), Image.Resampling.LANCZOS)
    gh_path = OUTPUT_DIR / "aegis_github_profile.png"
    gh_logo.save(gh_path, "PNG", optimize=True)

    print(f"  Logo saved: {logo_path}")
    print(f"  GitHub profile pic saved: {gh_path}")
    return logo_path, gh_path


if __name__ == "__main__":
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    wallpaper_path = generate_wallpaper()
    print()
    logo_path, gh_path = generate_logo()

    print()
    print("=== Brand assets generated ===")
    print(f"Wallpaper:      {wallpaper_path}")
    print(f"Logo (500px):   {logo_path}")
    print(f"GitHub profile: {gh_path}")
