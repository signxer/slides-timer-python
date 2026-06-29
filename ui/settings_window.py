from PIL import Image
import customtkinter as ctk
from tkinter import colorchooser, font, filedialog

from ui.banner import BannerWindow
from ui.ppt_manager_window import PPTManagerWindow

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, config_manager):
        super().__init__(parent)
        self.cfg = config_manager
        
        # Load Icons
        self.icons = {}
        for name in ["start", "settings", "sound", "clock", "folder", "save", "palette", "bell"]:
            try:
                img = Image.open(f"ui/assets/icon_{name}.png")
                self.icons[name] = ctk.CTkImage(light_image=img, dark_image=img, size=(20, 20))
            except Exception as e:
                print(f"Failed to load icon {name}: {e}")
                self.icons[name] = None

        self.preview_banner = BannerWindow(self) # For previewing
        self.title("设置")
        self.geometry("700x500") # Wider for tabs
        self.attributes('-topmost', True)
        
        # Center on screen
        self.update_idletasks()
        
        # High-DPI Fix
        try:
            scaling = self._get_window_scaling()
        except:
            scaling = 1.0
            
        width = 700
        height = 500
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Manual override from config
        manual_w = self.cfg.get("screen_width")
        manual_h = self.cfg.get("screen_height")
        if manual_w and int(manual_w) > 0: screen_width = int(manual_w)
        if manual_h and int(manual_h) > 0: screen_height = int(manual_h)
        
        x = int((screen_width - width) / 2)
        y = int((screen_height - height) / 2)
        
        # Apply scaling to position if needed (High-DPI fix)
        if scaling > 1.0:
            x = int(x * scaling)
            y = int(y * scaling)
        
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # Main Layout: TabView
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_reminder = self.tab_view.add("提醒设置")
        self.tab_appearance = self.tab_view.add("外观与位置")
        self.tab_ppt = self.tab_view.add("PPT文件管理")
        
        # === Tab 1: Reminder Settings ===
        self.scroll_rem = ctk.CTkScrollableFrame(self.tab_reminder)
        self.scroll_rem.pack(fill="both", expand=True)
        
        self._add_section(self.scroll_rem, "提醒设置 (第一阶段)", "bell")
        self._add_entry(self.scroll_rem, "剩余提示语", "text_warning")
        self._add_entry(self.scroll_rem, "提示持续时间(秒)", "duration_warning")
        self._add_trigger_option(self.scroll_rem, "触发条件", "warning_trigger_type", "warning_trigger_value")
        self._add_sound_option(self.scroll_rem, "播放声音", "sound_warning_enabled", "sound_warning_path")
        
        self._add_section(self.scroll_rem, "提醒设置 (时间耗尽)", "bell")
        self._add_entry(self.scroll_rem, "提示语", "text_critical")
        self._add_entry(self.scroll_rem, "提示持续时间(秒)", "duration_critical")
        self._add_sound_option(self.scroll_rem, "播放声音", "sound_critical_enabled", "sound_critical_path")
        
        # === Tab 2: Appearance & Position ===
        self.scroll_app = ctk.CTkScrollableFrame(self.tab_appearance)
        self.scroll_app.pack(fill="both", expand=True)
        
        self._add_section(self.scroll_app, "位置偏移 (像素)", "settings")
        self._add_entry(self.scroll_app, "水平偏移 (X)", "offset_x")
        self._add_entry(self.scroll_app, "垂直偏移 (Y)", "offset_y")
        
        self._add_section(self.scroll_app, "屏幕分辨率 (0为自动识别)", "settings")
        self._add_entry(self.scroll_app, "屏幕宽度", "screen_width")
        self._add_entry(self.scroll_app, "屏幕高度", "screen_height")
        ctk.CTkLabel(self.scroll_app, text=f"当前自动识别: {self.winfo_screenwidth()} x {self.winfo_screenheight()}", 
                     font=("Microsoft YaHei UI", 10), text_color="gray").pack(anchor="w", pady=(0, 10))
        
        self._add_section(self.scroll_app, "外观", "palette")
        self._add_entry(self.scroll_app, "字体大小", "font_size")
        self._add_font_selector(self.scroll_app, "字体名称", "font_family")
        
        self._add_color_picker(self.scroll_app, "文字颜色", "text_color")
        self._add_color_picker(self.scroll_app, "剩余1/3警告背景色", "bg_color_warning")
        self._add_color_picker(self.scroll_app, "时间耗尽背景色", "bg_color_critical")
        
        self._add_section(self.scroll_app, "位置", "settings")
        # Map config value to display value
        pos_map = {"top": "顶部", "bottom": "底部"}
        current_pos = self.cfg.get("position")
        display_pos = pos_map.get(current_pos, "顶部")
        
        self.pos_var = ctk.StringVar(value=display_pos)
        ctk.CTkSegmentedButton(self.scroll_app, values=["顶部", "底部"], variable=self.pos_var).pack(pady=5)
        
        # === Tab 3: PPT File Management ===
        self.scroll_ppt = ctk.CTkScrollableFrame(self.tab_ppt)
        self.scroll_ppt.pack(fill="both", expand=True)
        
        self._add_section(self.scroll_ppt, "PPT文件时间管理", "clock")
        ctk.CTkLabel(self.scroll_ppt, text="管理PPT文件的预设时间，播放时会自动加载对应时间。", 
                     font=("Microsoft YaHei UI", 12)).pack(anchor="w", pady=(0, 20))
        
        ctk.CTkButton(self.scroll_ppt, text="打开PPT文件管理", image=self.icons.get("folder"), compound="left",
                      font=("Microsoft YaHei UI", 14), command=self.open_ppt_manager).pack(pady=10)
        
        # Bottom Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkButton(btn_frame, text="预览效果", image=self.icons.get("start"), compound="left",
                      font=("Microsoft YaHei UI", 14), fg_color="gray", command=self.preview).pack(side="left", padx=5, expand=True)
        ctk.CTkButton(btn_frame, text="保存并关闭", image=self.icons.get("save"), compound="left",
                      font=("Microsoft YaHei UI", 14), command=self.save).pack(side="left", padx=5, expand=True)

    def preview(self):
        # Temporarily apply settings for preview
        try:
            msg = self.entry_text_warning.get()
            bg = self.btn_bg_color_warning.cget("text")
            fg = self.btn_text_color.cget("text")
            fs = int(self.entry_font_size.get())
            ff = self.combo_font_family.get()
            pos = "top" if self.pos_var.get() == "顶部" else "bottom"
            off_x = int(self.entry_offset_x.get())
            off_y = int(self.entry_offset_y.get())
            
            # Manual screen size override if set
            sw = int(self.entry_screen_width.get())
            sh = int(self.entry_screen_height.get())
            
            self.preview_banner.show_message(
                message=msg,
                bg_color=bg,
                text_color=fg,
                font_size=fs,
                font_family=ff,
                position=pos,
                duration=3,
                offset_x=off_x,
                offset_y=off_y,
                manual_width=sw,
                manual_height=sh
            )
        except ValueError:
            pass

    def _add_trigger_option(self, parent, label, type_key, value_key):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(frame, text=label, font=("Microsoft YaHei UI", 12)).pack(side="left")
        
        # Trigger type combo
        type_var = ctk.StringVar(value="百分比(%)" if self.cfg.get(type_key) == "percent" else "剩余时间(分钟)")
        combo = ctk.CTkComboBox(frame, values=["百分比(%)", "剩余时间(分钟)"], variable=type_var, 
                                font=("Microsoft YaHei UI", 12), width=120)
        combo.pack(side="left", padx=10)
        setattr(self, f"combo_{type_key}", combo)
        
        # Value entry
        entry = ctk.CTkEntry(frame, width=60, font=("Microsoft YaHei UI", 12))
        entry.insert(0, str(self.cfg.get(value_key)))
        entry.pack(side="left")
        setattr(self, f"entry_{value_key}", entry)

    def _add_sound_option(self, parent, label, enable_key, path_key):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 10))
        
        # Checkbox
        var = ctk.BooleanVar(value=self.cfg.get(enable_key))
        cb = ctk.CTkCheckBox(frame, text=label, variable=var, font=("Microsoft YaHei UI", 12))
        cb.pack(side="left")
        setattr(self, f"cb_{enable_key}", var)
        
        # Path entry and browse button
        path_frame = ctk.CTkFrame(parent, fg_color="transparent")
        path_frame.pack(fill="x", pady=(0, 10))
        
        entry = ctk.CTkEntry(path_frame, font=("Microsoft YaHei UI", 12))
        entry.insert(0, str(self.cfg.get(path_key)))
        entry.pack(side="left", fill="x", expand=True, padx=(20, 5))
        setattr(self, f"entry_{path_key}", entry)
        
        btn = ctk.CTkButton(path_frame, text="", image=self.icons.get("folder"), width=30, height=30,
                            command=lambda: self._browse_file(entry))
        btn.pack(side="right")

    def _browse_file(self, entry_widget):
        filename = filedialog.askopenfilename(filetypes=[("Sound Files", "*.wav;*.mp3")])
        if filename:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, filename)

    def _add_section(self, parent, text, icon_name=None):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(20, 5))
        
        if icon_name and self.icons.get(icon_name):
            ctk.CTkLabel(frame, text="", image=self.icons.get(icon_name)).pack(side="left", padx=(0, 5))
        
        ctk.CTkLabel(frame, text=text, font=("Microsoft YaHei UI", 16, "bold"), anchor="w").pack(side="left")

    def _add_entry(self, parent, label, key):
        ctk.CTkLabel(parent, text=label, font=("Microsoft YaHei UI", 12)).pack(anchor="w")
        entry = ctk.CTkEntry(parent, font=("Microsoft YaHei UI", 12))
        entry.insert(0, str(self.cfg.get(key)))
        entry.pack(fill="x", pady=(0, 10))
        setattr(self, f"entry_{key}", entry)

    def _add_font_selector(self, parent, label, key):
        ctk.CTkLabel(parent, text=label, font=("Microsoft YaHei UI", 12)).pack(anchor="w")
        
        # Get installed fonts
        fonts = list(font.families())
        fonts.sort()
        
        current_font = self.cfg.get(key)
        if current_font not in fonts:
            fonts.insert(0, current_font)
            
        combo = ctk.CTkComboBox(parent, values=fonts, font=("Microsoft YaHei UI", 12))
        combo.set(current_font)
        combo.pack(fill="x", pady=(0, 10))
        setattr(self, f"combo_{key}", combo)

    def _add_color_picker(self, parent, label, key):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(frame, text=label, font=("Microsoft YaHei UI", 12)).pack(side="left")
        
        current_color = self.cfg.get(key)
        btn = ctk.CTkButton(frame, text=current_color, width=100, fg_color=current_color, font=("Microsoft YaHei UI", 12),
                            command=lambda k=key: self._pick_color(k))
        btn.pack(side="right")
        setattr(self, f"btn_{key}", btn)

    def _pick_color(self, key):
        color = colorchooser.askcolor(initialcolor=self.cfg.get(key), title="选择颜色")
        if color[1]:
            btn = getattr(self, f"btn_{key}")
            btn.configure(fg_color=color[1], text=color[1])

    def open_ppt_manager(self):
        # Temporarily set settings window to not topmost
        self.attributes('-topmost', False)
        # Create PPT manager window and set it to topmost
        ppt_window = PPTManagerWindow(self)
        ppt_window.attributes('-topmost', True)
        # Force update to ensure it's displayed
        ppt_window.update()
        # Set settings window back to topmost if needed
        # self.attributes('-topmost', True)

    def save(self):
        # Save entries
        try:
            self.cfg.set("text_warning", self.entry_text_warning.get())
            self.cfg.set("duration_warning", int(self.entry_duration_warning.get()))
            
            # Save trigger settings
            trigger_type_display = self.combo_warning_trigger_type.get()
            trigger_type = "percent" if trigger_type_display == "百分比(%)" else "time_remaining"
            self.cfg.set("warning_trigger_type", trigger_type)
            self.cfg.set("warning_trigger_value", int(self.entry_warning_trigger_value.get()))
            
            self.cfg.set("sound_warning_enabled", self.cb_sound_warning_enabled.get())
            self.cfg.set("sound_warning_path", self.entry_sound_warning_path.get())
            
            self.cfg.set("text_critical", self.entry_text_critical.get())
            self.cfg.set("duration_critical", int(self.entry_duration_critical.get()))
            self.cfg.set("sound_critical_enabled", self.cb_sound_critical_enabled.get())
            self.cfg.set("sound_critical_path", self.entry_sound_critical_path.get())
            
            self.cfg.set("offset_x", int(self.entry_offset_x.get()))
            self.cfg.set("offset_y", int(self.entry_offset_y.get()))
            self.cfg.set("screen_width", int(self.entry_screen_width.get()))
            self.cfg.set("screen_height", int(self.entry_screen_height.get()))
            self.cfg.set("font_size", int(self.entry_font_size.get()))
            self.cfg.set("font_family", self.combo_font_family.get())
            
            # Map display value back to config value
            pos_display = self.pos_var.get()
            pos_value = "top" if pos_display == "顶部" else "bottom"
            self.cfg.set("position", pos_value)
            
            # Colors are updated via button text/color in _pick_color, we need to read them back
            self.cfg.set("text_color", self.btn_text_color.cget("text"))
            self.cfg.set("bg_color_warning", self.btn_bg_color_warning.cget("text"))
            self.cfg.set("bg_color_critical", self.btn_bg_color_critical.cget("text"))
            
            self.destroy()
        except ValueError:
            print("Invalid input")
