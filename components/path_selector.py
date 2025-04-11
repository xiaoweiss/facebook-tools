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
            title="选择AdsPower主程序（任意名称的.exe文件）",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
        )
        if path:
            self.entry.delete(0, "end")
            self.entry.insert(0, path)
            self.entry.configure(placeholder_text=Path(path).name)  # 显示文件名
    
    @property
    def path(self):
        return self.entry.get().strip()

def is_valid_adspower(path):
    """增强版路径验证"""
    exe_path = Path(path)
    
    # 基础验证
    if not (exe_path.exists() and exe_path.suffix.lower() == '.exe'):
        return False
    
    # 验证常见特征
    try:
        # 检查文件版本信息
        import win32api
        info = win32api.GetFileVersionInfo(str(exe_path), '\\')
        if 'CompanyName' in info:
            return 'adspower' in info['CompanyName'].lower()
    except:
        pass
    
    # 验证目录结构
    parent_dir = exe_path.parent
    required_files = {'config', 'data', 'profiles'}
    return any(folder.name.lower() in required_files for folder in parent_dir.iterdir()) 