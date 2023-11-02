""" 
TODO 按照优先级排名
* ✅ 明文展示文件名
* ✅ 文件名区分状态
* ✅ 单文件直接解密
* ✅ 双击打开文件时，能够自动解密再打开
* 展示更多信息，比如大小、修改时间、排序
* 修改文件名
* 删除文件
* 移动文件

* 需要支持搜索功能（要不然对于文件太多的时候，就会存在难找的问题）
* 封装成App
* 监控文件变化，并且自动生成新的加密文件
* 在该程序不运行的时候，能够监控文件改变，避免被篡改（MD5对比）
* 新增文件
* 修改目录名
* 在Finder中展示

* 批量化
"""



import os
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import pystray
from PIL import Image,ImageTk
import base64
import time
from send2trash import send2trash
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler



# WatchDog 监控文件改变
class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, file_browser):
        self.file_browser = file_browser

    def on_modified(self, event):
        self.file_browser.load_nodes(self.file_browser.dir_path)

# 创建文件浏览器
class FileBrowser(ttk.Treeview):
    def __init__(self, parent, dir_path):
        super().__init__(parent)

        self.dir_path = dir_path
        self.nodes = {}
        self.insert('', 'end', dir_path, text=dir_path)
        self.load_nodes(dir_path)   
        self.bind('<Double-1>', self.open_file)  # 绑定双击事件

        # watchdog,监控文件变化
        self.observer = Observer()
        self.observer.schedule(FileChangeHandler(self), path=dir_path, recursive=True)
        self.observer.start()

        # 添加时间/大小
        # 需要在file_browser.insert('', 'end', values=('1024', '2020-01-01 12:00:00'))处理
        # 后续再实现
        # self['columns'] = ('大小', '修改时间')
        # self['show'] = 'headings'
        # self.heading('大小', text='大小', command=lambda: self.sortby('大小', False))
        # self.heading('修改时间', text='修改时间', command=lambda: self.sortby('修改时间', False))
        # self.column('大小', width=100, anchor='center')
        # self.column('修改时间', width=100, anchor='center')

    def sortby(self, col, descending):
        """sort tree contents when a column header is clicked on"""
        data = [(self.set(child, col), child) for child in self.get_children('')]
        data.sort(reverse=descending)
        for ix, item in enumerate(data):
            self.move(item[1], '', ix)
        self.heading(col, command=lambda: self.sortby(col, not descending))

    # 获取选中的文件，选中多个，可能是个list
    def get_selected_file(self):
        return self.selection()

    # 加载目录下的文件
    def load_nodes(self, dir_path):
        for i in self.get_children():
            self.delete(i)
        self.nodes = {}
        self.insert('', 'end', dir_path, text='🟢 当前浏览路径：'+dir_path)

        for dirpath, dirnames, filenames in os.walk(dir_path):
            self.add_dirs(dirpath, dirnames)
            # filenames = [ self.decrypt_name(filename)  for filename in filenames]
            # print(filenames)
            self.add_files(dirpath, filenames)
    
    def file_name_show(self, file_name):
        if file_name.endswith('.b64') :
            file_name_dec = base64.urlsafe_b64decode(file_name[:-4]).decode("UTF-8") 
            # image_ok = Image.open(current_dir+'/res/okiconTemplate.png') 
            # icon_ok = ImageTk.PhotoImage(image_ok)  
            # icon_ok = tk.PhotoImage(file= current_dir+'/res/okiconTemplate.png')
            return ('🔰 ' + file_name_dec )
        else:
            # image_x = Image.open(current_dir+'/res/xiconTemplate.png') 
            # icon_x = ImageTk.PhotoImage(image_x)  
            # icon_x = tk.PhotoImage(file= current_dir+'/res/xiconTemplate.png')
            return ('👁️ ' + file_name )

    def add_dirs(self, dirpath, dirnames):
        for dirname in dirnames:
            abs_dir = os.path.join(dirpath, dirname)
            parent_abs_dir = os.path.dirname(abs_dir)
            parent_node = self.nodes.get(parent_abs_dir, '')
            node = self.insert(parent_node, 'end', abs_dir, text=dirname)
            self.nodes[abs_dir] = node

    def add_files(self, dirpath, filenames):
        for filename in filenames:
            if filename.endswith('.DS_Store'):  # 排除.DS_Store文件
                continue
            abs_file = os.path.join(dirpath, filename)
            parent_abs_file = os.path.dirname(abs_file)
            parent_node = self.nodes.get(parent_abs_file, '')
        
            self.insert(parent_node, 'end', abs_file, text=self.file_name_show(filename))

    def open_file(self,event):
        filepath = self.selection()[0]  # 获取选中的项  
        if os.path.isfile(filepath):  # 如果是文件，用系统默认程序打开
            filepath_real = decrypt_file(os.path.dirname(filepath),os.path.basename(filepath))
            try:
                subprocess.run(['open', filepath_real], check=True)
            except subprocess.CalledProcessError as e:
                messagebox.showerror('错误', f'无法打开文件: {e}')
                print(f'无法打开文件: {e}')

class SystemTrayIcon:
    def __init__(self, window):
        self.window = window
        self.icon = None
        self.dir_path = window.dir_path

    def hide_window_and_create_icon(self):
        self.window.withdraw()

        # image = Image.open(current_dir+'/res/okiconTemplate.png')  # 你需要一个icon.png作为图标
        image = Image.open('okiconTemplate.png')  # 你需要一个icon.png作为图标
        menu = (pystray.MenuItem('打开窗口', self.on_tray_browser_click),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem('Enc全部', self.on_tray_encypt_click),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem('退出', self.on_tray_quit_click)
                )
        self.icon = pystray.Icon("name", image, "My System Tray Icon", menu)
        threading.Thread(target=self.icon.run).start()

    def on_tray_browser_click(self):
        self.window.deiconify()
        self.icon.stop()
        self.icon.remove()

    def on_tray_encypt_click(self):
        walk_encrypt_files(self.dir_path)

    def on_tray_quit_click(self, icon, item):
        # 显示确认对话框
        if messagebox.askyesno("确认", "你确定要退出吗？"):
            icon.stop()  # 停止系统托盘图标
            self.window.destroy()  # 销毁Tk窗口

class MainWindow(tk.Tk):
    def __init__(self, dir_path):
        super().__init__()
        self.dir_path = dir_path
        self.title('ProtectMyFile')

        tm = 150
        tn = 20
        button1 = tk.Button(self, text='🔒 Enc All', command=self.encypt_all)
        button1.place(x=tn, y=0)  # 将按钮放在左上角

        button2 = tk.Button(self, text='🔑 Dec Select', command=self.decrypt_sel_file)
        button2.place(x=tn+tm, y=0)# 将按钮放在button1的右边

        button3 = tk.Button(self, text='💻 Finder打开', command=self.open_dir)
        button3.place(x=tn+2*tm, y=0)  # 将按钮放在button2的右边

        button4 = tk.Button(self, text='❌ 退出程序', command=self.quit_program)
        button4.place(x=tn+3*tm, y=0)  # 将按钮放在button2的右边


        
        self.file_browser = FileBrowser(self, dir_path)
        self.file_browser.place(x=10, y=button1.winfo_reqheight(), relwidth=1, relheight=1)  # 将file_browser放在按钮下方，并填满剩余空间
        
        # 创建托盘图标
        self.system_tray_icon = SystemTrayIcon(self)

        # 或者按照屏幕的分辨率设置窗口的大小，并居中
        self.center_window(0.6*self.winfo_screenwidth(), 0.6*self.winfo_screenheight())  

        # 关闭按钮，设置为隐藏而非关闭
        self.protocol("WM_DELETE_WINDOW", self.system_tray_icon.hide_window_and_create_icon)

    def open_dir(self):
        file_paths = self.file_browser.get_selected_file()
        print("Opening file: ", file_paths)
        if not file_paths:
            messagebox.showinfo('Info', 'No file selected')
            return
        try:
            # 只能打开第一个文件的目录
            subprocess.run(['open', os.path.dirname(file_paths[0])])      
        except Exception as e:
            messagebox.showinfo('Error', f'解密出现错误，具体错误原因: {e}')


    
    def decrypt_sel_file(self):
        file_paths = self.file_browser.get_selected_file()
        print("Opening file: ", file_paths)
        if not file_paths:
            messagebox.showinfo('Info', 'No file selected')
            return
        try:
            for file_path in file_paths:
                decrypt_file(os.path.dirname(file_path),os.path.basename(file_path))
            messagebox.showinfo('完成', f'解密完成，{str(len(file_paths))}个文件已解密！')
        except Exception as e:
            messagebox.showinfo('Error', f'解密出现错误，具体错误原因: {e}')

 
    
    def encypt_all(self):
        walk_encrypt_files(self.dir_path)

    def quit_program(self):
        if messagebox.askyesno("确认", "你确定要退出吗？"):
            self.destroy()
    
    def center_window(self, width=500, height=400):
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        size = '%dx%d+%d+%d' % (width, height, (screenwidth - width)/2, (screenheight - height)/2)
        self.geometry(size)

def cur_ftime():
    # 获取当前时间戳
    timestamp = time.time()
    # 将时间戳转换为datetime对象
    dt = datetime.fromtimestamp(timestamp)
    # 将datetime对象格式化为字符串
    return dt.strftime('%Y-%m-%d %H:%M:%S')
     

def encrypt_file(file_path,file_name):
    # 待加密的完整文件路径
    file_path_decrypt = os.path.join(file_path, file_name)

    # 判断是否要处理
    if (file_name in except_list 
        or file_name.endswith('.b64')
        # or file_name.endswith('.py') #test情况下可启用
        ):

        print(cur_ftime(),':\n -- 文件夹路径:',file_path,'\n -- 原始文件名:',file_name,'\n -- 加密文件名: 文件在排除列表，未处理\n')      

    else:
        # 加密文件名
        file_byte = base64.urlsafe_b64encode(file_name.encode("UTF-8"))
        file_name_encrypt = file_byte.decode('UTF-8')
        file_path_encrypt = os.path.join(file_path, file_name_encrypt )

        with open(file_path_decrypt, 'rb') as f_in, open(file_path_encrypt + '.b64', 'wb') as f_out:
            while True:
                data = f_in.read(1020)
                if not data:
                    break
                # 对文件内容进行Base64编码
                encoded_data = base64.b64encode(data)
                # 将加密后的数据写入新文件
                f_out.write(encoded_data)
        send2trash(file_path_decrypt)

        print(cur_ftime(),':\n -- 文件夹路径:',file_path,'\n -- 原始文件名:',file_name,'\n -- 加密文件名:',file_name_encrypt,'\n -- 备注与说明: 原文件已移入回收站\n')      

   
        
# 遍历指定目录下的所有文件，进行加密
def walk_encrypt_files(dir_path):
    start_time = time.time()
    for root, dirs, files in os.walk(dir_path):
        for file in files :
            encrypt_file(root,file)
    end_time = time.time()
    print(cur_ftime(),': ',dir_path,"全部加密完成，程序运行时间：", end_time - start_time, "秒\n\n")
    messagebox.showinfo(title = '完成', message='全部加密完成，程序运行时间：'+str(round(end_time - start_time,4)))




# 对指定文件进行解密
def decrypt_file(file_path,file_name):
    file_path_enc = os.path.join(file_path , file_name)
    if file_name[-4:] == '.b64':
        
        # 先对file_path进行解密
        # print(file_name[:-4])
        dec_name = base64.urlsafe_b64decode(file_name[:-4]).decode("UTF-8") 
        file_path_dec = os.path.join(file_path , dec_name) 
       
       # 写入解密文件
        with open(file_path_enc, 'rb') as f_in, open(file_path_dec, 'wb') as f_out:
            while True:
                data = f_in.read(1024)
                # 会在read(1024)返回空的字节串时退出循环
                if not data:
                    break
                # 对文件内容进行Base64解码
                decoded_data = base64.b64decode(data)
                # 将解密后的数据写入新文件
                f_out.write(decoded_data)
        print(cur_ftime(),':\n -- 文件夹路径:',file_path,'\n -- 原始文件名:',file_name,'\n -- 解密文件名:',dec_name,'\n')      
        return file_path_dec
    else:
        print("该文件未加密")
        return file_path_enc




if __name__ == "__main__":

    # 全局定义区
    dir_path_global = '/Users/工作盘/ProtectedDir'
    current_dir = os.path.dirname(os.path.realpath(__file__))
    print('\n----\n',cur_ftime(),': 当前代码运行目录为 ',current_dir)

    except_list = [os.path.basename(__file__),'.DS_Store','run_test.py','iconTemplate.png']
    print(cur_ftime(),': 以下文件不会被加密处理 ',except_list)

    #主程序
    window = MainWindow(dir_path_global)
    # window.title()
    window.mainloop()
