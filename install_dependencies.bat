@echo off
echo ========================================
echo taskcon 依存関係インストールスクリプト
echo ========================================
echo.

echo Pythonのバージョンを確認しています...
python --version
if %errorlevel% neq 0 (
    echo エラー: Pythonがインストールされていません。
    echo Python 3.7以上をインストールしてください: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo 必要なライブラリをインストールしています...
echo.

echo 1. tkcalendar をインストール中...
pip install tkcalendar
if %errorlevel% neq 0 (
    echo エラー: tkcalendar のインストールに失敗しました。
    pause
    exit /b 1
)

echo 2. tkinterdnd2 をインストール中...
pip install tkinterdnd2
if %errorlevel% neq 0 (
    echo エラー: tkinterdnd2 のインストールに失敗しました。
    pause
    exit /b 1
)

echo.
echo ========================================
echo インストール完了！
echo ========================================
echo.
echo 以下のライブラリがインストールされました:
echo - tkcalendar: カレンダーウィジェット
echo - tkinterdnd2: ドラッグ&ドロップ機能
echo.
echo アプリケーションを起動するには:
echo python main.py
echo.
pause 