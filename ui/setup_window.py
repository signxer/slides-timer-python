import customtkinter as ctk
from PIL import Image
from config import cfg
from tkinter import filedialog

class SetupWindow(ctk.CTkToplevel):
    def __init__(self, parent, on_start_callback, on_settings_callback):
        super().__init__(parent)
        self.on_start = on_start_callback
        self.on_settings = on_settings_callback
        
        self.title("设置演讲倒计时")
        self.geometry("400x320")
        self.resizable(False, False)
        self.attributes('-topmost', True)
        
        # Load Icon
        try:
            img = Image.open("ui/assets/icon_start.png")
            self.icon_start = ctk.CTkImage(light_image=img, dark_image=img, size=(24, 24))
        except:
            self.icon_start = None

        # Center on screen
        self.update_idletasks()
        
        # High-DPI Fix: scaling factor
        try:
            scaling = self._get_window_scaling()
        except:
            scaling = 1.0

        width = self.winfo_width()
        height = self.winfo_height()
        
        # Calculate center relative to screen size
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Manual override from config
        manual_w = cfg.get("screen_width")
        manual_h = cfg.get("screen_height")
        if manual_w and int(manual_w) > 0: screen_width = int(manual_w)
        if manual_h and int(manual_h) > 0: screen_height = int(manual_h)
        
        x = int((screen_width - width) / 2)
        y = int((screen_height - height) / 2)
        
        # Apply scaling to position if needed (High-DPI fix)
        if scaling > 1.0:
            x = int(x * scaling)
            y = int(y * scaling)
        
        # Sometimes tkinter needs explicit +x+y
        self.geometry(f'+{x}+{y}')

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(main_frame, text="演讲时长 (分钟)", font=("Microsoft YaHei UI", 16)).pack(pady=(20, 10))

        # Time Input Frame
        input_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        input_frame.pack(pady=10)
        
        ctk.CTkButton(input_frame, text="-", width=40, font=("Microsoft YaHei UI", 20),
                      command=lambda: self._adjust_time(-1)).pack(side="left", padx=5)

        self.time_entry = ctk.CTkEntry(input_frame, width=120, font=("Microsoft YaHei UI", 28), justify="center")
        self.time_entry.insert(0, "10")
        self.time_entry.pack(side="left", padx=5)
        
        ctk.CTkButton(input_frame, text="+", width=40, font=("Microsoft YaHei UI", 20),
                      command=lambda: self._adjust_time(1)).pack(side="left", padx=5)
        
        # Quick select buttons
        quick_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        quick_frame.pack(pady=10)
        
        for m in [5, 10, 15, 20]:
            ctk.CTkButton(quick_frame, text=f"{m}分钟", width=60, font=("Microsoft YaHei UI", 12),
                          command=lambda t=m: self._set_time(t)).pack(side="left", padx=5)

        action_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        action_frame.pack(pady=20, fill="x", padx=20)
        
        ctk.CTkButton(action_frame, text="开始计时", image=self.icon_start, compound="left",
                      width=200, height=50, font=("Microsoft YaHei UI", 20, "bold"),
                      command=self._on_start_click).pack(expand=True)
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _adjust_time(self, delta):
        try:
            current = int(self.time_entry.get())
            new_val = max(1, current + delta)
            self._set_time(new_val)
        except ValueError:
            self._set_time(10)

    def _set_time(self, minutes):
        self.time_entry.delete(0, "end")
        self.time_entry.insert(0, str(minutes))

    def _on_start_click(self):
        try:
            minutes = float(self.time_entry.get())
            self.on_start(minutes)
            self.destroy()
        except ValueError:
            # Shake or error? Just ignore for now
            pass

    def _on_close(self):
        # If closed without starting, we just destroy. Main logic handles the rest (no timer).
        self.destroy()
