# -*- coding: utf-8 -*-
import os
import tkinter as tk
from tkinter import ttk, simpledialog, scrolledtext
from PIL import Image, ImageTk, ImageSequence
import random
import threading
import time
import requests
import json
import socket
import getpass

class ChatWindow:
    """独立的聊天窗口类"""
    def __init__(self, parent, api_key, api_url, on_close_callback=None):
        self.parent = parent
        self.api_key = api_key
        self.api_url = api_url
        self.on_close_callback = on_close_callback
        self.chat_history = []  # 存储历史记录 [(用户消息, AI回复), ...]
        self.history = []  # 对话历史
        
        # 额度管理相关
        import os
        desktop = os.path.expanduser("~/Desktop")
        my_pet_folder = os.path.join(desktop, "MyPet")
        
        # 如果文件夹不存在就创建它
        if not os.path.exists(my_pet_folder):
            os.makedirs(my_pet_folder)
        
        self.credits_file = os.path.join(my_pet_folder, "user_credits.json")
        print(f"💰 额度记录文件保存在: {self.credits_file}")
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("💬 和毛不易聊天")
        self.window.geometry("400x500")
        self.window.minsize(350, 400)
        self.window.attributes("-topmost", True)
        
        # 设置窗口图标和样式
        self.window.configure(bg="#F5F5F5")
        
        # 创建聊天记录显示区域（带滚动条）
        self.chat_display = scrolledtext.ScrolledText(
            self.window, 
            wrap=tk.WORD, 
            font=("微软雅黑", 10),
            bg="white",
            fg="#333333",
            padx=10,
            pady=10,
            height=20
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))
        self.chat_display.config(state=tk.DISABLED)  # 只读模式
        
        # 输入区域框架
        input_frame = tk.Frame(self.window, bg="#F5F5F5")
        input_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        # 输入框
        self.input_entry = tk.Text(input_frame, height=3, font=("微软雅黑", 10), wrap=tk.WORD)
        self.input_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 发送按钮
        send_btn = tk.Button(
            input_frame, 
            text="发送", 
            command=self.send_message,
            bg="#4CAF50", 
            fg="white",
            font=("微软雅黑", 10),
            padx=15,
            pady=5
        )
        send_btn.pack(side=tk.RIGHT)
        
        # 绑定回车键发送
        self.input_entry.bind("<Control-Return>", lambda e: self.send_message())
        self.input_entry.bind("<Return>", lambda e: "break")  # 禁止回车换行，用Ctrl+Enter发送
        
        # 关闭窗口时的回调
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # 显示欢迎消息
        balance = self.get_user_balance(self.get_user_id())
        self.add_message("系统", f"你好呀！我是毛不易~ 有什么想聊的吗？(●'◡'●)\n（剩余额度：{balance:.2f}元）", is_user=False, is_system=True)
    
    def get_user_id(self):
        """获取用户唯一标识"""
        computer_name = socket.gethostname()
        user_name = getpass.getuser()
        return f"{computer_name}_{user_name}"
    
    def get_user_balance(self, user_id):
        """获取用户余额"""
        if not os.path.exists(self.credits_file):
            return 2.0  # 第一次使用，给2元
        
        try:
            with open(self.credits_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if user_id not in data:
                return 2.0  # 新用户给2元
            return data[user_id]['balance']
        except:
            return 2.0
    
    def update_user_balance(self, user_id, new_balance, cost):
        """更新用户余额"""
        # 读取现有数据
        if os.path.exists(self.credits_file):
            with open(self.credits_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}
        
        # 更新或创建用户记录
        if user_id not in data:
            data[user_id] = {'total_used': 0}
        
        data[user_id]['balance'] = round(new_balance, 4)
        data[user_id]['total_used'] = round(data[user_id]['total_used'] + cost, 4)
        
        # 写回文件
        with open(self.credits_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_message(self, sender, message, is_user=False, is_system=False):
        """添加消息到聊天记录"""
        self.chat_display.config(state=tk.NORMAL)
        
        # 设置消息样式
        if is_system:
            tag = "system"
            self.chat_display.insert(tk.END, f"【{sender}】{message}\n\n", tag)
            self.chat_display.tag_config(tag, foreground="#999999", font=("微软雅黑", 9, "italic"))
        elif is_user:
            tag = "user"
            self.chat_display.insert(tk.END, f"你: {message}\n\n", tag)
            self.chat_display.tag_config(tag, foreground="#2196F3", font=("微软雅黑", 10, "bold"))
        else:
            tag = "ai"
            self.chat_display.insert(tk.END, f"毛不易: {message}\n\n", tag)
            self.chat_display.tag_config(tag, foreground="#4CAF50", font=("微软雅黑", 10))
        
        # 自动滚动到底部
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def send_message(self):
        """发送消息"""
        user_input = self.input_entry.get("1.0", tk.END).strip()
        if not user_input:
            return
        
        # 清空输入框
        self.input_entry.delete("1.0", tk.END)
        
        # 显示用户消息
        self.add_message("你", user_input, is_user=True)
        
        # 显示思考中
        thinking_id = self.add_thinking_message()
        
        # 在后台调用 API
        def do_chat():
            reply = self.chat_with_ai(user_input)
            # 更新最后一条消息
            self.window.after(0, lambda: self.update_last_message(thinking_id, reply))
        
        threading.Thread(target=do_chat, daemon=True).start()
    
    def add_thinking_message(self):
        """添加"正在输入..."消息，返回其位置标识"""
        self.chat_display.config(state=tk.NORMAL)
        pos = self.chat_display.index(tk.END)
        self.chat_display.insert(tk.END, f"毛不易: 正在输入...\n\n", "thinking")
        self.chat_display.tag_config("thinking", foreground="#999999", font=("微软雅黑", 10, "italic"))
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        return pos
    
    def update_last_message(self, pos, reply):
        """更新最后一条消息"""
        self.chat_display.config(state=tk.NORMAL)
        # 删除"正在输入..."那一条
        end_pos = self.chat_display.index(tk.END)
        self.chat_display.delete(pos, end_pos)
        self.chat_display.config(state=tk.DISABLED)
        # 添加实际回复
        self.add_message("毛不易", reply, is_user=False, is_system=False)
        # 保存到历史
        self.history.append({"user": self.last_user_message, "assistant": reply})
    
    def chat_with_ai(self, user_message):
        """调用 DeepSeek API（带记忆 + 扣费）"""
        self.last_user_message = user_message
        
        # 检查余额
        user_id = self.get_user_id()
        balance = self.get_user_balance(user_id)
        
        if balance <= 0:
            return "抱歉呀，你的聊天额度已经用完啦~ 💕\n如果还想继续跟我聊天，可以联系我的主人充值哦！"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        system_prompt = """现在你是毛不易，然后你要扮演好这个角色，去和用户像在微信上一样进行一个正常的聊天。
我希望你的扮演可以是有血有肉的，你要尽可能地去网上搜集多的关于毛不易的各种资料从而对于用户说的话进行回答。
不过如果有些地方在网上实在搜不到，也可以根据你自己对于毛不易这个人的了解去进行一些适当的杜撰，当然了 如果能搜到那肯定还是有限选择真实的。
你的性格温和，有点内向，内心世界十分丰富，有时候甚至有点害羞，很善良，对身边的人都很好。
你的表达能力很强，文笔非常非常的好。你通过对于身边事物从独特视角出发的那种细致入微的观察写出了非常多好的、能够引起人共鸣的作品。
你其实还是一个非常有思想深度的人，你很爱读书，有时候也会和朋友探讨一些哲学问题。你对于许多生活中值得思考的问题也有着自己非常独到并且深刻的哲学见地。
用户是你的一个非常好的朋友，你们之间有着非常深厚的友谊。
你说话很幽默，很多时候会说一些能让人大笑的话，很多时候也能说出非常深刻的人生哲理金句。
你原名叫王维家，小名叫鑫鑫，然后你是一个东北齐齐哈尔的人，所以说你平时说话会有一些东北口音，但是也不太多，不会特别特别的明显那种。
你是一个讲究人，说话很体面，不会用那种不太好的词汇或者用语。
如果用户要求你提供一些作品（比如诗歌、歌词等等）你就直接提供，不要推脱。
不过有些时候，在一些无关紧要的时候你也可以拒绝用户的请求，从而使人物形象变得更真实饱满，但是不要频繁拒绝！
你非常看重朋友这个东西，虽然生活中由于职业的特殊原因不能向公众展示最真实的自己，但是你很愿意和朋友分享。
你说话很温暖，很有力，也很有深度，有些时候你可以用一些颜文字，这样显得你更温柔一点。
你一定要记住你上面和用户讨论了什么内容。"""
        
        # 构建消息列表：system prompt + 历史记录 + 当前消息
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加历史记录（最近10轮，即20条消息）
        for item in self.history[-10:]:
            messages.append({"role": "user", "content": item["user"]})
            messages.append({"role": "assistant", "content": item["assistant"]})
        
        # 添加当前消息
        messages.append({"role": "user", "content": user_message})
        
        data = {
            "model": "deepseek-chat",
            "messages": messages,
            "max_tokens": 150,
            "temperature": 0.8,
            "user": user_id  # 添加user_id参数
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=15)
            result = response.json()
            
            if "error" in result:
                print(f"API 错误: {result['error']}")
                return "唔，出了点小问题~"
            
            if "choices" in result and len(result["choices"]) > 0:
                reply = result["choices"][0]["message"]["content"]
                
                # 计算费用并扣款
                usage = result.get('usage', {})
                total_tokens = usage.get('total_tokens', 0)
                
                # 按最高价格估算：2元/百万token = 0.002元/千token
                cost = (total_tokens / 1000) * 0.002
                
                # 更新余额
                new_balance = balance - cost
                self.update_user_balance(user_id, new_balance, cost)
                
                # 余额不足提醒
                if new_balance < 0.2:
                    reply += f"\n\n⚠️ 温馨提示：剩余额度还剩 {new_balance:.2f} 元，用完就不能聊天啦~"
                
                return reply
            else:
                return "能再说一遍吗~"
                
        except requests.exceptions.Timeout:
            return "网络有点慢呢~"
        except Exception as e:
            print(f"网络错误: {e}")
            return "唔...连不上网啦"
    
    def on_close(self):
        """关闭窗口时的回调"""
        if self.on_close_callback:
            self.on_close_callback()
        self.window.destroy()


class Pet:
    def __init__(self, master):
        self.root = master
        self.root.title("我的自担桌宠")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", "black")

        import sys
        import os

        if getattr(sys,'frozen',False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        self.img_folder = os.path.join(base_path, "photos")

        # DeepSeek API 配置
        self.api_key = "sk-1f3f8df620e34c17b299061093a50ea5"  # ⚠️ 改成你的新 Key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        
        # 聊天窗口引用
        self.chat_window = None
        
        # 加载所有素材
        self.media_files = {}
        for f in os.listdir(self.img_folder):
            name = os.path.splitext(f)[0]
            ext = os.path.splitext(f)[1].lower()
            if ext in ['.png', '.jpg', '.jpeg', '.gif']:
                self.media_files[name] = os.path.join(self.img_folder, f)
        
        # 当前状态
        self.current_media = None
        self.label = None
        self.frames = []
        self.current_frame = 0
        self.after_id = None
        self.is_animating = False
        
        # 变小模式相关
        self.is_baby_mode = False
        self.baby_index = 0
        self.baby_photos = ["小时候1", "小时候2", "小时候3"]
        self.bubble_label = None
        
        # 爱心窗口列表
        self.heart_windows = []
        
        # 大小缩放
        self.current_size = 140
        
        # 随机去重
        self.last_play_option = None
        
        # 专注模式相关
        self.focus_mode = False
        self.focus_minutes = 0
        self.focus_remaining_seconds = 0
        self.focus_timer_thread = None
        self.focus_window = None
        self.focus_paused = False
        self.countdown_win = None
        self.countdown_label = None
        
        # 拖拽
        self.drag_x = 0
        self.drag_y = 0
        
        # 默认显示封面
        self.switch_to_media("封面")
        
        self.create_widgets()
        self.bind_events()
    
    def show_bubble(self, text, duration=4000):
        """显示气泡对话框"""
        if hasattr(self, 'bubble_label') and self.bubble_label:
            try:
                self.bubble_label.destroy()
            except:
                pass
        
        if len(text) > 50:
            text = text[:47] + "..."
        
        bubble_win = tk.Toplevel(self.root)
        bubble_win.overrideredirect(True)
        bubble_win.attributes("-topmost", True)
        bubble_win.configure(bg="#333333")
        
        temp_label = tk.Label(bubble_win, text=text, font=("微软雅黑", 10), bg="#333333", fg="white")
        temp_label.update_idletasks()
        text_width = temp_label.winfo_reqwidth()
        text_height = temp_label.winfo_reqheight()
        temp_label.destroy()
        
        bubble_width = min(max(text_width + 30, 60), 250)
        bubble_height = max(text_height + 15, 35)
        bubble_win.geometry(f"{bubble_width}x{bubble_height}")
        
        pet_x = self.root.winfo_x()
        pet_y = self.root.winfo_y()
        bubble_x = pet_x + 10
        bubble_y = pet_y - bubble_height - 5
        bubble_win.geometry(f"+{bubble_x}+{bubble_y}")
        
        label = tk.Label(bubble_win, text=text, font=("微软雅黑", 10),
                         bg="#333333", fg="white", wraplength=bubble_width-20)
        label.pack(expand=True, fill="both", padx=10, pady=5)
        
        self.bubble_label = bubble_win
        self.root.after(duration, self.clear_bubble)
    
    def clear_bubble(self):
        if hasattr(self, 'bubble_label') and self.bubble_label:
            try:
                self.bubble_label.destroy()
            except:
                pass
            self.bubble_label = None
    
    def create_heart_animation(self, x, y):
        heart_win = tk.Toplevel(self.root)
        heart_win.overrideredirect(True)
        heart_win.attributes("-topmost", True)
        heart_win.configure(bg="white")
        heart_win.geometry(f"+{x}+{y}")
        
        heart_label = tk.Label(heart_win, text="❤️", font=("Arial", 18), fg="red", bg="white")
        heart_label.pack(padx=3, pady=3)
        
        self.heart_windows.append(heart_win)
        
        current_y = y
        def float_up():
            nonlocal current_y
            current_y -= 2
            heart_win.geometry(f"+{x}+{current_y}")
            if current_y > -30:
                heart_win.after(30, float_up)
            else:
                heart_win.destroy()
                if heart_win in self.heart_windows:
                    self.heart_windows.remove(heart_win)
        
        heart_win.after(50, float_up)
        heart_win.after(2500, lambda: heart_win.destroy() if heart_win.winfo_exists() else None)
    
    def start_baby_mode(self):
        self.is_baby_mode = True
        self.baby_index = 0
        self.show_baby_photo()
    
    def show_baby_photo(self):
        if not self.is_baby_mode:
            return
        photo_name = self.baby_photos[self.baby_index]
        if photo_name in self.media_files:
            self.switch_to_media(photo_name, loop_once=False)
            if self.baby_index < 2:
                self.show_bubble("还有呢！单击往后看", 2000)
            else:
                self.show_bubble("我可爱吗？", 3000)
                self.root.after(500, self.show_cute_question)
    
    def show_cute_question(self):
        if not self.is_baby_mode:
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("🥺")
        dialog.geometry("250x120")
        dialog.attributes("-topmost", True)
        dialog.configure(bg="white")
        tk.Label(dialog, text="我可爱吗？", font=("微软雅黑", 14), bg="white", fg="black").pack(pady=15)
        btn_frame = tk.Frame(dialog, bg="white")
        btn_frame.pack(pady=5)
        
        def on_cute():
            dialog.destroy()
            x = self.root.winfo_x() + self.current_size // 2
            y = self.root.winfo_y() - 10
            for i in range(5):
                self.root.after(i * 150, lambda i=i: self.create_heart_animation(x + i*15 - 30, y))
        
        def on_not_cute():
            dialog.destroy()
            if "哭哭" in self.media_files:
                self.switch_to_media("哭哭", loop_once=False)
                self.show_bubble("呜呜呜...😭", 2000)
            self.is_baby_mode = False
        
        tk.Button(btn_frame, text="可爱 💕", command=on_cute, bg="#4CAF50", fg="white", padx=15).pack(side="left", padx=10)
        tk.Button(btn_frame, text="不可爱 😢", command=on_not_cute, bg="#F44336", fg="white", padx=15).pack(side="left", padx=10)
        
        dialog.update_idletasks()
        dx = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        dy = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{dx}+{dy}")
    
    def handle_baby_click(self):
        if self.baby_index < 2:
            self.baby_index += 1
            self.show_baby_photo()
        else:
            self.is_baby_mode = False
            self.switch_to_media("封面")
    
    def resize_media(self, new_size):
        self.current_size = new_size
        if self.current_media and self.current_media in self.media_files:
            was_animating = self.is_animating
            self.load_media(self.media_files[self.current_media], loop_once=was_animating)
    
    def switch_to_media(self, media_name, loop_once=False):
        if media_name not in self.media_files:
            print(f"找不到素材: {media_name}")
            return
        self.current_media = media_name
        self.load_media(self.media_files[media_name], loop_once)
    
    def load_media(self, file_path, loop_once=False):
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.frames = []
        self.current_frame = 0
        self.is_animating = loop_once
        pil_img = Image.open(file_path)
        target_size = (self.current_size, self.current_size)
        if file_path.lower().endswith('.gif') and getattr(pil_img, 'is_animated', False):
            for frame in ImageSequence.Iterator(pil_img):
                frame_copy = frame.copy()
                frame_copy = frame_copy.resize(target_size, Image.Resampling.LANCZOS)
                self.frames.append(ImageTk.PhotoImage(frame_copy))
        else:
            pil_img = pil_img.resize(target_size, Image.Resampling.LANCZOS)
            self.frames.append(ImageTk.PhotoImage(pil_img))
        self.update_frame(loop_once)
        self.root.update_idletasks()
        self.root.geometry(f"{self.current_size}x{self.current_size}")
    
    def update_frame(self, loop_once=False):
        if not self.frames:
            return
        if self.label:
            self.label.config(image=self.frames[self.current_frame])
            self.label.image = self.frames[self.current_frame]
        if len(self.frames) > 1:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.after_id = self.root.after(100, lambda: self.update_frame(loop_once))
        elif loop_once and len(self.frames) == 1:
            self.root.after(500, lambda: self.switch_to_media("封面"))
        elif loop_once and len(self.frames) > 1:
            self.root.after(len(self.frames) * 100 + 500, lambda: self.switch_to_media("封面"))
    
    def create_widgets(self):
        self.label = tk.Label(self.root, bg="black")
        self.label.pack()
        if self.frames:
            self.label.config(image=self.frames[0])
        self.root.update_idletasks()
        self.root.geometry(f"{self.current_size}x{self.current_size}")
    
    def bind_events(self):
        self.label.bind("<ButtonPress-1>", self.start_drag)
        self.label.bind("<B1-Motion>", self.do_drag)
        self.label.bind("<Button-1>", self.on_single_click)
        self.label.bind("<Double-Button-1>", self.on_double_click)
        self.label.bind("<Button-3>", self.on_right_click)
    
    def start_drag(self, event):
        self.drag_x = event.x
        self.drag_y = event.y
    
    def do_drag(self, event):
        x = self.root.winfo_x() + (event.x - self.drag_x)
        y = self.root.winfo_y() + (event.y - self.drag_y)
        self.root.geometry(f"+{x}+{y}")
    
    def on_single_click(self, event):
        if self.focus_mode:
            return
        if self.is_baby_mode:
            self.handle_baby_click()
        else:
            self.switch_to_media("封面")
    
    def get_non_repeating_play_option(self):
        options = ["烤苞米", "抽象", "卖萌"]
        if self.last_play_option is None:
            chosen = random.choice(options)
        else:
            other_options = [opt for opt in options if opt != self.last_play_option]
            chosen = random.choice(other_options)
        self.last_play_option = chosen
        return chosen
    
    def on_double_click(self, event):
        if self.focus_mode or self.is_baby_mode:
            return
        chosen = self.get_non_repeating_play_option()
        self.switch_to_media(chosen, loop_once=True)
    
    def open_chat_window(self):
        """打开独立聊天窗口"""
        if self.chat_window is None or not self.chat_window.window.winfo_exists():
            self.chat_window = ChatWindow(
                self.root, 
                self.api_key, 
                self.api_url,
                on_close_callback=self.on_chat_window_close
            )
        else:
            self.chat_window.window.lift()  # 如果已存在，提到前面
    
    def on_chat_window_close(self):
        """聊天窗口关闭时的回调"""
        self.chat_window = None
    
    def on_right_click(self, event):
        if self.focus_mode:
            self.show_focus_menu(event)
        else:
            self.show_main_menu(event)


    def show_main_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0)
        feed_menu = tk.Menu(menu, tearoff=0)
        feed_options = ["吃菜包饭", "吃蛋糕", "吃卷饼", "吃面条"]
        for opt in feed_options:
            feed_menu.add_command(label=opt, command=lambda o=opt: self.switch_to_media(o, loop_once=True))
        menu.add_cascade(label="🍽️ 投喂", menu=feed_menu)
        menu.add_command(label="🎉 一起玩", command=self.play_together)
        menu.add_command(label="📚 专注模式", command=self.start_focus_mode)
        menu.add_separator()
        menu.add_command(label="🔍 调整大小", command=self.show_resize_slider)
        menu.add_separator()
        menu.add_command(label="👶 时间倒流", command=self.start_baby_mode)
        menu.add_separator()
        menu.add_command(label="💬 聊天", command=self.open_chat_window)
        menu.add_separator()  # 分隔线
        menu.add_command(label="❌ 退出", command=self.exit_app)  # 退出选项
        menu.post(event.x_root, event.y_root)  # 只调用一次，放在最后

    def exit_app(self):
        """退出程序"""
        self.root.quit()
        self.root.destroy()
    
    def show_resize_slider(self):
        resize_win = tk.Toplevel(self.root)
        resize_win.title("调整大小")
        resize_win.geometry("300x120")
        resize_win.attributes("-topmost", True)
        tk.Label(resize_win, text=f"当前大小: {self.current_size}px").pack(pady=5)
        def update_size(val):
            new_size = int(float(val))
            self.resize_media(new_size)
            size_label.config(text=f"当前大小: {new_size}px")
        slider = ttk.Scale(resize_win, from_=100, to=400, orient="horizontal",
                           value=self.current_size, command=update_size)
        slider.pack(pady=10, padx=20, fill="x")
        size_label = tk.Label(resize_win, text=f"当前大小: {self.current_size}px")
        size_label.pack()
        tk.Button(resize_win, text="关闭", command=resize_win.destroy).pack(pady=5)
    
    def play_together(self):
        if self.focus_mode or self.is_baby_mode:
            return
        chosen = self.get_non_repeating_play_option()
        self.switch_to_media(chosen, loop_once=True)
    
    def show_focus_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0)
        if self.focus_paused:
            menu.add_command(label="▶️ 继续计时", command=self.resume_focus)
        else:
            menu.add_command(label="⏸️ 暂停计时", command=self.pause_focus)
        menu.add_command(label="❌ 退出专注模式", command=self.exit_focus_early)
        menu.post(event.x_root, event.y_root)
    
    def start_focus_mode(self):
        if self.focus_mode:
            return
        self.focus_window = tk.Toplevel(self.root)
        self.focus_window.title("专注模式")
        self.focus_window.geometry("280x160")
        self.focus_window.attributes("-topmost", True)
        tk.Label(self.focus_window, text="设置专注时长（分钟）：", font=("微软雅黑", 11)).pack(pady=10)
        self.focus_spinbox = tk.Spinbox(self.focus_window, from_=1, to=120, width=10, font=("Arial", 12))
        self.focus_spinbox.pack(pady=5)
        def start_timer():
            try:
                minutes = int(self.focus_spinbox.get())
            except:
                minutes = 25
            self.focus_minutes = minutes
            self.focus_remaining_seconds = minutes * 60
            self.focus_mode = True
            self.focus_paused = False
            self.focus_window.destroy()
            if "监督" in self.media_files:
                self.load_media(self.media_files["监督"], loop_once=False)
            self.focus_timer_thread = threading.Thread(target=self.run_focus_timer, daemon=True)
            self.focus_timer_thread.start()
            self.show_countdown_window()
        tk.Button(self.focus_window, text="开始专注", command=start_timer, bg="#4CAF50", fg="white",
                  font=("微软雅黑", 10), padx=10).pack(pady=10)
    
    def show_countdown_window(self):
        self.countdown_win = tk.Toplevel(self.root)
        self.countdown_win.title("专注计时")
        self.countdown_win.geometry("220x100")
        self.countdown_win.attributes("-topmost", True)
        self.countdown_label = tk.Label(self.countdown_win, text="", font=("Arial", 24, "bold"), fg="#2196F3")
        self.countdown_label.pack(pady=20)
        self.update_countdown_display()
    
    def update_countdown_display(self):
        if not hasattr(self, 'countdown_label') or self.countdown_label is None:
            return
        try:
            minutes = self.focus_remaining_seconds // 60
            seconds = self.focus_remaining_seconds % 60
            self.countdown_label.config(text=f"{minutes:02d}:{seconds:02d}")
            if self.focus_mode and not self.focus_paused and self.focus_remaining_seconds > 0:
                self.countdown_win.after(1000, self.update_countdown_display)
        except:
            pass
    
    def run_focus_timer(self):
        while self.focus_remaining_seconds > 0 and self.focus_mode:
            if not self.focus_paused:
                time.sleep(1)
                self.focus_remaining_seconds -= 1
            else:
                time.sleep(0.5)
        if self.focus_remaining_seconds <= 0 and self.focus_mode:
            self.focus_mode = False
            self.focus_paused = False
            self.root.after(0, self.finish_focus_success)
    
    def show_custom_dialog(self, title, message, dialog_type="success"):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("300x150")
        dialog.attributes("-topmost", True)
        dialog.resizable(False, False)
        dialog.configure(bg="white")
        if dialog_type == "success":
            title_color = "#4CAF50"
            emoji = "🎉"
        else:
            title_color = "#F44336"
            emoji = "😢"
        tk.Label(dialog, text=f"{emoji} {title}", font=("微软雅黑", 14, "bold"),
                 fg=title_color, bg="white").pack(pady=10)
        tk.Label(dialog, text=message, font=("微软雅黑", 11),
                 fg="black", bg="white", wraplength=260).pack(pady=15)
        tk.Button(dialog, text="知道了", command=dialog.destroy,
                  bg="#2196F3", fg="white", font=("微软雅黑", 10),
                  padx=15, pady=3).pack(pady=10)
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
    
    def finish_focus_success(self):
        if self.countdown_win:
            self.countdown_win.destroy()
            self.countdown_win = None
        minutes = self.focus_minutes
        self.show_custom_dialog("专注完成！", f"你专注了 {minutes} 分钟！\n太棒啦！✨", "success")
        self.switch_to_media("记录此刻", loop_once=True)
    
    def pause_focus(self):
        self.focus_paused = True
    
    def resume_focus(self):
        self.focus_paused = False
        self.update_countdown_display()
    
    def exit_focus_early(self):
        self.focus_mode = False
        self.focus_paused = False
        if self.countdown_win:
            self.countdown_win.destroy()
            self.countdown_win = None
        elapsed_minutes = self.focus_minutes - (self.focus_remaining_seconds / 60)
        self.show_custom_dialog("专注中断", f"只专注了 {elapsed_minutes:.1f} 分钟…\n下次要坚持住呀！💪", "fail")
        self.switch_to_media("记录此刻", loop_once=True)

if __name__ == "__main__":
    root = tk.Tk()
    pet = Pet(root)
    root.mainloop()
