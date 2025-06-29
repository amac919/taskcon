#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
taskcon 単体テスト
"""

import unittest
import os
import tempfile
import shutil
from datetime import datetime, date
import tkinter as tk
from unittest.mock import patch, MagicMock

# テスト用のモックTkinterDnD
class MockTkinterDnD:
    class Tk:
        def __init__(self):
            pass

# モックを設定
import sys
sys.modules['tkinterdnd2'] = MockTkinterDnD()

# テスト用のモックtkcalendar
class MockDateEntry:
    def __init__(self, *args, **kwargs):
        self._date = None
    
    def get_date(self):
        return self._date
    
    def set_date(self, date_obj):
        self._date = date_obj

sys.modules['tkcalendar'] = MagicMock()
sys.modules['tkcalendar'].DateEntry = MockDateEntry

# メインアプリケーションをインポート
from main import TaskApp, SettingsWindow, CSV_HEADERS, PRIORITY_LEVELS, STATUS_OPTIONS, SORT_OPTIONS, TODAY_OPTIONS


class TestTaskDataStructure(unittest.TestCase):
    """タスクデータ構造のテスト"""
    
    def test_task_structure(self):
        """タスクデータ構造が正しいことを確認"""
        task = {
            "id": "test-id",
            "name": "テストタスク",
            "status": "未着手",
            "priority": "中",
            "due_date": "2024-01-01",
            "tags": "テスト,タスク",
            "today": "〇"
        }
        
        # 必須フィールドの存在確認
        required_fields = ["id", "name", "status", "priority", "due_date", "tags", "today"]
        for field in required_fields:
            self.assertIn(field, task)
        
        # 値の型確認
        self.assertIsInstance(task["id"], str)
        self.assertIsInstance(task["name"], str)
        self.assertIn(task["status"], ["未着手", "完了"])
        self.assertIn(task["priority"], PRIORITY_LEVELS)
        self.assertIn(task["today"], TODAY_OPTIONS)


class TestConstants(unittest.TestCase):
    """定数のテスト"""
    
    def test_priority_levels(self):
        """優先度レベルの確認"""
        self.assertEqual(PRIORITY_LEVELS, ["高", "中", "低"])
    
    def test_status_options(self):
        """状態オプションの確認"""
        self.assertEqual(STATUS_OPTIONS, ["すべて", "未着手", "完了"])
    
    def test_sort_options(self):
        """ソートオプションの確認"""
        self.assertEqual(SORT_OPTIONS, ["追加順", "期限順", "優先度順", "タグ順"])
    
    def test_today_options(self):
        """今日やるオプションの確認"""
        self.assertEqual(TODAY_OPTIONS, ["〇", ""])


class TestTaskApp(unittest.TestCase):
    """TaskAppクラスのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.root = tk.Tk()
        self.root.withdraw()  # ウィンドウを非表示
        
        # テスト用のデータフォルダを作成
        self.test_data_folder = os.path.join(self.temp_dir, "test_data")
        os.makedirs(self.test_data_folder, exist_ok=True)
        
        # テスト用のアプリケーションインスタンスを作成
        with patch('main.DEFAULT_DATA_FOLDER', self.test_data_folder):
            self.app = TaskApp(self.root)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.root.destroy()
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """初期化のテスト"""
        self.assertIsNotNone(self.app.tasks)
        self.assertIsNotNone(self.app.tags)
        self.assertEqual(self.app.data_folder, self.test_data_folder)
        self.assertEqual(self.app.data_file, os.path.join(self.test_data_folder, "tasks.csv"))
        self.assertEqual(self.app.tags_file, os.path.join(self.test_data_folder, "tags.txt"))
    
    def test_add_task(self):
        """タスク追加のテスト"""
        # テスト用のタスクデータを設定
        self.app.task_entry.insert(0, "テストタスク")
        self.app.priority_var.set("高")
        self.app.tags_var.set("テスト")
        self.app.today_var.set("〇")
        
        # タスクを追加
        initial_count = len(self.app.tasks)
        self.app.add_task()
        
        # タスクが追加されたことを確認
        self.assertEqual(len(self.app.tasks), initial_count + 1)
        
        # 追加されたタスクの内容を確認
        added_task = self.app.tasks[-1]
        self.assertEqual(added_task["name"], "テストタスク")
        self.assertEqual(added_task["priority"], "高")
        self.assertEqual(added_task["tags"], "テスト")
        self.assertEqual(added_task["today"], "〇")
        self.assertEqual(added_task["status"], "未着手")
    
    def test_delete_task(self):
        """タスク削除のテスト"""
        # テスト用のタスクを追加
        test_task = {
            "id": "test-id",
            "name": "削除テストタスク",
            "status": "未着手",
            "priority": "中",
            "due_date": "",
            "tags": "",
            "today": ""
        }
        self.app.tasks.append(test_task)
        
        # 削除対象のタスクをview_tasksに設定
        self.app.view_tasks = [test_task]
        
        # モックでチェックボックスを選択状態にする
        with patch.object(self.app, 'get_selected_task_ids', return_value=["test-id"]):
            with patch('tkinter.messagebox.askyesno', return_value=True):
                initial_count = len(self.app.tasks)
                self.app.delete_task()
                
                # タスクが削除されたことを確認
                self.assertEqual(len(self.app.tasks), initial_count - 1)
    
    def test_toggle_task_status(self):
        """タスク状態切り替えのテスト"""
        # テスト用のタスクを追加
        test_task = {
            "id": "test-id",
            "name": "状態切り替えテスト",
            "status": "未着手",
            "priority": "中",
            "due_date": "",
            "tags": "",
            "today": ""
        }
        self.app.tasks.append(test_task)
        
        # モックでチェックボックスを選択状態にする
        with patch.object(self.app, 'get_selected_task_ids', return_value=["test-id"]):
            # 未着手から完了に切り替え
            self.app.toggle_task_status()
            self.assertEqual(test_task["status"], "完了")
            
            # 完了から未着手に切り替え
            self.app.toggle_task_status()
            self.assertEqual(test_task["status"], "未着手")
    
    def test_toggle_today_status(self):
        """今日やる状態切り替えのテスト"""
        # テスト用のタスクを追加
        test_task = {
            "id": "test-id",
            "name": "今日やるテスト",
            "status": "未着手",
            "priority": "中",
            "due_date": "",
            "tags": "",
            "today": ""
        }
        self.app.tasks.append(test_task)
        
        # モックでチェックボックスを選択状態にする
        with patch.object(self.app, 'get_selected_task_ids', return_value=["test-id"]):
            # 空から〇に切り替え
            self.app.toggle_today_status()
            self.assertEqual(test_task["today"], "〇")
            
            # 〇から空に切り替え
            self.app.toggle_today_status()
            self.assertEqual(test_task["today"], "")
    
    def test_apply_filters_and_sort(self):
        """フィルタリングとソートのテスト"""
        # テスト用のタスクを追加
        test_tasks = [
            {
                "id": "1",
                "name": "タスクA",
                "status": "未着手",
                "priority": "高",
                "due_date": "2024-01-01",
                "tags": "テスト",
                "today": ""
            },
            {
                "id": "2",
                "name": "タスクB",
                "status": "完了",
                "priority": "中",
                "due_date": "2024-01-02",
                "tags": "完了",
                "today": "〇"
            },
            {
                "id": "3",
                "name": "タスクC",
                "status": "未着手",
                "priority": "低",
                "due_date": "2024-01-03",
                "tags": "今日",
                "today": "〇"
            }
        ]
        self.app.tasks = test_tasks
        
        # 一覧タブのフィルタリングテスト
        with patch.object(self.app.notebook, 'tab', return_value="一覧"):
            self.app.apply_filters_and_sort()
            # 一覧タブには未完了かつ今日やるフラグがOFFのタスクのみ表示
            self.assertEqual(len(self.app.view_tasks), 1)
            self.assertEqual(self.app.view_tasks[0]["name"], "タスクA")
        
        # 今日タブのフィルタリングテスト
        with patch.object(self.app.notebook, 'tab', return_value="今日"):
            self.app.apply_filters_and_sort()
            # 今日タブには今日やるフラグがONの未完了タスクのみ表示
            self.assertEqual(len(self.app.view_today_tasks), 1)
            self.assertEqual(self.app.view_today_tasks[0]["name"], "タスクC")
        
        # 完了タブのフィルタリングテスト
        with patch.object(self.app.notebook, 'tab', return_value="完了"):
            self.app.apply_filters_and_sort()
            # 完了タブには完了状態のタスクのみ表示
            self.assertEqual(len(self.app.view_completed_tasks), 1)
            self.assertEqual(self.app.view_completed_tasks[0]["name"], "タスクB")
    
    def test_search_filter(self):
        """検索フィルターのテスト"""
        # テスト用のタスクを追加
        test_tasks = [
            {
                "id": "1",
                "name": "Pythonタスク",
                "status": "未着手",
                "priority": "高",
                "due_date": "",
                "tags": "プログラミング",
                "today": ""
            },
            {
                "id": "2",
                "name": "Javaタスク",
                "status": "未着手",
                "priority": "中",
                "due_date": "",
                "tags": "プログラミング",
                "today": ""
            }
        ]
        self.app.tasks = test_tasks
        self.app.view_tasks = test_tasks
        
        # タスク名での検索
        self.app.search_entry.insert(0, "Python")
        self.app.apply_filters_and_sort()
        self.assertEqual(len(self.app.view_tasks), 1)
        self.assertEqual(self.app.view_tasks[0]["name"], "Pythonタスク")
        
        # タグでの検索
        self.app.search_entry.delete(0, tk.END)
        self.app.search_entry.insert(0, "プログラミング")
        self.app.apply_filters_and_sort()
        self.assertEqual(len(self.app.view_tasks), 2)
    
    def test_sort_functionality(self):
        """ソート機能のテスト"""
        # テスト用のタスクを追加
        test_tasks = [
            {
                "id": "1",
                "name": "タスクA",
                "status": "未着手",
                "priority": "低",
                "due_date": "2024-01-03",
                "tags": "C",
                "today": ""
            },
            {
                "id": "2",
                "name": "タスクB",
                "status": "未着手",
                "priority": "高",
                "due_date": "2024-01-01",
                "tags": "A",
                "today": ""
            },
            {
                "id": "3",
                "name": "タスクC",
                "status": "未着手",
                "priority": "中",
                "due_date": "2024-01-02",
                "tags": "B",
                "today": ""
            }
        ]
        self.app.tasks = test_tasks
        self.app.view_tasks = test_tasks
        
        # 優先度順でソート
        self.app.sort_var.set("優先度順")
        self.app.apply_filters_and_sort()
        self.assertEqual(self.app.view_tasks[0]["priority"], "高")
        self.assertEqual(self.app.view_tasks[1]["priority"], "中")
        self.assertEqual(self.app.view_tasks[2]["priority"], "低")
        
        # 期限順でソート
        self.app.sort_var.set("期限順")
        self.app.apply_filters_and_sort()
        self.assertEqual(self.app.view_tasks[0]["due_date"], "2024-01-01")
        self.assertEqual(self.app.view_tasks[1]["due_date"], "2024-01-02")
        self.assertEqual(self.app.view_tasks[2]["due_date"], "2024-01-03")
        
        # タグ順でソート
        self.app.sort_var.set("タグ順")
        self.app.apply_filters_and_sort()
        self.assertEqual(self.app.view_tasks[0]["tags"], "A")
        self.assertEqual(self.app.view_tasks[1]["tags"], "B")
        self.assertEqual(self.app.view_tasks[2]["tags"], "C")


class TestSettingsWindow(unittest.TestCase):
    """SettingsWindowクラスのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.root = tk.Tk()
        self.root.withdraw()  # ウィンドウを非表示
        self.test_data_folder = "/test/path"
        self.settings_window = SettingsWindow(self.root, self.test_data_folder)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.root.destroy()
    
    def test_initialization(self):
        """初期化のテスト"""
        self.assertEqual(self.settings_window.data_folder, self.test_data_folder)
        self.assertEqual(self.settings_window.result_data_folder, self.test_data_folder)
    
    def test_ok_clicked(self):
        """OKボタンクリックのテスト"""
        new_folder = "/new/test/path"
        self.settings_window.data_folder_var.set(new_folder)
        self.settings_window._ok_clicked()
        self.assertEqual(self.settings_window.result_data_folder, new_folder)
    
    def test_cancel_clicked(self):
        """キャンセルボタンクリックのテスト"""
        self.settings_window.data_folder_var.set("/different/path")
        self.settings_window._cancel_clicked()
        # キャンセル時は元の値が保持される
        self.assertEqual(self.settings_window.result_data_folder, self.test_data_folder)


class TestDataPersistence(unittest.TestCase):
    """データ永続化のテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_folder = os.path.join(self.temp_dir, "test_data")
        os.makedirs(self.test_data_folder, exist_ok=True)
        
        self.root = tk.Tk()
        self.root.withdraw()
        
        with patch('main.DEFAULT_DATA_FOLDER', self.test_data_folder):
            self.app = TaskApp(self.root)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.root.destroy()
        shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_tasks(self):
        """タスクの保存と読み込みのテスト"""
        # テスト用のタスクを追加
        test_task = {
            "id": "test-id",
            "name": "保存テストタスク",
            "status": "未着手",
            "priority": "高",
            "due_date": "2024-01-01",
            "tags": "テスト",
            "today": "〇"
        }
        self.app.tasks.append(test_task)
        
        # タスクを保存
        self.app.save_tasks()
        
        # ファイルが作成されたことを確認
        self.assertTrue(os.path.exists(self.app.data_file))
        
        # 新しいアプリケーションインスタンスで読み込み
        with patch('main.DEFAULT_DATA_FOLDER', self.test_data_folder):
            new_app = TaskApp(self.root)
            
            # タスクが正しく読み込まれたことを確認
            self.assertEqual(len(new_app.tasks), 1)
            loaded_task = new_app.tasks[0]
            self.assertEqual(loaded_task["name"], "保存テストタスク")
            self.assertEqual(loaded_task["status"], "未着手")
            self.assertEqual(loaded_task["priority"], "高")
            self.assertEqual(loaded_task["due_date"], "2024-01-01")
            self.assertEqual(loaded_task["tags"], "テスト")
            self.assertEqual(loaded_task["today"], "〇")
    
    def test_save_and_load_tags(self):
        """タグの保存と読み込みのテスト"""
        # テスト用のタグを追加
        test_tags = ["タグ1", "タグ2", "タグ3"]
        self.app.tags = test_tags
        
        # タグを保存
        self.app.save_tags()
        
        # ファイルが作成されたことを確認
        self.assertTrue(os.path.exists(self.app.tags_file))
        
        # 新しいアプリケーションインスタンスで読み込み
        with patch('main.DEFAULT_DATA_FOLDER', self.test_data_folder):
            new_app = TaskApp(self.root)
            
            # タグが正しく読み込まれたことを確認
            self.assertEqual(len(new_app.tags), 3)
            self.assertIn("タグ1", new_app.tags)
            self.assertIn("タグ2", new_app.tags)
            self.assertIn("タグ3", new_app.tags)


class TestTagManagement(unittest.TestCase):
    """タグ管理のテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_folder = os.path.join(self.temp_dir, "test_data")
        os.makedirs(self.test_data_folder, exist_ok=True)
        
        self.root = tk.Tk()
        self.root.withdraw()
        
        with patch('main.DEFAULT_DATA_FOLDER', self.test_data_folder):
            self.app = TaskApp(self.root)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.root.destroy()
        shutil.rmtree(self.temp_dir)
    
    def test_extract_tags_from_tasks(self):
        """タスクからのタグ抽出テスト"""
        # テスト用のタスクを追加
        test_tasks = [
            {
                "id": "1",
                "name": "タスク1",
                "status": "未着手",
                "priority": "高",
                "due_date": "",
                "tags": "タグ1,タグ2",
                "today": ""
            },
            {
                "id": "2",
                "name": "タスク2",
                "status": "未着手",
                "priority": "中",
                "due_date": "",
                "tags": "タグ2,タグ3",
                "today": ""
            }
        ]
        self.app.tasks = test_tasks
        
        # タグを抽出
        self.app.extract_tags_from_tasks()
        
        # 重複なしでタグが抽出されたことを確認
        expected_tags = ["タグ1", "タグ2", "タグ3"]
        self.assertEqual(set(self.app.tags), set(expected_tags))
    
    def test_cleanup_unused_tags(self):
        """未使用タグのクリーンアップテスト"""
        # 初期タグを設定
        self.app.tags = ["使用中", "未使用1", "未使用2"]
        
        # テスト用のタスクを追加（使用中のタグのみ使用）
        test_tasks = [
            {
                "id": "1",
                "name": "タスク1",
                "status": "未着手",
                "priority": "高",
                "due_date": "",
                "tags": "使用中",
                "today": ""
            }
        ]
        self.app.tasks = test_tasks
        
        # 未使用タグをクリーンアップ
        self.app.cleanup_unused_tags()
        
        # 未使用タグが削除されたことを確認
        self.assertEqual(self.app.tags, ["使用中"])


if __name__ == '__main__':
    # テストスイートを実行
    unittest.main(verbosity=2) 