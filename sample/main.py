import os, sys
#utilsフォルダを自動検出してパスを通す

import ras2csv
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import importlib

importlib.reload(ras2csv)

# 現在のディレクトリ（sampleフォルダ）を指定して一括変換を実行
current_folder = os.getcwd()
print(f"📁 対象フォルダ: {current_folder}")
print()

# フォルダ内の全ての.rasファイルを一括変換
results = ras2csv.ras2csv_json_all(current_folder)