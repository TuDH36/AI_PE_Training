"""
Đánh giá các đặc trưng quan trọng nhất của model CYAIPE32.mdl
Cấu trúc 1040 đặc trưng:
  - [0-774]    : Dữ liệu số từ PE header (getDataFloat, data_origin[:775])
      [0-291]   : PE header stats nhóm 1
      [292-547] : Byte frequency histogram (0x00-0xFF)
      [548-774] : PE header stats nhóm 2
  - [775-784]  : 10 Section slots (mã hoá từ PE32Section vocab)
  - [785-1039] : Binary presence của 255 API từ PE32DICT
"""

import pickle
import numpy as np
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

MODEL_PATH   = r"E:\AV\Train_AI_Python\Data_Preprocessing\CYAIPE32.mdl"
PE32DICT_PATH = r"E:\AV\Train_AI_Python\Data_Preprocessing\PE32DICT"
PE32SECT_PATH = r"E:\AV\Train_AI_Python\Data_Preprocessing\PE32Section"

# ──────────────────────────────────────────────
# 1. Load model
# ──────────────────────────────────────────────
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

num_features = model.num_feature()
print(f"Model: CYAIPE32.mdl  |  Tổng đặc trưng: {num_features}  |  Số cây: {model.num_trees()}")

# ──────────────────────────────────────────────
# 2. Xây dựng tên đặc trưng
# ──────────────────────────────────────────────

# Import API vocab (255 tokens)
with open(PE32DICT_PATH, "r", encoding="utf-8", errors="ignore") as f:
    import_vocab = f.read().strip().split()   # space-separated

# Section vocab (dùng để hiểu section slot)
with open(PE32SECT_PATH, "r", encoding="utf-8", errors="ignore") as f:
    section_vocab = f.read().strip().split()

# Đặt tên từng cột
feature_names = []

# [0-291] PE header stats nhóm 1
for i in range(292):
    feature_names.append(f"header1_{i:03d}")

# [292-547] Byte frequency histogram
for byte_val in range(256):
    feature_names.append(f"byte_freq_0x{byte_val:02X}")

# [548-774] PE header stats nhóm 2
for i in range(227):
    feature_names.append(f"header2_{i:03d}")

# [775-784] Section slots
for slot in range(10):
    feature_names.append(f"section_slot{slot}")

# [785-1039] Import API binary flags
for api in import_vocab[:255]:
    feature_names.append(f"api::{api}")

# Kiểm tra
assert len(feature_names) == num_features, \
    f"Mismatch: feature_names={len(feature_names)} vs model={num_features}"

# ──────────────────────────────────────────────
# 3. Tính feature importance (2 loại)
# ──────────────────────────────────────────────
imp_gain  = model.feature_importance(importance_type="gain")
imp_split = model.feature_importance(importance_type="split")

# Chuẩn hoá về phần trăm
pct_gain  = imp_gain  / imp_gain.sum()  * 100
pct_split = imp_split / imp_split.sum() * 100

# ──────────────────────────────────────────────
# 4. Phân loại đặc trưng theo nhóm
# ──────────────────────────────────────────────
GROUPS = {
    "PE Header 1 (field)":       range(0,   292),
    "Byte Histogram":            range(292, 548),
    "PE Header 2 (field)":       range(548, 775),
    "Section Slots":             range(775, 785),
    "Import API (binary flag)":  range(785, 1040),
}

print("\n" + "="*70)
print("ĐÓNG GÓP THEO NHÓM ĐẶC TRƯNG (importance_type=gain)")
print("="*70)
print(f"{'Nhóm':<35} {'Gain %':>8}  {'Split %':>8}  {'Số features':>12}")
print("-"*70)
for group, rng in GROUPS.items():
    idx = list(rng)
    g = pct_gain[idx].sum()
    s = pct_split[idx].sum()
    print(f"{group:<35} {g:>7.2f}%  {s:>7.2f}%  {len(idx):>12}")

# ──────────────────────────────────────────────
# 5. Top-N đặc trưng quan trọng nhất (gain)
# ──────────────────────────────────────────────
TOP_N = 50
order = np.argsort(imp_gain)[::-1]

print(f"\n{'='*70}")
print(f"TOP {TOP_N} ĐẶC TRƯNG QUAN TRỌNG NHẤT (theo Gain)")
print(f"{'='*70}")
print(f"{'Rank':<5} {'Feature':<50} {'Gain %':>8}  {'Split %':>8}")
print("-"*70)
for rank, idx in enumerate(order[:TOP_N], 1):
    print(f"{rank:<5} {feature_names[idx]:<50} {pct_gain[idx]:>7.3f}%  {pct_split[idx]:>7.3f}%")

# ──────────────────────────────────────────────
# 6. Top Import APIs
# ──────────────────────────────────────────────
api_indices  = list(range(785, 785 + len(import_vocab[:255])))
api_gain     = [(feature_names[i], pct_gain[i], pct_split[i]) for i in api_indices]
api_gain_srt = sorted(api_gain, key=lambda x: x[1], reverse=True)

print(f"\n{'='*70}")
print(f"TOP 30 IMPORT API QUAN TRỌNG NHẤT (theo Gain)")
print(f"{'='*70}")
print(f"{'Rank':<5} {'API':<50} {'Gain %':>8}  {'Split %':>8}")
print("-"*70)
for rank, (name, g, s) in enumerate(api_gain_srt[:30], 1):
    print(f"{rank:<5} {name:<50} {g:>7.3f}%  {s:>7.3f}%")

# ──────────────────────────────────────────────
# 7. Top Section Slots
# ──────────────────────────────────────────────
sect_indices = list(range(775, 785))
sect_gain    = [(feature_names[i], pct_gain[i], pct_split[i]) for i in sect_indices]
sect_gain_srt = sorted(sect_gain, key=lambda x: x[1], reverse=True)

print(f"\n{'='*70}")
print(f"SECTION SLOTS (theo Gain)")
print(f"{'='*70}")
print(f"{'Feature':<20} {'Gain %':>8}  {'Split %':>8}")
print("-"*40)
for name, g, s in sect_gain_srt:
    print(f"{name:<20} {g:>7.3f}%  {s:>7.3f}%")

# ──────────────────────────────────────────────
# 8. Top Byte Histogram bytes
# ──────────────────────────────────────────────
byte_indices  = list(range(292, 548))
byte_gain     = [(feature_names[i], pct_gain[i], pct_split[i]) for i in byte_indices]
byte_gain_srt = sorted(byte_gain, key=lambda x: x[1], reverse=True)

print(f"\n{'='*70}")
print(f"TOP 20 BYTE HISTOGRAM QUAN TRỌNG NHẤT (theo Gain)")
print(f"{'='*70}")
print(f"{'Rank':<5} {'Byte':<25} {'Gain %':>8}  {'Split %':>8}")
print("-"*50)
for rank, (name, g, s) in enumerate(byte_gain_srt[:20], 1):
    print(f"{rank:<5} {name:<25} {g:>7.3f}%  {s:>7.3f}%")

# ──────────────────────────────────────────────
# 9. Lưu kết quả ra file CSV
# ──────────────────────────────────────────────
out_path = r"E:\AV\Train_AI_Python\Data_Preprocessing\feature_importance_PE32.csv"
with open(out_path, "w", encoding="utf-8") as f:
    f.write("rank,feature_name,group,gain_pct,split_pct\n")
    for rank, idx in enumerate(order, 1):
        name = feature_names[idx]
        # xác định nhóm
        grp = "Unknown"
        for g, rng in GROUPS.items():
            if idx in rng:
                grp = g
                break
        f.write(f"{rank},{name},{grp},{pct_gain[idx]:.6f},{pct_split[idx]:.6f}\n")

print(f"\n[OK] Da luu toan bo bang xep hang vao: {out_path}")
