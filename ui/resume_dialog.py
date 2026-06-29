import customtkinter as ctk

class ResumeDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_resume, on_stop):
        super().__init__(parent)
        self.on_resume = on_resume
        self.on_stop = on_stop
        
        self.title("演示已结束")
        self.geometry("350x200")
        self.resizable(False, False)
        self.attributes('-topmost', True)
        
        # Center
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = int((screen_width - width) / 2)
        y = int((screen_height - height) / 2)
        
        self.geometry(f'+{x}+{y}')
        
        ctk.CTkLabel(self, text="检测到演示提前结束。\n您的演讲完成了吗？", font=("Microsoft YaHei UI", 16)).pack(pady=30)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20)
        
        ctk.CTkButton(btn_frame, text="是的，已完成", fg_color="red", hover_color="darkred", font=("Microsoft YaHei UI", 14),
                      command=self._on_stop).pack(side="left", expand=True, padx=5)
                      
        ctk.CTkButton(btn_frame, text="没有，稍后继续", font=("Microsoft YaHei UI", 14),
                      command=self._on_resume).pack(side="right", expand=True, padx=5)
        
        self.protocol("WM_DELETE_WINDOW", self._on_stop) # Default to stop if closed

    def _on_resume(self):
        self.on_resume()
        self.destroy()

    def _on_stop(self):
        self.on_stop()
        self.destroy()
