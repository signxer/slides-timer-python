from PIL import Image, ImageDraw

def create_icons():
    # 1. Start/Play Icon (Triangle)
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.polygon([(20, 12), (20, 52), (54, 32)], fill="white") # Adjusted for better centering
    img.save("ui/assets/icon_start.png")

    # 2. Settings/Gear Icon
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((10, 10, 54, 54), outline="white", width=5)
    draw.ellipse((24, 24, 40, 40), fill="white")
    img.save("ui/assets/icon_settings.png")

    # 3. Sound/Speaker Icon
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.polygon([(10, 24), (10, 40), (24, 40), (38, 54), (38, 10), (24, 24)], fill="white")
    draw.arc((30, 20, 50, 44), -60, 60, fill="white", width=3)
    draw.arc((36, 14, 60, 50), -60, 60, fill="white", width=3)
    img.save("ui/assets/icon_sound.png")

    # 4. Clock/Timer Icon
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 56, 56), outline="white", width=4)
    draw.line((32, 32, 32, 16), fill="white", width=3)
    draw.line((32, 32, 44, 32), fill="white", width=3)
    img.save("ui/assets/icon_clock.png")
    
    # 5. Browse/Folder Icon
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle((8, 16, 56, 48), outline="white", width=3)
    draw.polygon([(8, 16), (24, 16), (28, 10), (56, 10), (56, 16)], fill="white")
    img.save("ui/assets/icon_folder.png")

    # 6. Save/Check Icon
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Checkmark
    draw.line((10, 32, 24, 48), fill="white", width=6)
    draw.line((24, 48, 54, 16), fill="white", width=6)
    img.save("ui/assets/icon_save.png")

    # 7. Palette Icon (Appearance)
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 56, 56), outline="white", width=4)
    draw.ellipse((16, 24, 22, 30), fill="white")
    draw.ellipse((32, 16, 38, 22), fill="white")
    draw.ellipse((48, 24, 54, 30), fill="white")
    img.save("ui/assets/icon_palette.png")

    # 8. Bell Icon (Reminder)
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Bell body
    draw.arc((16, 16, 48, 48), 180, 0, fill="white", width=4) # Top arc
    draw.line((16, 32, 16, 48), fill="white", width=4) # Left
    draw.line((48, 32, 48, 48), fill="white", width=4) # Right
    draw.line((8, 48, 56, 48), fill="white", width=4) # Bottom rim
    # Clapper
    draw.ellipse((28, 48, 36, 56), fill="white")
    img.save("ui/assets/icon_bell.png")

if __name__ == "__main__":
    import os
    if not os.path.exists("ui/assets"):
        os.makedirs("ui/assets")
    create_icons()
