@echo off
echo ========================================
echo taskcon アプリケーション起動
echo ========================================
echo.

echo Pythonのバージョンを確認しています...
python --version
if %errorlevel% neq 0 (
    echo エラー: Pythonがインストールされていません。
    echo まず install_dependencies.bat を実行してください。
    pause
    exit /b 1
)

echo.
echo taskcon を起動しています...
python main.py

if %errorlevel% neq 0 (
    echo.
    echo エラー: アプリケーションの起動に失敗しました。
    echo 必要なライブラリがインストールされているか確認してください。
    echo install_dependencies.bat を実行してください。
    pause
) 