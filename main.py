import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from tkinterdnd2 import DND_FILES, TkinterDnD
import csv
import os
import uuid
from datetime import datetime

# --- 定数定義 ---
DEFAULT_DATA_FOLDER = "taskcon_data"
DEFAULT_DATA_FILE = os.path.join(DEFAULT_DATA_FOLDER, "tasks.csv")
DEFAULT_TAGS_FILE = os.path.join(DEFAULT_DATA_FOLDER, "tags.txt")  # タグを保存するファイル
WINDOW_TITLE = "taskcon"
WINDOW_GEOMETRY = "700x650"
# CSVヘッダーに新しい項目を追加
CSV_HEADERS = ["id", "name", "status", "priority", "due_date", "tags", "today"]

# --- デザイン/文言定義 ---
FONT_FAMILY = "Yu Gothic UI"
# FONT_FAMILY = "Hiragino Sans" # for macOS
FONT_SIZE_NORMAL = 11
FONT_SIZE_LARGE = 14
MONOSPACE_FONT = "Consolas"  # 固定幅フォント
PRIORITY_LEVELS = ["高", "中", "低"]
STATUS_OPTIONS = ["すべて", "未着手", "完了"]
SORT_OPTIONS = ["追加順", "期限順", "優先度順", "タグ順"]
TODAY_OPTIONS = ["〇", ""]

COLOR_BG = "#f0f0f0"
COLOR_FRAME_BG = "#ffffff"
COLOR_OVERDUE = "#e74c3c" # 期限切れタスクの文字色
COLOR_COMPLETED = "gray"
COLOR_INCOMPLETE = "black"


class SettingsWindow:
    """設定ウィンドウクラス"""
    
    def __init__(self, parent, data_folder):
        self.parent = parent
        self.data_folder = data_folder
        self.result_data_folder = data_folder
        
        self.window = tk.Toplevel(parent)
        self.window.title("設定")
        self.window.geometry("500x150")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        
        self._create_widgets()
        
        # ウィンドウを中央に配置
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.window.winfo_screenheight() // 2) - (150 // 2)
        self.window.geometry(f"500x150+{x}+{y}")
        
    def _create_widgets(self):
        """ウィジェットを作成"""
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # データフォルダ設定
        ttk.Label(main_frame, text="データフォルダ:", font=(FONT_FAMILY, FONT_SIZE_NORMAL)).grid(row=0, column=0, sticky="w", pady=5)
        
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        folder_frame.columnconfigure(0, weight=1)
        
        self.data_folder_var = tk.StringVar(value=self.data_folder)
        self.data_folder_entry = ttk.Entry(folder_frame, textvariable=self.data_folder_var, width=50)
        self.data_folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        ttk.Button(folder_frame, text="参照", command=self._browse_data_folder).grid(row=0, column=1)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        button_frame.columnconfigure([0, 1], weight=1)
        
        ttk.Button(button_frame, text="OK", command=self._ok_clicked).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="キャンセル", command=self._cancel_clicked).grid(row=0, column=1, padx=5)
        
    def _browse_data_folder(self):
        """データフォルダ選択ダイアログ"""
        from tkinter import filedialog
        folder = filedialog.askdirectory(
            title="データフォルダを選択",
            initialdir=self.data_folder
        )
        if folder:
            self.data_folder_var.set(folder)
            
    def _ok_clicked(self):
        """OKボタンクリック時の処理"""
        self.result_data_folder = self.data_folder_var.get()
        self.window.destroy()
        
    def _cancel_clicked(self):
        """キャンセルボタンクリック時の処理"""
        self.window.destroy()
        
    def show(self):
        """設定ウィンドウを表示"""
        self.window.wait_window()
        return self.result_data_folder


class TaskApp:
    """
    多機能タスク管理アプリケーションのメインクラス
    """

    def __init__(self, root):
        self.root = root
        self.tasks = []  # すべてのタスクのマスターリスト
        self.view_tasks = [] # 現在表示されているタスクのリスト
        self.view_completed_tasks = [] # 完了タスクのリスト
        self.view_today_tasks = [] # 今日やるタスクのリスト
        self.tags = []  # 既存のタグリスト
        
        # データフォルダの設定
        self.data_folder = DEFAULT_DATA_FOLDER
        self.data_file = DEFAULT_DATA_FILE
        self.tags_file = DEFAULT_TAGS_FILE
        
        self._setup_window()
        self._create_widgets()
        self.load_tags()  # タグを先に読み込む
        self.load_tasks()

    def _setup_window(self):
        """ウィンドウの基本的な設定"""
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_GEOMETRY)
        self.root.configure(bg=COLOR_BG)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1) # Listboxの行を伸縮させる

    def _create_widgets(self):
        """GUIウィジェットを作成し、配置する"""
        # --- Notebook（タブ） ---
        self.root.rowconfigure(3, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 5))
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.apply_filters_and_sort())

        # --- タスク一覧タブ ---
        self.tab_incomplete = ttk.Frame(self.notebook)
        self.tab_incomplete.rowconfigure(1, weight=1)  # リストフレームを伸縮させる
        self.tab_incomplete.columnconfigure(0, weight=1)
        self.notebook.add(self.tab_incomplete, text="一覧")

        # --- 今日やるタスクタブ ---
        self.tab_today = ttk.Frame(self.notebook)
        self.tab_today.rowconfigure(1, weight=1)  # リストフレームを伸縮させる
        self.tab_today.columnconfigure(0, weight=1)
        self.notebook.add(self.tab_today, text="今日")

        # --- 完了タスクタブ ---
        self.tab_completed = ttk.Frame(self.notebook)
        self.tab_completed.rowconfigure(1, weight=1)  # リストフレームを伸縮させる
        self.tab_completed.columnconfigure(0, weight=1)
        self.notebook.add(self.tab_completed, text="完了")

        # --- 入力フレーム ---
        input_frame = ttk.LabelFrame(self.root, text="タスクの追加・編集", padding=10)
        input_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        input_frame.columnconfigure(1, weight=1)

        # 1行目: タスク名
        ttk.Label(input_frame, text="タスク名:", font=(FONT_FAMILY, FONT_SIZE_NORMAL)).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.task_entry = ttk.Entry(input_frame, font=(FONT_FAMILY, FONT_SIZE_LARGE))
        self.task_entry.grid(row=0, column=1, columnspan=2, sticky="ew", pady=2)
        self.task_entry.bind("<Return>", lambda e: self.add_or_update_task())

        # 2行目: 優先度、期限日、タグ
        ttk.Label(input_frame, text="優先度:", font=(FONT_FAMILY, FONT_SIZE_NORMAL)).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.priority_var = tk.StringVar(value=PRIORITY_LEVELS[1])
        priority_combo = ttk.Combobox(input_frame, textvariable=self.priority_var, values=PRIORITY_LEVELS, state="readonly", width=8)
        priority_combo.grid(row=1, column=1, sticky="w", pady=2)

        ttk.Label(input_frame, text="期限日:", font=(FONT_FAMILY, FONT_SIZE_NORMAL)).grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.due_date_entry = DateEntry(input_frame, date_pattern='yyyy-mm-dd', width=12)
        self.due_date_entry.grid(row=2, column=1, sticky="w", pady=2)
        
        ttk.Label(input_frame, text="タグ (カンマ区切り):", font=(FONT_FAMILY, FONT_SIZE_NORMAL)).grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.tags_var = tk.StringVar()
        self.tags_combo = ttk.Combobox(input_frame, textvariable=self.tags_var, width=30)
        self.tags_combo.grid(row=3, column=1, columnspan=2, sticky="ew", pady=2)
        self.tags_combo.bind("<KeyRelease>", self.on_tags_input)
        self.tags_combo.bind("<<ComboboxSelected>>", self.on_tags_selected)
        
        ttk.Label(input_frame, text="今日:", font=(FONT_FAMILY, FONT_SIZE_NORMAL)).grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.today_var = tk.StringVar(value=TODAY_OPTIONS[1])
        today_combo = ttk.Combobox(input_frame, textvariable=self.today_var, values=TODAY_OPTIONS, state="readonly", width=12)
        today_combo.grid(row=4, column=1, sticky="w", pady=2)
        
        # 追加・更新ボタン
        add_button = ttk.Button(input_frame, text="追加・更新", command=self.add_or_update_task)
        add_button.grid(row=0, column=3, rowspan=3, sticky="ns", padx=10)
        
        # クリアボタン
        clear_button = ttk.Button(input_frame, text="クリア", command=self.clear_inputs)
        clear_button.grid(row=3, column=3, rowspan=2, sticky="ns", padx=10)

        # --- フィルター/ソートフレーム ---
        filter_frame = ttk.LabelFrame(self.root, text="表示設定", padding=10)
        filter_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        filter_frame.columnconfigure(1, weight=1)

        ttk.Label(filter_frame, text="検索:", font=(FONT_FAMILY, FONT_SIZE_NORMAL)).grid(row=0, column=0, sticky="w", padx=5)
        self.search_entry = ttk.Entry(filter_frame)
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.apply_filters_and_sort())

        ttk.Label(filter_frame, text="状態:", font=(FONT_FAMILY, FONT_SIZE_NORMAL)).grid(row=0, column=2, sticky="w", padx=5)
        self.status_filter_var = tk.StringVar(value=STATUS_OPTIONS[0])
        status_filter_combo = ttk.Combobox(filter_frame, textvariable=self.status_filter_var, values=STATUS_OPTIONS, state="readonly", width=10)
        status_filter_combo.grid(row=0, column=3, sticky="w", padx=5)
        status_filter_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters_and_sort())
        
        ttk.Label(filter_frame, text="並び替え:", font=(FONT_FAMILY, FONT_SIZE_NORMAL)).grid(row=0, column=4, sticky="w", padx=5)
        self.sort_var = tk.StringVar(value=SORT_OPTIONS[0])
        sort_combo = ttk.Combobox(filter_frame, textvariable=self.sort_var, values=SORT_OPTIONS, state="readonly", width=10)
        sort_combo.grid(row=0, column=5, sticky="w", padx=5)
        sort_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters_and_sort())

        # --- タスク一覧リストフレーム ---
        list_frame = ttk.Frame(self.tab_incomplete, padding=(0, 0, 0, 5))
        list_frame.grid(row=1, column=0, sticky="nsew")  # row=1に変更
        list_frame.columnconfigure(1, weight=1)
        list_frame.rowconfigure(0, weight=1)  # リストボックス行を伸縮

        # Treeviewでタスク一覧を作成
        columns = ('選択', '優先度', '状態', 'タスク名', '期限日', 'タグ')
        self.task_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # 列の設定
        self.task_tree.heading('選択', text='選択')
        self.task_tree.heading('優先度', text='優先度')
        self.task_tree.heading('状態', text='状態')
        self.task_tree.heading('タスク名', text='タスク名')
        self.task_tree.heading('期限日', text='期限日')
        self.task_tree.heading('タグ', text='タグ')
        
        # 列幅の設定（アプリ起動時の幅に合わせて調整）
        self.task_tree.column('選択', width=30, minwidth=30)
        self.task_tree.column('優先度', width=60, minwidth=60)
        self.task_tree.column('状態', width=80, minwidth=80)
        self.task_tree.column('タスク名', width=300, minwidth=200)
        self.task_tree.column('期限日', width=100, minwidth=100)
        self.task_tree.column('タグ', width=100, minwidth=100)
        
        self.task_tree.grid(row=0, column=0, sticky="nsew")
        self.task_tree.bind("<<TreeviewSelect>>", self.on_task_select)
        self.task_tree.bind("<Button-1>", self.on_tree_click)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.config(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # --- 完了タスクリストフレーム ---
        completed_frame = ttk.Frame(self.tab_completed, padding=(0, 0, 0, 5))
        completed_frame.grid(row=1, column=0, sticky="nsew")  # row=1に変更
        completed_frame.columnconfigure(0, weight=1)
        completed_frame.rowconfigure(0, weight=1)  # リストボックス行を伸縮

        # Treeviewで完了タスク一覧を作成
        self.completed_tree = ttk.Treeview(completed_frame, columns=columns, show='headings', height=15)
        
        # 列の設定
        self.completed_tree.heading('選択', text='選択')
        self.completed_tree.heading('優先度', text='優先度')
        self.completed_tree.heading('状態', text='状態')
        self.completed_tree.heading('タスク名', text='タスク名')
        self.completed_tree.heading('期限日', text='期限日')
        self.completed_tree.heading('タグ', text='タグ')
        
        # 列幅の設定（アプリ起動時の幅に合わせて調整）
        self.completed_tree.column('選択', width=30, minwidth=30)
        self.completed_tree.column('優先度', width=60, minwidth=60)
        self.completed_tree.column('状態', width=80, minwidth=80)
        self.completed_tree.column('タスク名', width=300, minwidth=200)
        self.completed_tree.column('期限日', width=100, minwidth=100)
        self.completed_tree.column('タグ', width=100, minwidth=100)
        
        self.completed_tree.grid(row=0, column=0, sticky="nsew")
        self.completed_tree.bind("<Button-1>", self.on_completed_tree_click)

        completed_scrollbar = ttk.Scrollbar(completed_frame, orient=tk.VERTICAL, command=self.completed_tree.yview)
        self.completed_tree.config(yscrollcommand=completed_scrollbar.set)
        completed_scrollbar.grid(row=0, column=1, sticky="ns")

        # --- 今日やるタスクリストフレーム ---
        today_frame = ttk.Frame(self.tab_today, padding=(0, 0, 0, 5))
        today_frame.grid(row=1, column=0, sticky="nsew")  # row=1に変更
        today_frame.columnconfigure(0, weight=1)
        today_frame.rowconfigure(0, weight=1)  # リストボックス行を伸縮

        # Treeviewで今日タスク一覧を作成
        self.today_tree = ttk.Treeview(today_frame, columns=columns, show='headings', height=15)
        
        # 列の設定
        self.today_tree.heading('選択', text='選択')
        self.today_tree.heading('優先度', text='優先度')
        self.today_tree.heading('状態', text='状態')
        self.today_tree.heading('タスク名', text='タスク名')
        self.today_tree.heading('期限日', text='期限日')
        self.today_tree.heading('タグ', text='タグ')
        
        # 列幅の設定（アプリ起動時の幅に合わせて調整）
        self.today_tree.column('選択', width=30, minwidth=30)
        self.today_tree.column('優先度', width=60, minwidth=60)
        self.today_tree.column('状態', width=80, minwidth=80)
        self.today_tree.column('タスク名', width=300, minwidth=200)
        self.today_tree.column('期限日', width=100, minwidth=100)
        self.today_tree.column('タグ', width=100, minwidth=100)
        
        self.today_tree.grid(row=0, column=0, sticky="nsew")
        self.today_tree.bind("<<TreeviewSelect>>", self.on_today_task_select)
        self.today_tree.bind("<Button-1>", self.on_today_tree_click)

        today_scrollbar = ttk.Scrollbar(today_frame, orient=tk.VERTICAL, command=self.today_tree.yview)
        self.today_tree.config(yscrollcommand=today_scrollbar.set)
        today_scrollbar.grid(row=0, column=1, sticky="ns")

        # --- 操作ボタンフレーム ---
        button_frame = ttk.Frame(self.root, padding=10)
        button_frame.grid(row=4, column=0, sticky="ew")
        button_frame.columnconfigure([0, 1, 2, 3, 4], weight=1)
        
        ttk.Button(button_frame, text="完了 / 未着手", command=self.toggle_task_status).grid(row=0, column=0, padx=5, sticky="ew")
        ttk.Button(button_frame, text="今日 / 今日以外", command=self.toggle_today_status).grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(button_frame, text="削除", command=self.delete_task).grid(row=0, column=2, padx=5, sticky="ew")
        ttk.Button(button_frame, text="設定", command=self.show_settings).grid(row=0, column=3, padx=5, sticky="ew")
        ttk.Button(button_frame, text="終了", command=self.root.quit).grid(row=0, column=4, padx=5, sticky="ew")

    def apply_filters_and_sort(self):
        """フィルターとソートを適用してタスクを表示"""
        current_tab = self.notebook.tab(self.notebook.select(), "text")
        
        # 現在のタブに応じてタスクをフィルター
        if current_tab == "一覧":
            filtered_tasks = [task for task in self.tasks if task['status'] != "完了" and task['today'] != TODAY_OPTIONS[0]]
        elif current_tab == "今日":
            filtered_tasks = [task for task in self.tasks if task['today'] == TODAY_OPTIONS[0] and task['status'] != "完了"]
        elif current_tab == "完了":
            filtered_tasks = [task for task in self.tasks if task['status'] == "完了"]
        else:
            filtered_tasks = self.tasks.copy()
        
        # 検索フィルターを適用
        search_term = self.search_entry.get().lower()
        if search_term:
            filtered_tasks = [task for task in filtered_tasks if search_term in task["name"].lower() or search_term in (task["tags"] or "").lower()]
        
        # ソートを適用
        sort_option = self.sort_var.get()
        if sort_option == "追加順":
            # 追加順は変更なし（既存の順序を維持）
            pass
        elif sort_option == "期限順":
            filtered_tasks.sort(key=lambda x: (x['due_date'] or '9999-12-31', x['priority']))
        elif sort_option == "優先度順":
            filtered_tasks.sort(key=lambda x: (x['priority'], x['due_date'] or '9999-12-31'))
        elif sort_option == "タグ順":
            filtered_tasks.sort(key=lambda x: (x['tags'] or '', x['due_date'] or '9999-12-31'))
        
        # 現在のタブに応じて適切なリストに設定
        if current_tab == "一覧":
            self.view_tasks = filtered_tasks
        elif current_tab == "今日":
            self.view_today_tasks = filtered_tasks
        elif current_tab == "完了":
            self.view_completed_tasks = filtered_tasks
        
        self._populate_listbox()

    def _populate_listbox(self):
        """Treeviewをview_tasks, view_completed_tasksの内容で埋める"""
        self.task_tree.delete(*self.task_tree.get_children())
        self.completed_tree.delete(*self.completed_tree.get_children())
        self.today_tree.delete(*self.today_tree.get_children())
        
        today = datetime.now().date()
        
        # 未完了タスク
        for i, task in enumerate(self.view_tasks):
            # 完了ステータスを優先度の横に表示
            status_text = "完了" if task["status"] == "完了" else "未着手"
            prio = f"[{task.get('priority', '中')}]"
            status = f"[{status_text}]"
            due = f"{task.get('due_date', 'なし')}"
            tags_disp = f"{task.get('tags', '')}" if task.get("tags") else ""
            
            # Treeviewにアイテムを追加（チェックボックスは初期状態で未チェック）
            item_id = self.task_tree.insert("", "end", values=("□", prio, status, task['name'], due, tags_disp))
            
            # 色の設定
            color = COLOR_INCOMPLETE
            if task.get("due_date"):
                try:
                    due_date_obj = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
                    if due_date_obj < today:
                        color = COLOR_OVERDUE
                except ValueError:
                    pass
            
            # 色をタグとして設定
            self.task_tree.tag_configure(color, foreground=color)
            self.task_tree.item(item_id, tags=(color,))
        
        # 完了タスク
        for i, task in enumerate(self.view_completed_tasks):
            # 完了ステータスを優先度の横に表示
            status_text = "完了"
            prio = f"[{task.get('priority', '中')}]"
            status = f"[{status_text}]"
            due = f"{task.get('due_date', 'なし')}"
            tags_disp = f"{task.get('tags', '')}" if task.get("tags") else ""
            
            # Treeviewにアイテムを追加（チェックボックスは初期状態で未チェック）
            item_id = self.completed_tree.insert("", "end", values=("□", prio, status, task['name'], due, tags_disp))
            
            # 色をタグとして設定
            self.completed_tree.tag_configure(COLOR_COMPLETED, foreground=COLOR_COMPLETED)
            self.completed_tree.item(item_id, tags=(COLOR_COMPLETED,))
        
        # 今日やるタスク
        for i, task in enumerate(self.view_today_tasks):
            # 完了ステータスを優先度の横に表示
            status_text = "完了" if task["status"] == "完了" else "未着手"
            prio = f"[{task.get('priority', '中')}]"
            status = f"[{status_text}]"
            due = f"{task.get('due_date', 'なし')}"
            tags_disp = f"{task.get('tags', '')}" if task.get("tags") else ""
            
            # Treeviewにアイテムを追加（チェックボックスは初期状態で未チェック）
            item_id = self.today_tree.insert("", "end", values=("□", prio, status, task['name'], due, tags_disp))
            
            # 色の設定
            color = COLOR_COMPLETED if task["status"] == "完了" else COLOR_INCOMPLETE
            if task.get("due_date"):
                try:
                    due_date_obj = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
                    if due_date_obj < today:
                        color = COLOR_OVERDUE
                except ValueError:
                    pass
            
            # 色をタグとして設定
            self.today_tree.tag_configure(color, foreground=color)
            self.today_tree.item(item_id, tags=(color,))

    def on_task_select(self, event=None):
        """Treeviewでタスクが選択されたときの処理"""
        selected_items = self.task_tree.selection()
        if not selected_items:
            return
        
        # 複数選択時は入力フォームを更新しない
        if len(selected_items) > 1:
            return
        
        selected_item = selected_items[0]
        # Treeviewのアイテムから値を取得
        values = self.task_tree.item(selected_item, 'values')
        if not values:
            return
        
        # タスク名からマスターリストのタスクを検索
        task_name = values[3]  # タスク名は4番目の列
        task = None
        for t in self.view_tasks:
            if t["name"] == task_name:
                task = t
                break
        
        if not task:
            return

        self.task_entry.delete(0, tk.END)
        self.task_entry.insert(0, task.get("name", ""))
        self.priority_var.set(task.get("priority", PRIORITY_LEVELS[1]))
        
        # 日付の設定
        due_date = task.get("due_date", "")
        if due_date:
            try:
                date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()
                self.due_date_entry.set_date(date_obj)
            except ValueError:
                self.due_date_entry.set_date(None)
        else:
            self.due_date_entry.set_date(None)
            
        self.tags_var.set(task.get("tags", ""))
        self.today_var.set(task.get("today", TODAY_OPTIONS[1]))
        
    def on_today_task_select(self, event=None):
        """今日やるタスクTreeviewでタスクが選択されたときの処理"""
        selected_items = self.today_tree.selection()
        if not selected_items:
            return
        
        # 複数選択時は入力フォームを更新しない
        if len(selected_items) > 1:
            return
        
        selected_item = selected_items[0]
        # Treeviewのアイテムから値を取得
        values = self.today_tree.item(selected_item, 'values')
        if not values:
            return
        
        # タスク名からマスターリストのタスクを検索
        task_name = values[3]  # タスク名は4番目の列
        task = None
        for t in self.view_today_tasks:
            if t["name"] == task_name:
                task = t
                break
        
        if not task:
            return

        self.task_entry.delete(0, tk.END)
        self.task_entry.insert(0, task.get("name", ""))
        self.priority_var.set(task.get("priority", PRIORITY_LEVELS[1]))
        
        # 日付の設定
        due_date = task.get("due_date", "")
        if due_date:
            try:
                date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()
                self.due_date_entry.set_date(date_obj)
            except ValueError:
                self.due_date_entry.set_date(None)
        else:
            self.due_date_entry.set_date(None)
            
        self.tags_var.set(task.get("tags", ""))
        self.today_var.set(task.get("today", TODAY_OPTIONS[1]))

    def _clear_inputs(self):
        """入力フィールドをクリアする"""
        self.task_entry.delete(0, tk.END)
        self.priority_var.set(PRIORITY_LEVELS[1])
        # 期限日を当日に設定
        self.due_date_entry.set_date(datetime.now().date())
        self.tags_var.set("")
        self.today_var.set(TODAY_OPTIONS[1])


    # --- データ永続化 (CSV) ---
    def load_tasks(self):
        """CSVファイルからタスクを読み込む"""
        self.tasks = []
        
        # データフォルダが存在しない場合は作成
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
            
        if not os.path.exists(self.data_file):
            return

        try:
            with open(self.data_file, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    task = {
                        "id": row.get("id", str(uuid.uuid4())),
                        "name": row.get("name", ""),
                        "status": row.get("status", "未着手"),
                        "priority": row.get("priority", "中"),
                        "due_date": row.get("due_date", ""),
                        "tags": row.get("tags", ""),
                        "today": row.get("today", TODAY_OPTIONS[1])
                    }
                    self.tasks.append(task)
        except Exception as e:
            messagebox.showerror("エラー", f"ファイルの読み込みに失敗しました: {e}")
            self.tasks = []
            
        self.apply_filters_and_sort()
        # 既存のタスクからタグを抽出
        self.extract_tags_from_tasks()
        
        # すべてのタブでフィルタリングを適用
        for tab_index in range(3):  # 0: 一覧, 1: 今日, 2: 完了
            self.notebook.select(tab_index)
            self.apply_filters_and_sort()
        
        # 一覧タブに戻す
        self.notebook.select(0)

    def save_tasks(self):
        """現在のタスクリストをCSVファイルに保存する"""
        # データフォルダが存在しない場合は作成
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
            
        try:
            with open(self.data_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                writer.writeheader()
                writer.writerows(self.tasks)
        except IOError as e:
            messagebox.showerror("エラー", f"ファイルへの保存に失敗しました: {e}")

    # --- タスク操作 (CRUD) ---
    def add_task(self):
        task_name = self.task_entry.get().strip()
        if not task_name:
            messagebox.showwarning("入力エラー", "タスク名を入力してください。")
            return
        
        due_date = self.due_date_entry.get_date()
        if due_date:
            due_date_str = due_date.strftime("%Y-%m-%d")
        else:
            due_date_str = ""

        new_task = {
            "id": str(uuid.uuid4()),
            "name": task_name,
            "status": "未着手",
            "priority": self.priority_var.get(),
            "due_date": due_date_str,
            "tags": self.tags_var.get(),
            "today": self.today_var.get()
        }
        self.tasks.append(new_task)
        # タスク名のみクリア、タグと期限日は保持
        self.task_entry.delete(0, tk.END)
        self.priority_var.set(PRIORITY_LEVELS[1])
        # タグと期限日はクリアしない
        self.apply_filters_and_sort()
        # 新しいタグを保存
        self.extract_tags_from_tasks()
        # 未使用タグをクリーンアップ
        self.cleanup_unused_tags()
        # CSVに保存
        self.save_tasks()

    def get_selected_task_ids(self):
        """チェックボックスで選択されたタスクのIDを取得"""
        selected_ids = []
        
        # 一覧タブのチェックボックス
        for item in self.task_tree.get_children():
            values = self.task_tree.item(item, 'values')
            if values and values[0] == "☑":
                task_name = values[3]  # タスク名は4番目の列
                for t in self.view_tasks:
                    if t["name"] == task_name:
                        selected_ids.append(t["id"])
                        break
        
        # 今日タブのチェックボックス
        for item in self.today_tree.get_children():
            values = self.today_tree.item(item, 'values')
            if values and values[0] == "☑":
                task_name = values[3]  # タスク名は4番目の列
                for t in self.view_today_tasks:
                    if t["name"] == task_name:
                        selected_ids.append(t["id"])
                        break
        
        # 完了タブのチェックボックス
        for item in self.completed_tree.get_children():
            values = self.completed_tree.item(item, 'values')
            if values and values[0] == "☑":
                task_name = values[3]  # タスク名は4番目の列
                for t in self.view_completed_tasks:
                    if t["name"] == task_name:
                        selected_ids.append(t["id"])
                        break
        
        return selected_ids

    def delete_task(self):
        selected_task_ids = self.get_selected_task_ids()
        if not selected_task_ids:
            messagebox.showwarning("選択エラー", "削除するタスクを選択してください。")
            return
        
        if not messagebox.askyesno("確認", f"選択された{len(selected_task_ids)}個のタスクを削除しますか？"):
            return

        # マスターリストからIDでタスクを検索して削除
        self.tasks = [t for t in self.tasks if t["id"] not in selected_task_ids]
        
        self._clear_inputs()
        self.apply_filters_and_sort()
        # 未使用タグをクリーンアップ
        self.cleanup_unused_tags()
        # CSVに保存
        self.save_tasks()

    def update_task(self):
        new_name = self.task_entry.get().strip()
        if not new_name:
            messagebox.showwarning("入力エラー", "タスク名を入力してください。")
            return
            
        due_date = self.due_date_entry.get_date()
        if due_date:
            due_date_str = due_date.strftime("%Y-%m-%d")
        else:
            due_date_str = ""

        # どのタブでタスクが選択されているかチェック
        selected_items = self.task_tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            values = self.task_tree.item(selected_item, 'values')
            if values:
                task_name = values[3]  # タスク名は4番目の列
                selected_task_id = None
                for t in self.view_tasks:
                    if t["name"] == task_name:
                        selected_task_id = t["id"]
                        break
        else:
            selected_items = self.today_tree.selection()
            if selected_items:
                selected_item = selected_items[0]
                values = self.today_tree.item(selected_item, 'values')
                if values:
                    task_name = values[3]  # タスク名は4番目の列
                    selected_task_id = None
                    for t in self.view_today_tasks:
                        if t["name"] == task_name:
                            selected_task_id = t["id"]
                            break
            else:
                selected_items = self.completed_tree.selection()
                if selected_items:
                    selected_item = selected_items[0]
                    values = self.completed_tree.item(selected_item, 'values')
                    if values:
                        task_name = values[3]  # タスク名は4番目の列
                        selected_task_id = None
                        for t in self.view_completed_tasks:
                            if t["name"] == task_name:
                                selected_task_id = t["id"]
                                break
                else:
                    messagebox.showwarning("選択エラー", "更新するタスクを選択してください。")
                    return
        
        if not selected_task_id:
            messagebox.showwarning("選択エラー", "更新するタスクを選択してください。")
            return
        
        # マスターリストからIDでタスクを検索して更新
        for task in self.tasks:
            if task["id"] == selected_task_id:
                task["name"] = new_name
                task["priority"] = self.priority_var.get()
                task["due_date"] = due_date_str
                task["tags"] = self.tags_var.get()
                task["today"] = self.today_var.get()
                break
        
        self.apply_filters_and_sort()
        # 新しいタグを保存
        self.extract_tags_from_tasks()
        # 未使用タグをクリーンアップ
        self.cleanup_unused_tags()
        # CSVに保存
        self.save_tasks()

    def toggle_task_status(self):
        selected_task_ids = self.get_selected_task_ids()
        if not selected_task_ids:
            messagebox.showwarning("選択エラー", "状態を変更するタスクを選択してください。")
            return

        # マスターリストからIDでタスクを検索して状態を切り替え
        for task in self.tasks:
            if task["id"] in selected_task_ids:
                task["status"] = "完了" if task["status"] == "未着手" else "未着手"
        
        self.apply_filters_and_sort()
        # CSVに保存
        self.save_tasks()

    def toggle_today_status(self):
        selected_task_ids = self.get_selected_task_ids()
        if not selected_task_ids:
            messagebox.showwarning("選択エラー", "タスクを選択してください。")
            return

        # マスターリストからIDでタスクを検索して今日やる属性を切り替え
        for task in self.tasks:
            if task["id"] in selected_task_ids:
                task["today"] = TODAY_OPTIONS[0] if task["today"] == TODAY_OPTIONS[1] else TODAY_OPTIONS[1]
        
        self.apply_filters_and_sort()
        # CSVに保存
        self.save_tasks()

    def on_tags_input(self, event):
        """タグ入力時の処理"""
        # 入力されたテキストを取得
        input_text = self.tags_var.get().strip()
        if input_text:
            # カンマで区切られたタグを分割
            new_tags = [tag.strip() for tag in input_text.split(',') if tag.strip()]
            # 新しいタグを既存のタグリストに追加
            for tag in new_tags:
                if tag not in self.tags:
                    self.tags.append(tag)
            # タグリストを更新
            self.update_tags_list()
            # タグを保存
            self.save_tags()

    def on_tags_selected(self, event):
        """タグ選択時の処理"""
        # 選択されたタグを取得
        selected_tag = self.tags_var.get()
        if selected_tag:
            # 選択されたタグが既存のタグリストにない場合は追加
            if selected_tag not in self.tags:
                self.tags.append(selected_tag)
                self.update_tags_list()
                self.save_tags()

    def load_tags(self):
        """タグファイルからタグを読み込む"""
        self.tags = []
        
        # データフォルダが存在しない場合は作成
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
            
        if not os.path.exists(self.tags_file):
            return

        try:
            with open(self.tags_file, 'r', encoding='utf-8') as f:
                for line in f:
                    tag = line.strip()
                    if tag and tag not in self.tags:
                        self.tags.append(tag)
        except Exception as e:
            messagebox.showerror("エラー", f"タグファイルの読み込みに失敗しました: {e}")
            self.tags = []
        
        self.update_tags_list()

    def save_tags(self):
        """現在のタグリストをファイルに保存する"""
        # データフォルダが存在しない場合は作成
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
            
        try:
            with open(self.tags_file, 'w', encoding='utf-8') as f:
                for tag in self.tags:
                    f.write(f"{tag}\n")
        except IOError as e:
            messagebox.showerror("エラー", f"タグファイルへの保存に失敗しました: {e}")

    def update_tags_list(self):
        """タグのコンボボックスリストを更新する"""
        self.tags_combo['values'] = self.tags

    def extract_tags_from_tasks(self):
        """既存のタスクからタグを抽出してタグリストを更新する"""
        for task in self.tasks:
            if task.get("tags"):
                tags = [tag.strip() for tag in task["tags"].split(',') if tag.strip()]
                for tag in tags:
                    if tag not in self.tags:
                        self.tags.append(tag)
        self.update_tags_list()
        self.save_tags()

    def cleanup_unused_tags(self):
        """利用されていないタグを削除する"""
        # 現在使用されているタグを収集
        used_tags = set()
        for task in self.tasks:
            if task.get("tags"):
                tags = [tag.strip() for tag in task["tags"].split(',') if tag.strip()]
                used_tags.update(tags)
        
        # 使用されていないタグを削除
        self.tags = [tag for tag in self.tags if tag in used_tags]
        self.update_tags_list()
        self.save_tags()

    def add_or_update_task(self):
        # どのタブでもタスクが選択されているかチェック
        selected_items = self.task_tree.selection()
        if not selected_items:
            selected_items = self.today_tree.selection()
        if not selected_items:
            selected_items = self.completed_tree.selection()
        
        if selected_items:
            self.update_task()
        else:
            self.add_task()

    def clear_inputs(self):
        """入力フィールドをクリアする"""
        self._clear_inputs()
        self.apply_filters_and_sort()

    def show_settings(self):
        """設定ウィンドウを表示する"""
        settings_window = SettingsWindow(self.root, self.data_folder)
        new_data_folder = settings_window.show()
        
        if new_data_folder and new_data_folder != self.data_folder:
            self.data_folder = new_data_folder
            self.data_file = os.path.join(self.data_folder, "tasks.csv")
            self.tags_file = os.path.join(self.data_folder, "tags.txt")
            
            # データを再読み込み
            self.load_tags()
            self.load_tasks()

    def on_tree_click(self, event):
        """一覧タブのTreeviewクリック時の処理"""
        region = self.task_tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.task_tree.identify_column(event.x)
            if column == "#1":  # 選択列
                item = self.task_tree.identify_row(event.y)
                if item:
                    self._toggle_checkbox(self.task_tree, item, self.view_tasks)
    
    def on_completed_tree_click(self, event):
        """完了タブのTreeviewクリック時の処理"""
        region = self.completed_tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.completed_tree.identify_column(event.x)
            if column == "#1":  # 選択列
                item = self.completed_tree.identify_row(event.y)
                if item:
                    self._toggle_checkbox(self.completed_tree, item, self.view_completed_tasks)
    
    def on_today_tree_click(self, event):
        """今日タブのTreeviewクリック時の処理"""
        region = self.today_tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.today_tree.identify_column(event.x)
            if column == "#1":  # 選択列
                item = self.today_tree.identify_row(event.y)
                if item:
                    self._toggle_checkbox(self.today_tree, item, self.view_today_tasks)
    
    def _toggle_checkbox(self, tree, item, task_list):
        """チェックボックスの状態を切り替える（CSVには保存しない）"""
        values = list(tree.item(item, 'values'))
        
        # チェックボックスの状態を切り替え
        if values[0] == "□":
            values[0] = "☑"
        else:
            values[0] = "□"
        
        tree.item(item, values=values)

def on_closing(app):
    """アプリケーション終了時の処理"""
    app.save_tasks()
    app.save_tags()  # タグも保存
    app.root.destroy()

# --- アプリケーションの実行 ---
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = TaskApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(app))
    root.mainloop()

