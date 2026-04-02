#!/usr/bin/env python3
"""
Create macOS Application Icon for Python Project Generator
Generates a high-resolution icon with a generator-themed design
"""

from PIL import Image, ImageDraw, ImageFont
import os


def create_icon():
    """Create a modern icon for Python Project Generator"""

    # Create high-resolution image for icon (1024x1024 for macOS)
    size = 1024
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background with rounded corners and gradient effect
    margin = 80
    bg_rect = [margin, margin, size - margin, size - margin]

    # Draw rounded rectangle background
    corner_radius = 120
    draw.rounded_rectangle(bg_rect, corner_radius,
                           fill=(45, 55, 72, 255))  # Dark blue-gray

    # Add subtle border
    border_margin = margin - 10
    border_rect = [
        border_margin, border_margin, size - border_margin,
        size - border_margin
    ]
    draw.rounded_rectangle(border_rect,
                           corner_radius + 10,
                           outline=(200, 200, 200, 100),
                           width=8)

    # Draw stylized cog and boxes to represent a generator
    center = (size // 2, size // 2 + 40)
    cog_radius_outer = 260
    cog_radius_inner = 190

    # Cog teeth
    for i in range(12):
        angle = i * (360 / 12)
        # Simple rectangles for teeth
        tooth_width = 36
        tooth_height = 70
        # Approximate rotated rectangles by drawing rounded rectangles offset around the circle
        import math
        rad = math.radians(angle)
        tx = center[0] + int((cog_radius_outer + 10) * math.cos(rad)) - tooth_width // 2
        ty = center[1] + int((cog_radius_outer + 10) * math.sin(rad)) - tooth_height // 2
        draw.rounded_rectangle([tx, ty, tx + tooth_width, ty + tooth_height], 12, fill=(80, 90, 110, 255))

    # Cog body
    draw.ellipse(
        [center[0] - cog_radius_outer, center[1] - cog_radius_outer,
         center[0] + cog_radius_outer, center[1] + cog_radius_outer],
        fill=(95, 105, 125, 255)
    )
    draw.ellipse(
        [center[0] - cog_radius_inner, center[1] - cog_radius_inner,
         center[0] + cog_radius_inner, center[1] + cog_radius_inner],
        fill=(45, 55, 72, 255)
    )

    # Small boxes to suggest files/templates
    box_size = 88
    offsets = [(-220, -60), (140, -120), (-40, 120)]
    box_colors = [(30, 144, 255, 255), (255, 205, 0, 255), (76, 175, 80, 255)]  # blue/yellow/green
    for (dx, dy), color in zip(offsets, box_colors):
        x0 = center[0] + dx
        y0 = center[1] + dy
        draw.rounded_rectangle([x0, y0, x0 + box_size, y0 + box_size], 16, fill=(255, 255, 255, 255))
        draw.rounded_rectangle([x0, y0, x0 + box_size, y0 + 28], 16, fill=color)

    # Add title text at the top
    try:
        # Try to use a nice font
        font_size = 80
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",
                                  font_size)
    except Exception:
        # Fallback to default font (do not catch SystemExit / KeyboardInterrupt)
        font = ImageFont.load_default()

    title = "PPG"
    title_bbox = draw.textbbox((0, 0), title, font=font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (size - title_width) // 2
    title_y = 180

    # Draw title with shadow
    draw.text((title_x + 3, title_y + 3),
              title,
              font=font,
              fill=(0, 0, 0, 100))
    draw.text((title_x, title_y), title, font=font, fill=(255, 255, 255, 255))

    return img


def create_icon_set():
    """Create a complete icon set for macOS"""

    base_icon = create_icon()

    # Icon sizes for macOS
    sizes = [16, 32, 64, 128, 256, 512, 1024]

    # Create icons directory
    if not os.path.exists("icons"):
        os.makedirs("icons")

    for size in sizes:
        # Resize image with high quality
        resized = base_icon.resize((size, size), Image.Resampling.LANCZOS)

        # Save as PNG
        filename = f"icons/ppg_icon_{size}x{size}.png"
        resized.save(filename, "PNG")
        print(f"Created {filename}")

    # Save the main icon
    base_icon.save("icons/ppg_icon.png", "PNG")
    print("Created icons/ppg_icon.png")

    # Create ICO file for cross-platform compatibility
    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128),
                 (256, 256)]
    ico_images = []

    for size in ico_sizes:
        resized = base_icon.resize(size, Image.Resampling.LANCZOS)
        ico_images.append(resized)

    # Save as ICO
    ico_images[0].save("icons/ppg_icon.ico", format="ICO", sizes=ico_sizes)
    print("Created icons/ppg_icon.ico")

    print("\nIcon set created successfully!")
    print("For macOS app bundle, use the PNG files.")
    print("For cross-platform compatibility, use the ICO file.")


if __name__ == "__main__":
    create_icon_set()
