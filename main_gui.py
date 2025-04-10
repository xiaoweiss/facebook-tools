import customtkinter as ctk
from fb_billing_operations import main_operation, TaskType
import threading
from datetime import datetime, timedelta
import schedule
import time

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class BillingApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Facebook广告管理工具")
        self.geometry("800x600")
        self._create_widgets()
        self.running = False

    def _create_widgets(self):
        # 主容器
        main_frame = ctk.CTkFrame(self, corner_radius=15)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # 任务类型选择
        self.task_label = ctk.CTkLabel(main_frame, text="选择任务类型:", 
                                     font=("Microsoft YaHei", 12))
        self.task_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.task_combobox = ctk.CTkComboBox(main_frame,
                                            values=["账户检测", "创建广告"],
                                            font=("Microsoft YaHei", 12),
                                            dropdown_font=("Microsoft YaHei", 11),
                                            corner_radius=10)
        self.task_combobox.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # 账户输入
        self.accounts_label = ctk.CTkLabel(main_frame, text="输入账户(每行一个):",
                                         font=("Microsoft YaHei", 12))
        self.accounts_label.grid(row=1, column=0, padx=10, pady=10, sticky="nw")
        
        self.accounts_text = ctk.CTkTextbox(main_frame, width=300, height=150,
                                          font=("Microsoft YaHei", 11),
                                          border_width=1,
                                          corner_radius=10)
        self.accounts_text.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        # 定时设置
        self.time_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        self.time_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=20, sticky="ew")
        
        # 开始时间
        ctk.CTkLabel(self.time_frame, text="开始时间:").grid(row=0, column=0, padx=5)
        self.start_date = ctk.CTkEntry(self.time_frame, placeholder_text="YYYY-MM-DD HH:MM")
        self.start_date.grid(row=0, column=1, padx=5)
        
        # 结束时间
        ctk.CTkLabel(self.time_frame, text="结束时间:").grid(row=0, column=2, padx=5)
        self.end_date = ctk.CTkEntry(self.time_frame, placeholder_text="YYYY-MM-DD HH:MM")
        self.end_date.grid(row=0, column=3, padx=5)

        # 控制按钮
        self.start_btn = ctk.CTkButton(main_frame, text="开始执行", 
                                     command=self.toggle_execution,
                                     font=("Microsoft YaHei", 12),
                                     corner_radius=20,
                                     fg_color="#4CAF50",
                                     hover_color="#45a049")
        self.start_btn.grid(row=3, column=0, columnspan=2, pady=20)

        # 日志输出
        self.log_label = ctk.CTkLabel(main_frame, text="执行日志:")
        self.log_label.grid(row=4, column=0, padx=10, sticky="w")
        
        self.log_text = ctk.CTkTextbox(main_frame, width=700, height=200,
                                     font=("Consolas", 10),
                                     wrap="word")
        self.log_text.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

    def toggle_execution(self):
        if not self.running:
            self.start_execution()
        else:
            self.stop_execution()

    def start_execution(self):
        self.running = True
        self.start_btn.configure(text="停止执行", fg_color="#d9534f", hover_color="#c9302c")
        
        # 获取输入参数
        task_type = TaskType.CHECK_BALANCE if self.task_combobox.get() == "账户检测" else TaskType.CREATE_AD
        accounts = self.accounts_text.get("1.0", "end-1c").splitlines()
        
        # 创建执行线程
        self.exec_thread = threading.Thread(
            target=self.run_scheduled_tasks,
            args=(task_type, accounts),
            daemon=True
        )
        self.exec_thread.start()

    def stop_execution(self):
        self.running = False
        self.start_btn.configure(text="开始执行", fg_color="#4CAF50", hover_color="#45a049")
        self.log("执行已停止")

    def run_scheduled_tasks(self, task_type, accounts):
        # 解析时间设置
        start_time = datetime.strptime(self.start_date.get(), "%Y-%m-%d %H:%M")
        end_time = datetime.strptime(self.end_date.get(), "%Y-%m-%d %H:%M")
        
        # 设置定时任务
        schedule.every().hour.do(self.execute_tasks, task_type, accounts)
        
        while self.running and datetime.now() < end_time:
            if datetime.now() >= start_time:
                schedule.run_pending()
            time.sleep(60)

    def execute_tasks(self, task_type, accounts):
        for account in accounts:
            if not self.running:
                break
            try:
                self.log(f"开始处理账户: {account}")
                # 调用原有业务逻辑
                main_operation(task_type)
                self.log(f"账户 {account} 处理完成")
            except Exception as e:
                self.log(f"处理失败: {str(e)}")

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")

if __name__ == "__main__":
    app = BillingApp()
    app.mainloop() 