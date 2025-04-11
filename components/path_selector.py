import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path

class PathSelector(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_columnconfigure(1, weight=1)
        
        # 路径输入框
        self.entry = ctk.CTkEntry(
            self,
            placeholder_text="请选择AdsPower安装目录",
            width=400
        )
        self.entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # 浏览按钮
        self.browse_btn = ctk.CTkButton(
            self,
            text="浏览",
            width=80,
            command=self._browse_path
        )
        self.browse_btn.grid(row=0, column=1, padx=5, pady=5)
    
    def _browse_path(self):
        """打开文件选择对话框"""
        path = filedialog.askopenfilename(
            title="选择AdsPower主程序",
            filetypes=[("可执行文件", "ads.exe"), ("所有文件", "*.*")]
        )
        if path:
            self.entry.delete(0, "end")
            self.entry.insert(0, path)
    
    @property
    def path(self):
        return self.entry.get().strip() 