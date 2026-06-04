"""
carousel_generator.py — Premium Instagram Carousel Image Generator
Creates 5 high-quality 1080x1080 slides per news post using Pillow
Design: Dark futuristic AI aesthetic with glowing neon elements
"""
import os
import math
import random
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
# pyrefly: ignore [missing-import]
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import settings


# ── Design Tokens ─────────────────────────────────────────────────────────────
CANVAS_SIZE = (1080, 1080)

# Color Palette
BG_DARK       = (8, 8, 18)        # Deep space black
BG_MID        = (12, 12, 28)
ACCENT_BLUE   = (99, 102, 241)    # Indigo-500
ACCENT_VIOLET = (139, 92, 246)    # Violet-500
ACCENT_CYAN   = (34, 211, 238)    # Cyan-400
ACCENT_PINK   = (236, 72, 153)    # Pink-500
TEXT_WHITE    = (255, 255, 255)
TEXT_GRAY     = (180, 180, 210)
TEXT_DIM      = (100, 100, 140)
GOLD          = (251, 191, 36)

# Slide color schemes (one per slide)
SLIDE_ACCENTS = [
    (ACCENT_VIOLET, ACCENT_BLUE),   # Slide 1: violet→blue
    (ACCENT_BLUE, ACCENT_CYAN),     # Slide 2: blue→cyan
    (ACCENT_CYAN, ACCENT_BLUE),     # Slide 3: cyan→blue
    (ACCENT_VIOLET, ACCENT_PINK),   # Slide 4: violet→pink
    (GOLD, ACCENT_VIOLET),          # Slide 5: gold→violet
]


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load Inter font or fall back to default"""
    font_dir = settings.FONTS_DIR
    candidates = []
    if bold:
        candidates = [
            font_dir / "Inter-Bold.ttf",
            font_dir / "Inter-ExtraBold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/Arial Bold.ttf",
        ]
    else:
        candidates = [
            font_dir / "Inter-Regular.ttf",
            font_dir / "Inter-Medium.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]

    for path in candidates:
        try:
            return ImageFont.truetype(str(path), size)
        except Exception:
            continue

    # Absolute fallback
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def _lerp_color(c1: Tuple, c2: Tuple, t: float) -> Tuple:
    """Linear interpolate between two colors"""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _draw_gradient_bg(draw: ImageDraw.ImageDraw, img: Image.Image,
                      color1: Tuple, color2: Tuple):
    """Draw a radial gradient background"""
    w, h = img.size
    # Fill base
    img.paste(BG_DARK, [0, 0, w, h])

    # Radial gradient overlay
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    cx, cy = w // 2, h // 2
    max_r = int(math.sqrt(cx**2 + cy**2))

    for r in range(max_r, 0, -4):
        t = 1 - (r / max_r)
        alpha = int(t * 80)
        c = _lerp_color(color1, color2, t * 0.6)
        od.ellipse([cx - r, cy - r, cx + r, cy + r],
                   fill=(*c, alpha))

    merged = Image.alpha_composite(img.convert("RGBA"), overlay)
    img.paste(merged.convert("RGB"))


def _draw_grid_lines(draw: ImageDraw.ImageDraw, w: int, h: int, accent: Tuple):
    """Draw subtle geometric grid lines"""
    grid_color = (*accent, 15)
    # Vertical lines
    for x in range(0, w, 90):
        draw.line([(x, 0), (x, h)], fill=(*[min(c + 10, 255) for c in accent[:3]], 12), width=1)
    # Horizontal lines
    for y in range(0, h, 90):
        draw.line([(0, y), (w, y)], fill=(*[min(c + 10, 255) for c in accent[:3]], 12), width=1)


def _draw_glow_rect(img: Image.Image, x1: int, y1: int, x2: int, y2: int,
                    color: Tuple, radius: int = 20, alpha: int = 180):
    """Draw a glowing rounded rectangle border"""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    # Glow layers (blur effect via multiple rects)
    for i in range(6, 0, -1):
        a = int(alpha * (i / 6) * 0.4)
        expand = i * 3
        od.rounded_rectangle(
            [x1 - expand, y1 - expand, x2 + expand, y2 + expand],
            radius=radius + expand,
            outline=(*color, a),
            width=2
        )

    # Main border
    od.rounded_rectangle([x1, y1, x2, y2], radius=radius,
                          outline=(*color, alpha), width=3)
    # Fill with slight transparency
    od.rounded_rectangle([x1, y1, x2, y2], radius=radius,
                          fill=(*color[:3], 18))

    merged = Image.alpha_composite(img.convert("RGBA"), overlay)
    img.paste(merged.convert("RGB"))


def _draw_dot_particles(draw: ImageDraw.ImageDraw, w: int, h: int, color: Tuple):
    """Draw scattered dot particles for depth"""
    random.seed(42)
    for _ in range(40):
        x = random.randint(0, w)
        y = random.randint(0, h)
        size = random.choice([2, 3, 4])
        alpha_val = random.randint(40, 120)
        draw.ellipse([x, y, x + size, y + size], fill=(*color, alpha_val))


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int,
               draw: ImageDraw.ImageDraw) -> List[str]:
    """Word-wrap text to fit max_width"""
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _draw_text_shadow(draw: ImageDraw.ImageDraw, text: str, pos: Tuple,
                      font: ImageFont.FreeTypeFont, fill: Tuple,
                      shadow_offset: int = 3, shadow_alpha: int = 80):
    """Draw text with shadow effect"""
    # Shadow
    sx, sy = pos[0] + shadow_offset, pos[1] + shadow_offset
    draw.text((sx, sy), text, font=font, fill=(*BG_DARK, shadow_alpha))
    # Main text
    draw.text(pos, text, font=font, fill=fill)


def _draw_slide_number(draw: ImageDraw.ImageDraw, num: int, total: int,
                       w: int, accent: Tuple):
    """Draw slide progress indicator"""
    dot_size = 8
    spacing = 20
    total_w = total * dot_size + (total - 1) * (spacing - dot_size)
    start_x = (w - total_w) // 2
    y = 50

    for i in range(total):
        x = start_x + i * spacing
        if i == num - 1:
            # Active dot
            draw.ellipse([x, y, x + dot_size, y + dot_size], fill=accent)
        else:
            draw.ellipse([x, y, x + dot_size, y + dot_size],
                         fill=(*TEXT_DIM, 120))


def _draw_brand_tag(draw: ImageDraw.ImageDraw, w: int, h: int):
    """Draw brand watermark"""
    font = _get_font(22, bold=True)
    text = "AI DAILY NEWS"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) // 2, h - 55), text, font=font, fill=(*TEXT_DIM, 160))


def generate_slide1(content: Dict, accent: Tuple, bg_accent2: Tuple) -> Image.Image:
    """Slide 1: Hook headline"""
    img = Image.new("RGB", CANVAS_SIZE, BG_DARK)
    draw = ImageDraw.Draw(img, "RGBA")

    _draw_gradient_bg(draw, img, accent, bg_accent2)
    _draw_grid_lines(draw, *CANVAS_SIZE, accent)
    _draw_dot_particles(draw, *CANVAS_SIZE, accent)

    w, h = CANVAS_SIZE
    data = content.get("slide1", {})
    headline = data.get("headline", "AI NEWS UPDATE").upper()
    subtext = data.get("subtext", "")

    # Top label chip
    label_font = _get_font(26, bold=True)
    label_text = "🔥 BREAKING AI UPDATE"
    lb = draw.textbbox((0, 0), label_text, font=label_font)
    lw = lb[2] - lb[0]
    lx = (w - lw) // 2
    draw.rounded_rectangle([lx - 20, 150, lx + lw + 20, 200],
                            radius=20, fill=(*accent, 200))
    draw.text((lx, 155), label_text, font=label_font, fill=TEXT_WHITE)

    # Main headline (large, wrapped)
    headline_font = _get_font(72, bold=True)
    small_headline_font = _get_font(56, bold=True)

    wrapped = _wrap_text(headline, headline_font, w - 100, draw)
    if len(wrapped) > 3 or any(draw.textbbox((0,0), l, font=headline_font)[2] > w-80 for l in wrapped):
        wrapped = _wrap_text(headline, small_headline_font, w - 100, draw)
        use_font = small_headline_font
    else:
        use_font = headline_font

    total_h = len(wrapped) * 90
    start_y = (h - total_h) // 2 - 30

    for i, line in enumerate(wrapped):
        lb = draw.textbbox((0, 0), line, font=use_font)
        lw = lb[2] - lb[0]
        x = (w - lw) // 2
        y = start_y + i * 90
        # Gradient text effect
        _draw_text_shadow(draw, line, (x, y), use_font, TEXT_WHITE, 4, 100)

    # Subtext / source
    if subtext:
        sub_font = _get_font(32)
        sb = draw.textbbox((0, 0), subtext, font=sub_font)
        sw = sb[2] - sb[0]
        sx = (w - sw) // 2
        draw.text((sx, start_y + total_h + 30), subtext, font=sub_font,
                  fill=(*TEXT_GRAY, 200))

    # Swipe hint
    swipe_font = _get_font(26)
    swipe_text = "Swipe to learn more →"
    sb = draw.textbbox((0, 0), swipe_text, font=swipe_font)
    sw = sb[2] - sb[0]
    draw.text(((w - sw) // 2, h - 120), swipe_text, font=swipe_font,
              fill=(*accent, 200))

    _draw_slide_number(draw, 1, 5, w, accent)
    _draw_brand_tag(draw, w, h)

    # Decorative corner accents
    draw.line([(60, 60), (160, 60)], fill=(*accent, 200), width=3)
    draw.line([(60, 60), (60, 160)], fill=(*accent, 200), width=3)
    draw.line([(w - 160, 60), (w - 60, 60)], fill=(*accent, 200), width=3)
    draw.line([(w - 60, 60), (w - 60, 160)], fill=(*accent, 200), width=3)
    draw.line([(60, h - 160), (60, h - 60)], fill=(*accent, 200), width=3)
    draw.line([(60, h - 60), (160, h - 60)], fill=(*accent, 200), width=3)
    draw.line([(w - 160, h - 60), (w - 60, h - 60)], fill=(*accent, 200), width=3)
    draw.line([(w - 60, h - 160), (w - 60, h - 60)], fill=(*accent, 200), width=3)

    return img


def generate_content_slide(content: Dict, slide_key: str,
                            slide_num: int, accent: Tuple, bg_accent2: Tuple) -> Image.Image:
    """Slides 2-4: Content slides with header and bullets"""
    img = Image.new("RGB", CANVAS_SIZE, BG_DARK)
    draw = ImageDraw.Draw(img, "RGBA")

    _draw_gradient_bg(draw, img, accent, bg_accent2)
    _draw_grid_lines(draw, *CANVAS_SIZE, accent)
    _draw_dot_particles(draw, *CANVAS_SIZE, accent)

    w, h = CANVAS_SIZE
    data = content.get(slide_key, {})
    header = data.get("header", "")
    bullets = data.get("bullets", [])

    # Header chip
    header_font = _get_font(38, bold=True)
    hb = draw.textbbox((0, 0), header, font=header_font)
    hw = hb[2] - hb[0]
    hx = (w - hw) // 2
    hy = 140

    # Chip background
    draw.rounded_rectangle([hx - 30, hy - 12, hx + hw + 30, hy + 50],
                            radius=25, fill=(*accent, 220))
    draw.text((hx, hy), header, font=header_font, fill=TEXT_WHITE)

    # Decorative line under header
    draw.line([(100, hy + 80), (w - 100, hy + 80)],
              fill=(*accent, 120), width=2)

    # Bullet points
    bullet_font = _get_font(36, bold=False)
    bullet_bold = _get_font(40, bold=True)

    bullet_icons = ["◆", "◆", "◆"]
    start_y = hy + 130
    padding_x = 100

    for i, bullet in enumerate(bullets[:3]):
        by = start_y + i * 220
        icon = bullet_icons[i]
        icon_font = _get_font(28, bold=True)

        # Card background
        _draw_glow_rect(img, padding_x - 20, by - 20,
                        w - padding_x + 20, by + 160, accent, radius=16, alpha=100)

        # Bullet icon
        draw.text((padding_x + 10, by + 10), icon, font=icon_font, fill=accent)

        # Bullet text (wrapped)
        wrapped = _wrap_text(bullet, bullet_font, w - padding_x * 2 - 80, draw)
        for j, line in enumerate(wrapped[:3]):
            draw.text((padding_x + 60, by + 10 + j * 48),
                      line, font=bullet_font, fill=TEXT_WHITE)

    _draw_slide_number(draw, slide_num, 5, w, accent)
    _draw_brand_tag(draw, w, h)

    # Corner accents
    draw.line([(60, 60), (130, 60)], fill=(*accent, 180), width=2)
    draw.line([(60, 60), (60, 130)], fill=(*accent, 180), width=2)
    draw.line([(w - 130, 60), (w - 60, 60)], fill=(*accent, 180), width=2)
    draw.line([(w - 60, 60), (w - 60, 130)], fill=(*accent, 180), width=2)

    return img


def generate_slide5(content: Dict, accent: Tuple, bg_accent2: Tuple) -> Image.Image:
    """Slide 5: Summary + CTA"""
    img = Image.new("RGB", CANVAS_SIZE, BG_DARK)
    draw = ImageDraw.Draw(img, "RGBA")

    _draw_gradient_bg(draw, img, accent, bg_accent2)
    _draw_grid_lines(draw, *CANVAS_SIZE, accent)
    _draw_dot_particles(draw, *CANVAS_SIZE, accent)

    w, h = CANVAS_SIZE
    data = content.get("slide5", {})
    header = data.get("header", "KEY TAKEAWAY")
    summary = data.get("summary", "")
    cta = data.get("cta", "Would you use this AI tool? 👇")
    engagement = data.get("engagement", "Save this for later 🚀")

    # Top header chip
    header_font = _get_font(42, bold=True)
    hb = draw.textbbox((0, 0), header, font=header_font)
    hw = hb[2] - hb[0]
    hx = (w - hw) // 2

    draw.rounded_rectangle([hx - 30, 140, hx + hw + 30, 210],
                            radius=25, fill=(*accent, 230))
    draw.text((hx, 148), header, font=header_font, fill=TEXT_WHITE)

    # Decorative divider
    draw.line([(100, 250), (w - 100, 250)], fill=(*accent, 120), width=2)

    # Summary text
    summary_font = _get_font(42, bold=True)
    summary_lines = _wrap_text(summary, summary_font, w - 140, draw)
    sy = 310
    for line in summary_lines[:4]:
        lb = draw.textbbox((0, 0), line, font=summary_font)
        lw = lb[2] - lb[0]
        draw.text(((w - lw) // 2, sy), line, font=summary_font, fill=TEXT_WHITE)
        sy += 60

    # CTA Box
    cta_font = _get_font(38, bold=True)
    cta_box_y = 620
    _draw_glow_rect(img, 80, cta_box_y, w - 80, cta_box_y + 100,
                    accent, radius=20, alpha=200)
    cb = draw.textbbox((0, 0), cta, font=cta_font)
    cw = cb[2] - cb[0]
    draw.text(((w - cw) // 2, cta_box_y + 28), cta, font=cta_font, fill=TEXT_WHITE)

    # Engagement CTA
    eng_font = _get_font(34, bold=False)
    eb = draw.textbbox((0, 0), engagement, font=eng_font)
    ew = eb[2] - eb[0]
    draw.text(((w - ew) // 2, 760), engagement, font=eng_font,
              fill=(*bg_accent2, 220))

    # Follow prompt
    follow_font = _get_font(30, bold=True)
    follow_text = "Follow for daily AI updates 🤖"
    fb = draw.textbbox((0, 0), follow_text, font=follow_font)
    fw = fb[2] - fb[0]
    draw.text(((w - fw) // 2, 850), follow_text, font=follow_font,
              fill=(*TEXT_GRAY, 200))

    _draw_slide_number(draw, 5, 5, w, accent)
    _draw_brand_tag(draw, w, h)

    # Full corner decorations
    draw.line([(60, 60), (160, 60)], fill=(*accent, 200), width=3)
    draw.line([(60, 60), (60, 160)], fill=(*accent, 200), width=3)
    draw.line([(w - 160, 60), (w - 60, 60)], fill=(*accent, 200), width=3)
    draw.line([(w - 60, 60), (w - 60, 160)], fill=(*accent, 200), width=3)
    draw.line([(60, h - 160), (60, h - 60)], fill=(*accent, 200), width=3)
    draw.line([(60, h - 60), (160, h - 60)], fill=(*accent, 200), width=3)
    draw.line([(w - 160, h - 60), (w - 60, h - 60)], fill=(*accent, 200), width=3)
    draw.line([(w - 60, h - 160), (w - 60, h - 60)], fill=(*accent, 200), width=3)

    return img


def generate_carousel(post_content: Dict, post_index: int,
                      run_date: str, log_fn=None) -> List[str]:
    """
    Generate all 5 slides for a carousel post.
    Returns list of image file paths.
    """
    def log(msg):
        print(f"[Carousel] {msg}")
        if log_fn:
            log_fn(msg)

    content = post_content.get("content", {})
    accents = SLIDE_ACCENTS[post_index % len(SLIDE_ACCENTS)]
    accent, accent2 = accents

    log(f"Generating carousel {post_index + 1} slides...")

    # Output directory for this post
    post_dir = settings.IMAGES_DIR / run_date / f"post_{post_index + 1}"
    post_dir.mkdir(parents=True, exist_ok=True)

    image_paths = []

    slides = [
        ("slide1", generate_slide1),
        ("slide2", lambda c, a, a2: generate_content_slide(c, "slide2", 2, a, a2)),
        ("slide3", lambda c, a, a2: generate_content_slide(c, "slide3", 3, a, a2)),
        ("slide4", lambda c, a, a2: generate_content_slide(c, "slide4", 4, a, a2)),
        ("slide5", generate_slide5),
    ]

    for i, (name, generator) in enumerate(slides):
        try:
            img = generator(content, accent, accent2)
            path = post_dir / f"slide_{i + 1}.png"
            img.save(str(path), "PNG", quality=95)
            log(f"  ✓ Slide {i + 1}/5 generated locally")

            # Upload to Cloudinary
            # pyrefly: ignore [missing-import]
            from storage import upload_to_cloudinary
            cloudinary_url = upload_to_cloudinary(str(path), folder=f"antigravity/{run_date}/post_{post_index + 1}")
            image_paths.append(cloudinary_url)
            log(f"  ✓ Slide {i + 1}/5 uploaded to Cloudinary: {cloudinary_url}")

        except Exception as e:
            log(f"  ✗ Slide {i + 1} failed: {e}")
            import traceback
            traceback.print_exc()

    log(f"Carousel complete: {len(image_paths)} slides generated and uploaded")
    return image_paths


def generate_all_carousels(posts: List[Dict], run_date: str, log_fn=None) -> List[List[str]]:
    """Generate carousels for all 5 posts"""
    all_paths = []
    for i, post in enumerate(posts):
        paths = generate_carousel(post, i, run_date, log_fn=log_fn)
        all_paths.append(paths)
    return all_paths
