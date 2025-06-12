#!/usr/bin/env python3
"""
Quick script to generate PWA icons
Run this to create placeholder icons for PWA functionality
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Icon sizes needed
SIZES = [16, 32, 72, 96, 128, 144, 152, 180, 192, 384, 512]

# Create icons directory if it doesn't exist
icons_dir = "/mnt/c/Users/T14/Desktop/hotel_flask_app/static/icons"
os.makedirs(icons_dir, exist_ok=True)

def create_icon(size):
    # Create image with gradient background
    img = Image.new('RGB', (size, size), '#667eea')
    draw = ImageDraw.Draw(img)
    
    # Add gradient effect
    for i in range(size):
        alpha = int(255 * (i / size) * 0.3)
        color = (102 + alpha//4, 126 + alpha//4, 234 + alpha//4)
        draw.line([(0, i), (size, i)], fill=color)
    
    # Add hotel icon (simplified)
    center = size // 2
    icon_size = size // 3
    
    # Draw hotel building
    building_width = icon_size
    building_height = icon_size * 2 // 3
    left = center - building_width // 2
    top = center - building_height // 2
    right = left + building_width
    bottom = top + building_height
    
    # Building outline
    draw.rectangle([left, top, right, bottom], fill='white', outline='#334155', width=max(1, size//64))
    
    # Windows
    window_size = max(2, size // 32)
    for row in range(2):
        for col in range(3):
            x = left + (col + 1) * building_width // 4 - window_size // 2
            y = top + (row + 1) * building_height // 3 - window_size // 2
            draw.rectangle([x, y, x + window_size, y + window_size], fill='#667eea')
    
    # Door
    door_width = max(4, size // 16)
    door_height = max(6, size // 12)
    door_x = center - door_width // 2
    door_y = bottom - door_height
    draw.rectangle([door_x, door_y, door_x + door_width, door_y + door_height], fill='#334155')
    
    return img

# Generate all icon sizes
for size in SIZES:
    icon = create_icon(size)
    filename = f"icon-{size}x{size}.png"
    filepath = os.path.join(icons_dir, filename)
    icon.save(filepath, 'PNG')
    print(f"Created {filename}")

print(f"\n✅ All PWA icons generated in {icons_dir}")
print("Icons created for sizes:", SIZES)