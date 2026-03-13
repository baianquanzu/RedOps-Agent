#!/usr/bin/env python3
"""
RedOps Desktop Pet - 黑客少女桌宠
模仿天选姬风格的黑客动漫少女桌宠
"""

import tkinter as tk
from tkinter import ttk
import random
import threading
import time
import sys
import requests

# 桌宠状态
class DesktopPet:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("RedOps")
        self.window.geometry("180x280")
        self.window.configure(bg='#1a1a2e')
        
        # 窗口置顶
        self.window.attributes('-topmost', True)
        self.window.overrideredirect(True)
        
        # 拖拽相关
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0
        
        # 状态
        self.state = "idle"  # idle, thinking, working, happy, greeting
        self.mood = "normal"  # normal, happy, thinking, working, greeting
        self.hover_count = 0
        
        # 表情配置
        self.expressions = {
            "idle": {
                "normal": ["(◕‿◕)", "(◠‿◠)", "(｡◕‿◕｡)", "(◕ᴗ◕)"],
                "happy": ["(◕‿◕)", "ヽ(◕ᴗ◕)ﾉ", "(◕‿◕)♡"],
            },
            "thinking": {
                "normal": ["(◎_◎)", "(・・?)", "(・・)", "(?_?)"],
            },
            "working": {
                "normal": ["(ง'̀-'́)ง", "ヾ(≧▽≦)o", "(ﾉ´ヮ`)ﾉ", "(ง'̀-'́)ง"],
            },
            "greeting": {
                "normal": ["ヾ(◍'ᴗ'◍)ﾉ", "(◕‿◕)ノ", "ヾ(◕ᴗ◕)ﾉ", "(◠‿◠)ノ"],
            },
            "error": {
                "normal": ["(╥﹏╥)", "(;_;)", "(ノД`)・゜"],
            }
        }
        
        self.current_expression = self.expressions["idle"]["normal"][0]
        self.name = "Red"
        
        # 创建UI
        self.create_ui()
        
        # 启动动画循环
        self.animate()
        
        # 启动状态更新
        self.start_status_updater()
        
        # 绑定事件
        self.window.bind('<Button-1>', self.on_drag_start)
        self.window.bind('<B1-Motion>', self.on_drag_motion)
        self.window.bind('<ButtonRelease-1>', self.on_drag_end)
        self.window.bind('<Enter>', self.on_enter)
        self.window.bind('<Leave>', self.on_leave)
        self.window.bind('<Double-Button-1>', self.on_double_click)
        
        # 右键菜单
        self.window.bind('<Button-3>', self.show_context_menu)
        
        self.window.mainloop()
    
    def create_ui(self):
        # 主框架
        self.frame = tk.Frame(self.window, bg='#1a1a2e')
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 头像区域 - 使用更大的emoji
        self.avatar_label = tk.Label(
            self.frame,
            text="👩‍💻",
            font=('Segoe UI Emoji', 48),
            bg='#1a1a2e'
        )
        self.avatar_label.pack(pady=(5, 0))
        
        # 名字
        self.name_label = tk.Label(
            self.frame,
            text="Red",
            font=('Microsoft YaHei', 10, 'bold'),
            bg='#1a1a2e',
            fg='#00d97e'
        )
        self.name_label.pack(pady=(2, 0))
        
        # 状态气泡
        self.bubble_frame = tk.Frame(self.frame, bg='#2d2d44', relief=tk.RAISED, bd=1, padx=8, pady=4)
        self.bubble_frame.pack(fill=tk.X, pady=5)
        
        self.bubble_label = tk.Label(
            self.bubble_frame,
            text="你好呀！主人~",
            font=('Microsoft YaHei', 9),
            bg='#2d2d44',
            fg='#ffffff'
        )
        self.bubble_label.pack()
        
        # 互动按钮区域
        self.btn_frame = tk.Frame(self.frame, bg='#1a1a2e')
        self.btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=3)
        
        # 快捷按钮
        btn_style = {
            'font': ('Microsoft YaHei', 9),
            'bg': '#2d2d44',
            'fg': '#8b949e',
            'relief': tk.FLAT,
            'cursor': 'hand2',
            'padx': 8,
            'pady': 3
        }
        
        self.chat_btn = tk.Button(self.btn_frame, text="💬 对话", command=self.open_chat, **btn_style)
        self.chat_btn.pack(side=tk.LEFT, padx=2)
        
        self.scan_btn = tk.Button(self.btn_frame, text="🔍 扫描", command=self.quick_scan, **btn_style)
        self.scan_btn.pack(side=tk.LEFT, padx=2)
        
        self.min_btn = tk.Button(self.btn_frame, text="─", command=self.minimize_window, 
                                font=('Arial', 12), bg='#2d2d44', fg='#666', relief=tk.FLAT, width=2)
        self.min_btn.pack(side=tk.RIGHT, padx=1)
        
        self.close_btn = tk.Button(self.btn_frame, text="×", command=self.close_window, 
                                  font=('Arial', 12), bg='#2d2d44', fg='#f85149', relief=tk.FLAT, width=2)
        self.close_btn.pack(side=tk.RIGHT, padx=1)
    
    def animate(self):
        # 更新表情
        mood_expressions = self.expressions.get(self.mood, self.expressions["idle"]["normal"])
        
        if isinstance(mood_expressions, dict):
            state_expressions = mood_expressions.get(self.state, mood_expressions.get("normal", self.expressions["idle"]["normal"]))
        else:
            state_expressions = mood_expressions
        
        if isinstance(state_expressions, dict):
            state_expressions = state_expressions.get("normal", self.expressions["idle"]["normal"])
        
        self.current_expression = random.choice(state_expressions)
        
        # 根据状态更新头像
        avatar_map = {
            ("idle", "normal"): "👩‍💻",
            ("idle", "happy"): "😊",
            ("thinking", "normal"): "🤔",
            ("working", "normal"): "😎",
            ("greeting", "normal"): "👋",
            ("error", "normal"): "😢"
        }
        
        self.avatar_label.config(text=avatar_map.get((self.mood, self.state), "👩‍💻"))
        
        # 更新状态文字
        status_map = {
            ("idle", "normal"): "等待指令中...",
            ("idle", "happy"): "开心~",
            ("thinking", "normal"): "思考中...",
            ("working", "normal"): "工作中...",
            ("greeting", "normal"): "你好呀！",
            ("error", "normal"): "遇到问题了"
        }
        
        status = status_map.get((self.mood, self.state), "等待指令中...")
        self.bubble_label.config(text=status)
        
        # 状态自动恢复
        if self.mood in ["working", "thinking"]:
            self.window.after(5000, self.set_idle)
        
        # 定时更新
        self.window.after(3000, self.animate)
    
    def set_idle(self):
        """设置回空闲状态"""
        self.mood = "idle"
        self.state = "idle"
        self.bubble_label.config(text="等待指令中...")
    
    def set_mood(self, mood):
        """设置心情"""
        self.mood = mood
    
    def set_state(self, state):
        """设置状态"""
        self.state = state
    
    def show_message(self, message, duration=3):
        """显示消息"""
        self.bubble_label.config(text=message)
        if duration > 0:
            self.window.after(duration * 1000, self.set_idle)
    
    def on_enter(self, event):
        """鼠标进入"""
        self.hover_count += 1
        if self.hover_count >= 2:
            self.set_mood("happy")
            self.show_message("主人来啦~ ♡")
            self.hover_count = 0
    
    def on_leave(self, event):
        """鼠标离开"""
        pass
    
    def on_drag_start(self, event):
        """开始拖拽"""
        self.dragging = True
        self.offset_x = event.x
        self.offset_y = event.y
    
    def on_drag_motion(self, event):
        """拖拽中"""
        if self.dragging:
            x = self.window.winfo_x() + (event.x - self.offset_x)
            y = self.window.winfo_y() + (event.y - self.offset_y)
            self.window.geometry(f'+{x}+{y}')
    
    def on_drag_end(self, event):
        """结束拖拽"""
        self.dragging = False
    
    def on_double_click(self, event):
        """双击打开主界面"""
        self.open_chat()
    
    def show_context_menu(self, event):
        """右键菜单"""
        menu = tk.Menu(self.window, tearoff=0, bg='#2d2d44', fg='#cccccc', font=('Microsoft YaHei', 9))
        
        menu.add_command(label="💬 打开对话", command=self.open_chat)
        menu.add_command(label="🔍 快速扫描", command=self.quick_scan)
        menu.add_separator()
        menu.add_command(label="👋 打招呼", command=self.greeting)
        menu.add_command(label="💭 随机对话", command=self.random_chat)
        menu.add_separator()
        menu.add_command(label="❓ 使用帮助", command=self.show_help)
        menu.add_separator()
        menu.add_command(label="❌ 退出", command=self.close_window)
        
        menu.post(event.x_root, event.y_root)
    
    def open_chat(self):
        """打开对话"""
        import webbrowser
        webbrowser.open("http://localhost:8000")
        self.set_mood("happy")
        self.show_message("正在打开对话页面~")
    
    def quick_scan(self):
        """快速扫描"""
        self.set_mood("working")
        self.show_message("准备开始扫描任务！")
        try:
            # 可以触发API
            requests.get("http://localhost:8000/api/status", timeout=2)
        except:
            pass
    
    def greeting(self):
        """打招呼"""
        greetings = [
            "你好呀！主人~",
            "欢迎回来！",
            "今天也要加油哦！",
            "检测到主人上线！",
            "主人好~ (◕‿◕)"
        ]
        self.set_mood("greeting")
        self.show_message(random.choice(greetings), duration=4)
    
    def random_chat(self):
        """随机对话"""
        chats = [
            "要开始渗透测试吗？",
            "今天想测试什么呢？",
            "我可以帮你分析目标哦~",
            "让我想想有什么能帮你的",
            "主人有什么需要吗？"
        ]
        self.set_mood("idle")
        self.show_message(random.choice(chats), duration=4)
    
    def show_help(self):
        """显示帮助"""
        self.show_message("双击打开对话页面~")
    
    def minimize_window(self):
        """最小化"""
        self.window.withdraw()
    
    def close_window(self):
        """关闭窗口"""
        self.window.quit()
        sys.exit(0)
    
    def start_status_updater(self):
        """启动状态更新器"""
        def check_status():
            while True:
                try:
                    response = requests.get("http://localhost:8000/api/status", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data.get("active_scans", 0) > 0:
                            self.set_mood("working")
                            self.show_message(f"正在扫描 {data.get('active_scans')} 个目标...")
                        else:
                            if self.mood == "working":
                                self.set_idle()
                                self.show_message("扫描完成！")
                except:
                    pass
                
                time.sleep(10)
        
        thread = threading.Thread(target=check_status, daemon=True)
        thread.start()


def main():
    pet = DesktopPet()


if __name__ == "__main__":
    main()
