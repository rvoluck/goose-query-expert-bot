#!/usr/bin/env python3
"""
Create App Icon for Goose Query Expert Slackbot
Generates a professional icon suitable for Slack apps
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_goose_icon(size=512):
    """Create a professional Goose Query Expert icon"""
    
    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Color scheme - Professional blue/teal
    bg_color = (74, 144, 226)  # Blue
    accent_color = (52, 211, 153)  # Teal/Green
    text_color = (255, 255, 255)  # White
    shadow_color = (30, 58, 138, 180)  # Dark blue with transparency
    
    # Draw circular background with gradient effect
    center = size // 2
    radius = size // 2 - 20
    
    # Draw shadow
    draw.ellipse([15, 15, size-15, size-15], fill=shadow_color)
    
    # Draw main circle
    draw.ellipse([10, 10, size-10, size-10], fill=bg_color)
    
    # Draw accent circle (smaller, centered)
    accent_radius = radius - 40
    accent_box = [
        center - accent_radius,
        center - accent_radius,
        center + accent_radius,
        center + accent_radius
    ]
    draw.ellipse(accent_box, fill=accent_color)
    
    # Draw goose/duck silhouette in the center
    # Simple geometric goose shape
    goose_scale = size / 512  # Scale for different sizes
    
    # Goose body (ellipse)
    body_w = int(120 * goose_scale)
    body_h = int(100 * goose_scale)
    body_x = center - body_w // 2
    body_y = center - body_h // 2 + int(20 * goose_scale)
    draw.ellipse([body_x, body_y, body_x + body_w, body_y + body_h], fill=text_color)
    
    # Goose head (circle)
    head_r = int(50 * goose_scale)
    head_x = center - int(30 * goose_scale)
    head_y = center - int(60 * goose_scale)
    draw.ellipse([head_x - head_r, head_y - head_r, head_x + head_r, head_y + head_r], fill=text_color)
    
    # Goose beak (triangle)
    beak_points = [
        (head_x + int(35 * goose_scale), head_y - int(10 * goose_scale)),
        (head_x + int(70 * goose_scale), head_y),
        (head_x + int(35 * goose_scale), head_y + int(10 * goose_scale))
    ]
    draw.polygon(beak_points, fill=(255, 165, 0))  # Orange beak
    
    # Goose eye (small circle)
    eye_r = int(8 * goose_scale)
    eye_x = head_x + int(15 * goose_scale)
    eye_y = head_y - int(10 * goose_scale)
    draw.ellipse([eye_x - eye_r, eye_y - eye_r, eye_x + eye_r, eye_y + eye_r], fill=(30, 30, 30))
    
    # Add data/chart symbol (representing Query Expert)
    # Small bar chart in bottom right
    chart_x = center + int(40 * goose_scale)
    chart_y = center + int(40 * goose_scale)
    bar_width = int(15 * goose_scale)
    bar_gap = int(5 * goose_scale)
    
    # Three bars of different heights
    bars = [
        (chart_x, chart_y, chart_x + bar_width, chart_y + int(30 * goose_scale)),
        (chart_x + bar_width + bar_gap, chart_y - int(10 * goose_scale), 
         chart_x + 2*bar_width + bar_gap, chart_y + int(30 * goose_scale)),
        (chart_x + 2*(bar_width + bar_gap), chart_y - int(20 * goose_scale), 
         chart_x + 3*bar_width + 2*bar_gap, chart_y + int(30 * goose_scale))
    ]
    
    for bar in bars:
        draw.rectangle(bar, fill=text_color)
    
    return img


def create_simple_icon(size=512):
    """Create a simpler, more modern icon"""
    
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Modern gradient colors
    primary = (99, 102, 241)  # Indigo
    secondary = (139, 92, 246)  # Purple
    
    # Draw rounded square background
    margin = 40
    corner_radius = 80
    
    # Draw background with rounded corners
    draw.rounded_rectangle(
        [margin, margin, size-margin, size-margin],
        radius=corner_radius,
        fill=primary
    )
    
    # Draw "G" for Goose
    try:
        # Try to use a nice font
        font_size = size // 2
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Draw "G"
    text = "G"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2 - font_size // 8
    
    draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)
    
    # Add small database/query icon
    icon_size = size // 6
    icon_x = size - margin - icon_size - 20
    icon_y = size - margin - icon_size - 20
    
    # Draw small chart bars
    bar_width = icon_size // 4
    bar_heights = [icon_size * 0.4, icon_size * 0.7, icon_size * 0.5]
    
    for i, height in enumerate(bar_heights):
        x = icon_x + i * (bar_width + 5)
        y = icon_y + icon_size - height
        draw.rectangle([x, y, x + bar_width, icon_y + icon_size], fill=(255, 255, 255, 200))
    
    return img


def create_emoji_style_icon(size=512):
    """Create an emoji-style icon"""
    
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Bright, friendly colors
    bg_color = (66, 153, 225)  # Bright blue
    
    # Draw circle background
    draw.ellipse([10, 10, size-10, size-10], fill=bg_color)
    
    # Draw goose emoji style
    center = size // 2
    
    # Simple goose face
    # Eyes
    eye_radius = size // 15
    left_eye_x = center - size // 6
    right_eye_x = center + size // 6
    eye_y = center - size // 8
    
    draw.ellipse([left_eye_x - eye_radius, eye_y - eye_radius,
                  left_eye_x + eye_radius, eye_y + eye_radius], fill=(255, 255, 255))
    draw.ellipse([right_eye_x - eye_radius, eye_y - eye_radius,
                  right_eye_x + eye_radius, eye_y + eye_radius], fill=(255, 255, 255))
    
    # Pupils
    pupil_radius = eye_radius // 2
    draw.ellipse([left_eye_x - pupil_radius, eye_y - pupil_radius,
                  left_eye_x + pupil_radius, eye_y + pupil_radius], fill=(30, 30, 30))
    draw.ellipse([right_eye_x - pupil_radius, eye_y - pupil_radius,
                  right_eye_x + pupil_radius, eye_y + pupil_radius], fill=(30, 30, 30))
    
    # Beak
    beak_points = [
        (center - size // 12, center + size // 12),
        (center + size // 12, center + size // 12),
        (center, center + size // 6)
    ]
    draw.polygon(beak_points, fill=(255, 165, 0))
    
    # Add sparkles/stars for "smart" AI
    star_size = size // 20
    stars = [
        (size // 6, size // 6),
        (size - size // 6, size // 6),
        (size // 6, size - size // 6),
        (size - size // 6, size - size // 6)
    ]
    
    for star_x, star_y in stars:
        # Draw simple star
        points = []
        for i in range(5):
            angle = i * 144 - 90  # 144 degrees between points
            import math
            x = star_x + star_size * math.cos(math.radians(angle))
            y = star_y + star_size * math.sin(math.radians(angle))
            points.append((x, y))
        draw.polygon(points, fill=(255, 255, 255, 180))
    
    return img


def main():
    """Generate all icon variations"""
    
    print("🎨 Creating Goose Query Expert App Icons...")
    print()
    
    # Create output directory
    icon_dir = "app_icons"
    os.makedirs(icon_dir, exist_ok=True)
    
    # Generate different styles
    styles = [
        ("professional", create_goose_icon, "Professional goose with chart"),
        ("modern", create_simple_icon, "Modern minimalist 'G' logo"),
        ("emoji", create_emoji_style_icon, "Friendly emoji-style goose")
    ]
    
    sizes = [512, 256, 128, 64]
    
    for style_name, create_func, description in styles:
        print(f"Creating {style_name} style: {description}")
        
        for size in sizes:
            img = create_func(size)
            filename = f"{icon_dir}/goose_icon_{style_name}_{size}x{size}.png"
            img.save(filename, "PNG")
            print(f"  ✓ Saved {filename}")
        
        print()
    
    # Create the recommended size for Slack (512x512)
    print("📱 Creating Slack-optimized icon (512x512)...")
    recommended = create_goose_icon(512)
    recommended.save(f"{icon_dir}/slack_app_icon.png", "PNG")
    print(f"  ✓ Saved {icon_dir}/slack_app_icon.png")
    
    print()
    print("✅ All icons created successfully!")
    print()
    print(f"📁 Icons saved in: {os.path.abspath(icon_dir)}/")
    print()
    print("🎯 Recommended for Slack:")
    print(f"   {icon_dir}/slack_app_icon.png")
    print()
    print("💡 To use in Slack:")
    print("   1. Go to https://api.slack.com/apps")
    print("   2. Select your app")
    print("   3. Go to 'Basic Information'")
    print("   4. Scroll to 'Display Information'")
    print("   5. Upload the icon")
    print()
    print("🎨 Try all three styles and pick your favorite!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("💡 Make sure you have Pillow installed:")
        print("   pip install Pillow")
