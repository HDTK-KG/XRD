import os
import json
import pandas as pd


def ras2json(ras_filepath):
    """
    RASファイルのヘッダー部分（*RAS_INT_STARTまで）をJSONに変換する関数
    
    Args:
        ras_filepath (str): RASファイルのパス
        
    Returns:
        dict: ヘッダー情報を含む辞書
    """
    header_data = {}
    
    with open(ras_filepath, 'r', encoding='utf-8', errors='ignore') as file:
        lines = file.readlines()
    
    # ヘッダー部分のみを処理
    in_header = False
    for line in lines:
        line = line.strip()
        
        if line == '*RAS_HEADER_START':
            in_header = True
            continue
        elif line == '*RAS_HEADER_END':
            in_header = False
            continue
        elif line == '*RAS_INT_START':
            break
            
        # ヘッダー行を処理
        if line.startswith('*') and ' ' in line:
            # キーと値を分離
            parts = line.split(' ', 1)
            key = parts[0][1:]  # 先頭の*を除去
            value = parts[1].strip('"')  # クォートを除去
            header_data[key] = value
    
    return header_data


def ras2csv(ras_filepath):
    """
    RASファイルのデータ部分（*RAS_INT_START以降）をCSVに変換する関数
    
    Args:
        ras_filepath (str): RASファイルのパス
        
    Returns:
        pandas.DataFrame: two_theta, intensity, timeの列を持つDataFrame
    """
    data_lines = []
    
    with open(ras_filepath, 'r', encoding='utf-8', errors='ignore') as file:
        lines = file.readlines()
    
    # データ部分を探す
    data_started = False
    for line in lines:
        line = line.strip()
        
        if line == '*RAS_INT_START':
            data_started = True
            continue
        elif line == '*RAS_INT_END':
            break
            
        if data_started and line:
            # データ行を処理（3列のデータ）
            parts = line.split()
            if len(parts) >= 3:
                try:
                    two_theta = float(parts[0])
                    intensity = float(parts[1])
                    time = float(parts[2])
                    data_lines.append([two_theta, intensity, time])
                except ValueError:
                    # 数値に変換できない行はスキップ
                    continue
    
    # DataFrameを作成
    df = pd.DataFrame(data_lines, columns=['two_theta', 'intensity', 'time'])
    return df


def ras2csv_json(ras_filepath):
    """
    RASファイルをJSONとCSVに変換し、それぞれファイルに保存する関数
    
    Args:
        ras_filepath (str): RASファイルのパス
        
    Returns:
        tuple: (json_filepath, csv_filepath) 作成されたファイルのパス
    """
    # ファイル名の基本部分を取得
    base_name = os.path.splitext(ras_filepath)[0]
    
    # JSONファイルを作成
    header_data = ras2json(ras_filepath)
    json_filepath = base_name + '.json'
    with open(json_filepath, 'w', encoding='utf-8') as json_file:
        json.dump(header_data, json_file, indent=2, ensure_ascii=False)
    
    # CSVファイルを作成
    df = ras2csv(ras_filepath)
    csv_filepath = base_name + '.csv'
    df.to_csv(csv_filepath, index=False)
    
    print(f"JSONファイルを作成しました: {json_filepath}")
    print(f"CSVファイルを作成しました: {csv_filepath}")
    
    return json_filepath, csv_filepath


def ras2csv_json_all(folder_path):
    """
    指定フォルダ及びサブフォルダ内の全ての.rasファイルにras2csv_jsonを実行する関数
    
    Args:
        folder_path (str): 検索対象のフォルダパス
        
    Returns:
        list: 処理されたファイルの情報を含む辞書のリスト
            [{'ras_file': str, 'json_file': str, 'csv_file': str, 'success': bool, 'error': str}, ...]
    """
    results = []
    
    # フォルダが存在するかチェック
    if not os.path.exists(folder_path):
        print(f"❌ フォルダが見つかりません: {folder_path}")
        return results
    
    if not os.path.isdir(folder_path):
        print(f"❌ 指定されたパスはフォルダではありません: {folder_path}")
        return results
    
    print(f"📁 フォルダ内の.rasファイルを検索中: {folder_path}")
    
    # サブフォルダを含めて.rasファイルを再帰的に検索
    ras_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.ras'):
                ras_files.append(os.path.join(root, file))
    
    if not ras_files:
        print("📄 .rasファイルが見つかりませんでした")
        return results
    
    print(f"🔍 {len(ras_files)}個の.rasファイルを発見しました")
    
    # 各.rasファイルを処理
    for ras_file in ras_files:
        print(f"\n📄 処理中: {os.path.relpath(ras_file, folder_path)}")
        
        result = {
            'ras_file': ras_file,
            'json_file': None,
            'csv_file': None,
            'success': False,
            'error': None
        }
        
        try:
            json_path, csv_path = ras2csv_json(ras_file)
            result['json_file'] = json_path
            result['csv_file'] = csv_path
            result['success'] = True
            print(f"✅ 変換完了: {os.path.basename(json_path)}, {os.path.basename(csv_path)}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ エラーが発生しました: {e}")
        
        results.append(result)
    
    # 処理結果のサマリーを表示
    success_count = sum(1 for r in results if r['success'])
    error_count = len(results) - success_count
    
    print(f"\n📊 処理結果:")
    print(f"   ✅ 成功: {success_count}ファイル")
    print(f"   ❌ エラー: {error_count}ファイル")
    print(f"   📁 出力先: {folder_path}")
    
    return results


# メイン実行部分
if __name__ == "__main__":
    # 実行中のras2csv.pyが存在するディレクトリを取得
    current_dir = os.path.dirname(__file__)
    
    print("=" * 60)
    print("🔧 RAS to JSON/CSV 一括変換ツール")
    print("=" * 60)
    print(f"📁 検索対象ディレクトリ: {current_dir}")
    
    # 現在のディレクトリで全ての.rasファイルを処理
    results = ras2csv_json_all(current_dir)
    
    if results:
        print(f"\n" + "=" * 60)
        print("📋 詳細結果:")
        print("=" * 60)
        
        for i, result in enumerate(results, 1):
            status = "✅" if result['success'] else "❌"
            rel_path = os.path.relpath(result['ras_file'], current_dir)
            print(f"{i:2d}. {status} {rel_path}")
            
            if result['success']:
                json_name = os.path.basename(result['json_file'])
                csv_name = os.path.basename(result['csv_file'])
                print(f"     → {json_name}")
                print(f"     → {csv_name}")
            else:
                print(f"     エラー: {result['error']}")
            print()
    
    print("🎉 処理が完了しました！")
