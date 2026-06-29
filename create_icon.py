from PIL import Image, ImageDraw

def create_icon():
    # Create a 256x256 icon
    size = (256, 256)
    image = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Draw a blue circle background
    draw.ellipse((10, 10, 246, 246), fill="#1f538d", outline="#1f538d")

    # Draw clock face (white circle outline)
    draw.ellipse((40, 40, 216, 216), outline="white", width=8)

    # Draw hands
    # Hour hand (pointing at 3)
    draw.line((128, 128, 190, 128), fill="white", width=12)
    # Minute hand (pointing at 12)
    draw.line((128, 128, 128, 60), fill="white", width=12)

    # Center dot
    draw.ellipse((118, 118, 138, 138), fill="white")

    # Save as ICO
    image.save("icon.ico", format="ICO", sizes=[(256, 256)])
    print("icon.ico created.")

if __name__ == "__main__":
    create_icon()
