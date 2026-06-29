import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import threading

class SystemTray:
    def __init__(self, on_settings, on_exit):
        self.on_settings = on_settings
        self.on_exit = on_exit
        self.icon = None
        self._thread = None

    def create_image(self):
        # Generate a simple icon: a clock-like symbol
        width = 64
        height = 64
        bg_color = (0, 0, 0, 0) # Transparent if possible, but Windows tray usually needs solid or handled carefully. 
        # Let's use white background for simplicity or a colored circle.
        
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # Draw a blue circle
        dc.ellipse((4, 4, 60, 60), fill="#1f538d", outline="#1f538d")
        
        # Draw clock hands (white)
        dc.line((32, 32, 32, 12), fill="white", width=4) # Hour hand
        dc.line((32, 32, 48, 32), fill="white", width=4) # Minute hand
        
        return image

    def run(self):
        image = self.create_image()
        menu = (
            item('设置', self.on_settings_clicked),
            item('退出', self.on_exit_clicked)
        )
        self.icon = pystray.Icon("slides_timer", image, "演讲计时助手", menu)
        
        # Run in a separate thread so it doesn't block tkinter
        self._thread = threading.Thread(target=self.icon.run, daemon=True)
        self._thread.start()

    def on_settings_clicked(self, icon, item):
        self.on_settings()

    def on_exit_clicked(self, icon, item):
        self.icon.stop()
        self.on_exit()
        
    def stop(self):
        if self.icon:
            self.icon.stop()
