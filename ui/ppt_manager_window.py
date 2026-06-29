import customtkinter as ctk
from tkinter import filedialog
from config import cfg
import os

class PPTManagerWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("PPT文件时间管理")
        self.geometry("650x500")
        self.resizable(True, True)
        self.attributes('-topmost', True)

        # Center on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width - width) / 2)
        y = int((screen_height - height) / 2)
        self.geometry(f'+{x}+{y}')

        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(10, 20))
        ctk.CTkLabel(header_frame, text="PPT文件时间管理", font=("Microsoft YaHei UI", 18, "bold")).pack(side="left")
        # Add clear all button to top right
        ctk.CTkButton(header_frame, text="一键清空", width=100, fg_color="#FF5252", command=self._clear_all).pack(side="right", padx=5)

        # PPT list frame
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Listbox to display PPT files
        self.ppt_listbox = ctk.CTkScrollableFrame(list_frame)
        self.ppt_listbox.pack(fill="both", expand=True)

        # Add PPT section
        add_frame = ctk.CTkFrame(main_frame)
        add_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(add_frame, text="添加PPT文件", font=("Microsoft YaHei UI", 14)).pack(pady=(0, 10))

        file_frame = ctk.CTkFrame(add_frame, fg_color="transparent")
        file_frame.pack(fill="x", pady=5)

        self.file_path_var = ctk.StringVar()
        ctk.CTkEntry(file_frame, textvariable=self.file_path_var, width=400).pack(side="left", padx=5)
        ctk.CTkButton(file_frame, text="浏览", width=80, command=self._browse_file).pack(side="left", padx=5)

        time_frame = ctk.CTkFrame(add_frame, fg_color="transparent")
        time_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(time_frame, text="时间(分钟):", width=100).pack(side="left", padx=5)
        self.time_var = ctk.StringVar(value="10")
        ctk.CTkEntry(time_frame, textvariable=self.time_var, width=100).pack(side="left", padx=5)
        ctk.CTkButton(time_frame, text="添加", width=80, height=30, command=self._add_ppt).pack(side="left", padx=5)



        # Load PPT files
        self._load_ppt_files()

    def _browse_file(self):
        file_path = filedialog.askopenfilename(
            title="选择PPT文件",
            filetypes=[("PowerPoint文件", "*.pptx *.ppt"), ("WPS演示文件", "*.dps"), ("所有文件", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)

    def _add_ppt(self):
        file_path = self.file_path_var.get()
        try:
            time = float(self.time_var.get())
            if file_path and time > 0:
                ppt_timers = cfg.get("ppt_timers")
                ppt_timers[file_path] = time
                cfg.set("ppt_timers", ppt_timers)
                self._load_ppt_files()
                self.file_path_var.set("")
                self.time_var.set("10")
        except ValueError:
            pass

    def _edit_ppt(self):
        selected_item = self._get_selected_item()
        if selected_item:
            file_path = selected_item["path"]
            current_time = selected_item["time"]
            self._edit_ppt_by_path(file_path, current_time)

    def _edit_ppt_by_path(self, file_path, current_time=None):
        if not current_time:
            ppt_timers = cfg.get("ppt_timers")
            if file_path in ppt_timers:
                current_time = ppt_timers[file_path]
            else:
                return
        
        # Create edit dialog
        edit_dialog = ctk.CTkToplevel(self)
        edit_dialog.title("修改PPT时间")
        edit_dialog.geometry("300x150")
        edit_dialog.attributes('-topmost', True)
        
        ctk.CTkLabel(edit_dialog, text="新时间(分钟):").pack(pady=10)
        time_var = ctk.StringVar(value=str(current_time))
        ctk.CTkEntry(edit_dialog, textvariable=time_var).pack(pady=10)
        
        def save_edit():
            try:
                new_time = float(time_var.get())
                if new_time > 0:
                    ppt_timers = cfg.get("ppt_timers")
                    ppt_timers[file_path] = new_time
                    cfg.set("ppt_timers", ppt_timers)
                    self._load_ppt_files()
                    edit_dialog.destroy()
            except ValueError:
                pass
        
        button_frame = ctk.CTkFrame(edit_dialog, fg_color="transparent")
        button_frame.pack(pady=10)
        ctk.CTkButton(button_frame, text="保存", command=save_edit).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="取消", command=edit_dialog.destroy).pack(side="left", padx=10)

    def _delete_ppt(self):
        selected_item = self._get_selected_item()
        if selected_item:
            file_path = selected_item["path"]
            self._delete_ppt_by_path(file_path)

    def _delete_ppt_by_path(self, file_path):
        ppt_timers = cfg.get("ppt_timers")
        if file_path in ppt_timers:
            del ppt_timers[file_path]
            cfg.set("ppt_timers", ppt_timers)
            self._load_ppt_files()

    def _clear_all(self):
        # Confirm dialog
        confirm_dialog = ctk.CTkToplevel(self)
        confirm_dialog.title("确认清空")
        confirm_dialog.geometry("300x150")
        confirm_dialog.attributes('-topmost', True)
        
        ctk.CTkLabel(confirm_dialog, text="确定要清空所有PPT文件吗？").pack(pady=20)
        
        button_frame = ctk.CTkFrame(confirm_dialog, fg_color="transparent")
        button_frame.pack(pady=10)
        
        def do_clear():
            cfg.set("ppt_timers", {})
            self._load_ppt_files()
            confirm_dialog.destroy()
        
        ctk.CTkButton(button_frame, text="确定", command=do_clear).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="取消", command=confirm_dialog.destroy).pack(side="left", padx=10)

    def _load_ppt_files(self):
        # Clear existing items
        for widget in self.ppt_listbox.winfo_children():
            widget.destroy()
        
        ppt_timers = cfg.get("ppt_timers")
        if not ppt_timers:
            ctk.CTkLabel(self.ppt_listbox, text="暂无PPT文件", font=("Microsoft YaHei UI", 14)).pack(pady=20)
            return
        
        # Create list items
        for file_path, time in ppt_timers.items():
            file_name = os.path.basename(file_path)
            item_frame = ctk.CTkFrame(self.ppt_listbox, fg_color="transparent")
            item_frame.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(item_frame, text=file_name, width=300, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(item_frame, text=f"{time}分钟", width=100).pack(side="left", padx=5)
            
            # Add edit and delete buttons to each item
            button_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            button_frame.pack(side="right", padx=5)
            
            ctk.CTkButton(button_frame, text="修改", width=60, command=lambda path=file_path: self._edit_ppt_by_path(path)).pack(side="left", padx=2)
            ctk.CTkButton(button_frame, text="删除", width=60, fg_color="#FF5252", command=lambda path=file_path: self._delete_ppt_by_path(path)).pack(side="left", padx=2)
            
            # Store file path as attribute for easy access
            item_frame.file_path = file_path
            item_frame.time = time

    def _get_selected_item(self):
        # Get the currently focused item
        focused = self.ppt_listbox.focus_get()
        if focused and hasattr(focused, "file_path"):
            return {"path": focused.file_path, "time": focused.time}
        
        # Fallback: get the first child with file_path attribute
        for widget in self.ppt_listbox.winfo_children():
            if hasattr(widget, "file_path"):
                return {"path": widget.file_path, "time": widget.time}
        
        return None

    def _select_ppt(self, file_path):
        # This method can be used to select a PPT file and close the window
        # For now, just close the window
        self.destroy()
