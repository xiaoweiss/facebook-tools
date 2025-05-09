import customtkinter as ctk
from core import TaskType, AppConfig, validate_adspower
from fb_billing_operations import (
    process_account,
    get_active_session,
    connect_browser,
    get_business_accounts,
    process_business_accounts,
    open_new_tab,
    click_create_button,
    select_sales_objective
)
import threading
from datetime import datetime, timedelta
import schedule
import time
import re
from tkinter import messagebox
import sys
from pathlib import Path
from components.path_selector import PathSelector
import queue
import traceback

ctk.set_appearance_mode("System")
# 添加Windows深色模式支持
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
    if ctk.get_appearance_mode() == "Dark":
        windll.uxtheme.SetWindowTheme(0, "DarkMode_Explorer", None)
except:
    pass

class BillingApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 初始化日志队列
        self.log_queue = queue.Queue()
        self.after(100, self._process_log_queue)
        
        self.title("Facebook广告管理工具")
        self.geometry("800x600")
        self.running = False
        self.scheduler_thread = None
        self.adspower_path = None
        
        self._show_auth_dialog()
        self._create_path_selector()
        self._create_widgets()
        self._setup_validation()
        self._bind_events()

        # 新增定时配置存储
        self.schedule_config = {
            'interval': '立即执行',
            'start_time': '00:00',
            'days': '每天'
        }

    def _show_auth_dialog(self):
        """显示授权码输入对话框"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("授权验证")
        dialog.geometry("400x200")
        dialog.transient(self)  # 设为模态对话框
        dialog.grab_set()

        # 授权码输入
        auth_label = ctk.CTkLabel(dialog, text="请输入授权码:")
        auth_label.pack(pady=10)

        self.auth_entry = ctk.CTkEntry(dialog, width=200)
        self.auth_entry.pack(pady=5)

        # 验证按钮
        verify_btn = ctk.CTkButton(
            dialog, 
            text="验证", 
            command=lambda: self._check_auth(dialog)
        )
        verify_btn.pack(pady=15)

    def _check_auth(self, dialog):
        """验证授权码"""
        auth_code = self.auth_entry.get().strip()
        if auth_code == "2024ADMIN":  # 示例授权码
            dialog.destroy()
            self.deiconify()  # 显示主窗口
        else:
            ctk.CTkLabel(dialog, text="❌ 授权码错误，请重试！", text_color="red").pack()
            self.auth_entry.delete(0, "end")

    def _create_widgets(self):
        # 主容器
        main_frame = ctk.CTkFrame(self, corner_radius=15)
        main_frame.pack(pady=5, padx=20, fill="both", expand=True)
        
        # 使用标签页布局
        self.tab_view = ctk.CTkTabview(main_frame)
        self.tab_view.add("任务配置")
        self.tab_view.add("执行日志")
        self.tab_view.pack(pady=10, padx=10, fill="both", expand=True)
        
        # 任务配置标签页
        config_tab = self.tab_view.tab("任务配置")
        self._create_config_ui(config_tab)
        
        # 日志标签页
        log_tab = self.tab_view.tab("执行日志")
        self._create_log_ui(log_tab)

    def _create_config_ui(self, parent):
        # 任务类型选择
        self.task_label = ctk.CTkLabel(parent, text="选择任务类型:", 
                                      font=("Microsoft YaHei", 12))
        self.task_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.task_combobox = ctk.CTkComboBox(parent,
                                            values=["余额监控", "创建广告"],
                                            font=("Microsoft YaHei", 12),
                                            dropdown_font=("Microsoft YaHei", 11),
                                            corner_radius=10)
        self.task_combobox.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # 账户输入
        self.accounts_label = ctk.CTkLabel(parent, text="输入账户(每行一个):",
                                         font=("Microsoft YaHei", 12))
        self.accounts_label.grid(row=1, column=0, padx=10, pady=10, sticky="nw")
        
        self.accounts_text = ctk.CTkTextbox(parent, width=300, height=150,
                                          font=("Microsoft YaHei", 11),
                                          border_width=1,
                                          corner_radius=10)
        self.accounts_text.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        # 定时设置
        self.time_frame = ctk.CTkFrame(parent, corner_radius=10)
        self.time_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=20, sticky="ew")
        
        # 时间选择器
        self.time_switch = ctk.CTkSwitch(
            self.time_frame, 
            text="启用定时执行",
            command=self.toggle_time_selection
        )
        self.time_switch.grid(row=0, column=0, columnspan=2, pady=5)

        # 时间间隔设置
        self.interval_label = ctk.CTkLabel(self.time_frame, text="执行间隔:")
        self.interval_combobox = ctk.CTkComboBox(
            self.time_frame,
            values=["立即执行", "每小时", "每4小时", "每天", "每周"],
            state="disabled",
            command=self._update_schedule_config
        )
        self.interval_label.grid(row=1, column=0, padx=5, sticky="e")
        self.interval_combobox.grid(row=1, column=1, padx=5, sticky="w")

        # 开始时间选择
        self.start_label = ctk.CTkLabel(self.time_frame, text="首次执行时间:")
        self.start_time = ctk.CTkEntry(
            self.time_frame,
            placeholder_text="HH:MM",
            state="disabled",
            textvariable=ctk.StringVar(value="00:00")
        )
        self.start_label.grid(row=2, column=0, padx=5, sticky="e")
        self.start_time.grid(row=2, column=1, padx=5, sticky="w")

        # 日期选择
        self.date_label = ctk.CTkLabel(self.time_frame, text="执行日期:")
        self.date_picker = ctk.CTkOptionMenu(
            self.time_frame,
            values=["每天", "周一至周五", "周末"],
            state="disabled",
            command=self._update_schedule_config
        )
        self.date_label.grid(row=3, column=0, padx=5, sticky="e")
        self.date_picker.grid(row=3, column=1, padx=5, sticky="w")

        # 控制按钮
        self.start_btn = ctk.CTkButton(parent, text="开始执行", 
                                     command=self.toggle_execution,
                                     font=("Microsoft YaHei", 12),
                                     corner_radius=20,
                                     fg_color="#4CAF50",
                                     hover_color="#45a049")
        self.start_btn.grid(row=3, column=0, columnspan=2, pady=10, sticky="ew")

        # 添加滚动条到账户输入框
        self.accounts_text.configure(scrollbar_button_color="#4B4B4B")
        
        # 配置网格布局权重
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(1, weight=1)

    def _create_log_ui(self, parent):
        # 日志输出
        self.log_text = ctk.CTkTextbox(parent)
        self.log_text.pack(pady=10, padx=10, fill="both", expand=True)
        self.log_text.configure(
            font=("Consolas", 10),
            wrap="word",
            scrollbar_button_color="#4B4B4B",
            fg_color="#1E1E1E",  # 更深的背景
            text_color="#FFFFFF"  # 强制白色文字
        )

    def toggle_execution(self):
        if self.running:
            self.stop_execution()
        else:
            self.start_execution()
        # 添加状态同步延迟
        time.sleep(0.1)
        self.update()

    def start_execution(self):
        """启动任务执行"""
        self.running = True  # 先设置运行状态
        if not self.adspower_path:
            self.running = False
            messagebox.showerror("错误", "请先验证AdsPower路径")
            return

        accounts = [acc.strip() for acc in self.accounts_text.get("1.0", "end-1c").split('\n') if acc.strip()]
        
        if not accounts:
            self.running = False
            self.log("⚠️ 未输入有效账户")
            return

        # 立即执行或定时执行
        if self.schedule_config['interval'] == "立即执行":
            threading.Thread(
                target=self.execute_task,
                args=(self.task_combobox.get(), accounts),
                daemon=True,
                name="TaskThread"
            ).start()
            self.log(f"🧵 启动任务线程: {threading.current_thread().name} | 状态: {self.running}")
        else:
            self._setup_scheduler()

        self.start_btn.configure(text="停止执行", fg_color="#f44336", hover_color="#d32f2f")

    def _setup_scheduler(self):
        """配置定时任务"""
        # 解析时间参数
        hour, minute = map(int, self.schedule_config['start_time'].split(':'))
        
        # 根据间隔设置调度
        interval_map = {
            "每小时": lambda: schedule.every().hour.at(f":{minute:02d}"),
            "每4小时": lambda: schedule.every(4).hours.at(f":{minute:02d}"),
            "每天": lambda: schedule.every().day.at(f"{hour:02d}:{minute:02d}"),
            "每周": lambda: schedule.every().monday.at(f"{hour:02d}:{minute:02d}")
        }
        
        if self.schedule_config['interval'] in interval_map:
            interval_map[self.schedule_config['interval']]().do(self._run_scheduled_task)

        # 启动定时器线程
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.start()

    def _run_scheduler(self):
        """运行调度循环"""
        while self.running:
            schedule.run_pending()
            time.sleep(1)
        
    def _run_scheduled_task(self):
        """执行定时任务"""
        if not self.running:
            return
        task_type = self.task_combobox.get()
        accounts = self.accounts_text.get("1.0", "end-1c").split('\n')
        self.execute_task(task_type, accounts)

    def execute_task(self, task_type, accounts):
        """执行任务核心逻辑"""
        self.log("🔍 开始执行任务...")
        self.log(f"🔧 当前运行状态: {self.running}")
        for account in accounts:
            try:
                self.log(f"🔄 开始处理账户: {account}")
                session_data = get_active_session(account)
                self.log(f"📡 API响应数据: {session_data}")  # 显示在GUI日志
                self.log(f"🔗 连接浏览器会话: {session_data['ws']['selenium']}")
                driver = connect_browser(session_data)
                
                # 根据任务类型执行操作
                if task_type == "余额监控":
                    self.log("📊 执行余额监控操作")
                    accounts = get_business_accounts(driver)
                    process_business_accounts(driver, accounts)
                elif task_type == "创建广告":
                    self.log("🛠️ 执行创建广告操作")
                    open_new_tab(driver)
                    click_create_button(driver)
                    select_sales_objective(driver)
                
                driver.quit()
                self.log(f"✅ 账户 {account} 处理完成")
            except Exception as e:
                error_msg = f"🔥 处理账户 {account} 失败: {str(e)}"
                self.log(error_msg)
                self.log(f"📄 详细堆栈: {traceback.format_exc()}")
                continue

    def log(self, message):
        """线程安全的日志记录"""
        self.log_queue.put(message)

    def toggle_time_selection(self):
        """切换时间选择组件状态"""
        state = "normal" if self.time_switch.get() else "disabled"
        self.interval_combobox.configure(state=state)
        self.start_time.configure(state=state)
        self.date_picker.configure(state=state)
        
    def _setup_validation(self):
        """设置输入验证"""
        # 时间格式验证 (HH:MM)
        vcmd = (self.register(self._validate_time), '%P')
        self.start_time.configure(validate="key", validatecommand=vcmd)
        
    def _validate_time(self, text):
        """验证时间输入格式"""
        if text == "":
            return True
        return re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', text) is not None
        
    def _bind_events(self):
        """绑定事件"""
        self.start_time.bind("<FocusOut>", self._format_time_input)
        
    def _format_time_input(self, event):
        """格式化时间输入"""
        text = self.start_time.get()
        if len(text) == 4 and ':' not in text:
            self.start_time.delete(0, "end")
            self.start_time.insert(0, f"{text[:2]}:{text[2:]}")

    def stop_execution(self):
        self.running = False
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            schedule.clear()
        self.start_btn.configure(text="开始执行", fg_color="#4CAF50", hover_color="#45a049")
        self.log("⏹️ 任务已强制停止")
        self.update_idletasks()  # 强制刷新界面

    def _update_schedule_config(self, choice):
        """更新定时配置"""
        self.schedule_config.update({
            'interval': self.interval_combobox.get(),
            'start_time': self.start_time.get(),
            'days': self.date_picker.get()
        })

    def _create_path_selector(self):
        """创建路径选择区域"""
        path_frame = ctk.CTkFrame(self)
        path_frame.pack(pady=10, padx=20, fill="x")
        
        self.path_selector = PathSelector(path_frame)
        self.path_selector.pack(pady=5, padx=5)
        
        # 验证按钮
        validate_btn = ctk.CTkButton(
            path_frame,
            text="验证路径",
            command=self._validate_path
        )
        validate_btn.pack(pady=5)
        
    def _validate_path(self):
        """验证用户选择的路径"""
        path = self.path_selector.path
        if not path:
            messagebox.showerror("错误", "请先选择安装路径")
            return
        
        # 获取安装目录路径
        install_dir = Path(path).parent if path.lower().endswith('.exe') else Path(path)
        
        if (install_dir / "ads.exe").exists():
            self.adspower_path = str(install_dir)
            AppConfig.adspower_path = path
            messagebox.showinfo("验证成功", f"已选择主程序: {Path(path).name}")
        else:
            messagebox.showerror("无效路径", "请选择正确的AdsPower安装目录")

    def _process_log_queue(self):
        """处理日志队列"""
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self._safe_log(msg)
        self.after(100, self._process_log_queue)

    def _safe_log(self, message):
        """线程安全的日志记录"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")

    def is_thread_alive(self):
        """检测任务线程是否存活"""
        for thread in threading.enumerate():
            if thread.name == "TaskThread":
                return thread.is_alive()
        return False

if __name__ == "__main__":
    app = BillingApp()
    app.withdraw()  # 初始隐藏主窗口
    app.mainloop() 