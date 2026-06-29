import customtkinter as ctk
import time

class BannerWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.0)
        self.attributes("-transparentcolor", "black") # Set transparent key color
        
        # Determine screen size (primary monitor)
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        
        self.frame = ctk.CTkFrame(self, corner_radius=10, bg_color="black") # Set frame bg to match transparent key
        self.frame.pack(fill="both", expand=True, padx=0, pady=0) # Remove padding that caused the border
        
        self.label = ctk.CTkLabel(self.frame, text="", font=("Segoe UI", 24, "bold"))
        self.label.pack(expand=True, padx=20, pady=10)
        
        self.withdraw() # Hide initially
        
        self._is_animating = False
        self._target_text_color = ""
        self._target_bg_color = ""
        self._start_time = 0
        self._duration = 0

    def show_message(self, message, bg_color, text_color, font_size, font_family="Segoe UI", position="top", duration=5, offset_x=0, offset_y=0, manual_width=0, manual_height=0):
        self._is_animating = False # Cancel previous
        
        # On Windows, transparent color keying only works if the window background is that color.
        # CTkToplevel background is usually managed by system.
        # We need to set the root window background to black (our key) too.
        self.configure(fg_color="black")
        
        self._target_text_color = text_color
        self._target_bg_color = bg_color
        self._duration = duration
        
        self.label.configure(text=message, text_color=text_color, font=(font_family, font_size, "bold"))
        self.frame.configure(fg_color=bg_color)
        
        self.update_idletasks()
        
        req_width = self.label.winfo_reqwidth() + 60
        req_height = self.label.winfo_reqheight() + 30
        
        x_pos = (self.screen_width - req_width) // 2
        
        # Override screen size if manually set
        sw = self.screen_width
        sh = self.screen_height
        if manual_width > 0: sw = manual_width
        if manual_height > 0: sh = manual_height
        
        x_pos = (sw - req_width) // 2
        
        # Apply manual offset
        x_pos += offset_x
        
        # High-DPI Fix: Check if we need to scale the coordinates
        # On some Windows setups, overrideredirect windows need physical coordinates
        try:
            scaling = self._get_window_scaling()
            if scaling > 1.0:
                 x_pos = int(x_pos * scaling)
                 # Note: y_pos is usually fine relative to screen edge, but if top=50 looks small, we can scale it too
                 # But sticking to x_pos fix for centering primarily.
        except:
            pass

        if position == "top":
            y_pos = 50 + offset_y
        else:
            y_pos = sh - req_height - 100 + offset_y
            
        self.geometry(f"{req_width}x{req_height}+{x_pos}+{y_pos}")
        self.deiconify()
        
        self._is_animating = True
        self._fade_in(0)

    def _fade_in(self, step):
        if not self._is_animating: return
        
        alpha = step / 10.0
        self.attributes('-alpha', alpha)
        
        if step < 10:
            self.after(30, lambda: self._fade_in(step + 1))
        else:
            self._start_time = time.time()
            self._flash_loop(True)

    def _flash_loop(self, visible):
        if not self._is_animating: return
        
        if time.time() - self._start_time >= self._duration:
            self.label.configure(text_color=self._target_text_color) # Ensure visible before fade out
            self._fade_out(10)
            return

        # Toggle color between text color and background color (to make it invisible)
        color = self._target_text_color if visible else self._target_bg_color
        
        self.label.configure(text_color=color)
        
        # Flash rate: 500ms
        self.after(500, lambda: self._flash_loop(not visible))

    def _fade_out(self, step):
        if not self._is_animating: return
        
        alpha = step / 10.0
        self.attributes('-alpha', alpha)
        
        if step > 0:
            self.after(30, lambda: self._fade_out(step - 1))
        else:
            self.withdraw()
            self._is_animating = False

if __name__ == "__main__":
    app = ctk.CTk()
    app.withdraw()
    banner = BannerWindow(app)
    banner.show_message("5 Minutes Remaining!", "orange", "white", 24)
    app.mainloop()
