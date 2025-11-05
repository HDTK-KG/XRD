"""
XRDプロジェクト用のパス設定モジュール
このファイルをインポートするだけで、utilsモジュールが利用可能になります。
"""

import os
import sys
from pathlib import Path

def setup_project_paths():
    """プロジェクトのパスを設定してutilsモジュールを利用可能にする"""
    
    # このファイルの場所からプロジェクトルートを取得
    current_file = Path(__file__).resolve()
    project_root = current_file.parent
    
    # utilsディレクトリのパス
    utils_path = project_root / 'utils'
    
    # sys.pathに追加（重複チェック付き）
    utils_path_str = str(utils_path)
    if utils_path_str not in sys.path:
        sys.path.insert(0, utils_path_str)
    
    # プロジェクトルートもパスに追加（必要に応じて）
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    
    return {
        'project_root': project_root_str,
        'utils_path': utils_path_str
    }

# モジュールがインポートされた時点で自動実行
_paths = setup_project_paths()

# 便利な変数として提供
PROJECT_ROOT = _paths['project_root']
UTILS_PATH = _paths['utils_path']

# インポート成功の確認
try:
    import ras2csv
    print(f"✅ XRDプロジェクトの設定が完了しました")
    print(f"   プロジェクトルート: {PROJECT_ROOT}")
    print(f"   utilsパス: {UTILS_PATH}")
except ImportError as e:
    print(f"⚠️  ras2csvのインポートに失敗しました: {e}")