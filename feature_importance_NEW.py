"""
Danh gia dac trung quan trong nhat cua CYAIPE32NEW.mdl
Cau truc 2725 dac trung:
  [0-774]    : PE header data (getDataFloat -> data_origin[:775])
      [0-291]   : header fields nhom 1
      [292-547] : Byte frequency histogram (0x00-0xFF)
      [548-774] : header fields nhom 2
  [775-784]  : 10 Section slots (PE32Section vocab)
  [785-2711] : 1927 Import tokens tu PE32D (binary presence, vectorize_import_features)
  [2712-2724]: 13 Handcrafted import features (HAND_KEYS)
"""

import sys, os
sys.stdout.reconfigure(encoding='utf-8')
import lightgbm as lgb
import numpy as np

MODEL_PATH    = r"E:\AV\Train_AI_Python\Data_Preprocessing\CYAIPE32NEW.mdl"
PE32D_PATH    = r"E:\AV\Train_AI_Python\Data_Preprocessing\PE32DICT"
PE32SECT_PATH = r"E:\AV\Train_AI_Python\Data_Preprocessing\PE32Section"

# ──────────────────────────────────────────────
# 1. Load model (text format)
# ──────────────────────────────────────────────
model = lgb.Booster(model_file=MODEL_PATH)
num_features = model.num_feature()
print(f"Model: CYAIPE32NEW.mdl  |  Tong dac trung: {num_features}  |  So cay: {model.num_trees()}")

# ──────────────────────────────────────────────
# 2. Xay dung ten dac trung
# ──────────────────────────────────────────────

# Import tokens tu PE32D (1927 tokens, moi dong 1 token)
with open(PE32D_PATH, "r", encoding="utf-8", errors="ignore") as f:
    pe32d_tokens = [l.strip() for l in f if l.strip()]

# Handcrafted keys (thu tu phai giong voi vectorize_import_features trong notebook)
HAND_KEYS = [
    'n_imports_total', 'n_dlls_total', 'n_ordinals_total',
    'cnt_crt_imports', 'ratio_crt',
    'cnt_dynload', 'cnt_mem', 'cnt_proc_enum', 'cnt_reg',
    'has_net_dll', 'has_crypto_dll',
    'has_dynload_and_mem', 'has_proc_enum_and_mem'
]

feature_names = []

# [0-291] PE header nhom 1
for i in range(292):
    feature_names.append(f"header1_{i:03d}")

# [292-547] Byte histogram
for b in range(256):
    feature_names.append(f"byte_freq_0x{b:02X}")

# [548-774] PE header nhom 2
for i in range(227):
    feature_names.append(f"header2_{i:03d}")

# [775-784] Section slots
for s in range(10):
    feature_names.append(f"section_slot{s}")

# [785-2711] Import tokens (PE32D)
for tok in pe32d_tokens:
    feature_names.append(f"import::{tok}")

# [2712-2724] Handcrafted import features
for k in HAND_KEYS:
    feature_names.append(f"handcraft::{k}")

assert len(feature_names) == num_features, \
    f"Mismatch: feature_names={len(feature_names)} vs model={num_features}"

# ──────────────────────────────────────────────
# 3. Tinh feature importance
# ──────────────────────────────────────────────
imp_gain  = model.feature_importance(importance_type="gain")
imp_split = model.feature_importance(importance_type="split")

pct_gain  = imp_gain  / imp_gain.sum()  * 100
pct_split = imp_split / imp_split.sum() * 100

# ──────────────────────────────────────────────
# 4. Dong gop theo nhom
# ──────────────────────────────────────────────
GROUPS = {
    "PE Header 1 (field)":       range(0,   292),
    "Byte Histogram":            range(292, 548),
    "PE Header 2 (field)":       range(548, 775),
    "Section Slots":             range(775, 785),
    "Import Token (PE32D)":      range(785, 2712),
    "Handcrafted Import Stats":  range(2712, 2725),
}

print("\n" + "="*75)
print("DONG GOP THEO NHOM DAC TRUNG  (importance_type=gain)")
print("="*75)
print(f"{'Nhom':<35} {'Gain %':>8}  {'Split %':>8}  {'So features':>12}")
print("-"*75)
for group, rng in GROUPS.items():
    idx = list(rng)
    g = pct_gain[idx].sum()
    s = pct_split[idx].sum()
    print(f"{group:<35} {g:>7.2f}%  {s:>7.2f}%  {len(idx):>12}")

# ──────────────────────────────────────────────
# 5. Top-50 dac trung (gain)
# ──────────────────────────────────────────────
TOP_N = 50
order = np.argsort(imp_gain)[::-1]

print(f"\n{'='*75}")
print(f"TOP {TOP_N} DAC TRUNG QUAN TRONG NHAT (theo Gain)")
print(f"{'='*75}")
print(f"{'Rank':<5} {'Feature':<55} {'Gain %':>8}  {'Split %':>8}")
print("-"*80)
for rank, idx in enumerate(order[:TOP_N], 1):
    grp = "?"
    for g, rng in GROUPS.items():
        if idx in rng:
            grp = g[:12]
            break
    name = feature_names[idx]
    print(f"{rank:<5} {name:<55} {pct_gain[idx]:>7.3f}%  {pct_split[idx]:>7.3f}%")

# ──────────────────────────────────────────────
# 6. Top Import Tokens (PE32D)
# ──────────────────────────────────────────────
imp_indices  = list(range(785, 785 + len(pe32d_tokens)))
imp_data     = [(feature_names[i], pct_gain[i], pct_split[i]) for i in imp_indices]
imp_sorted   = sorted(imp_data, key=lambda x: x[1], reverse=True)

print(f"\n{'='*75}")
print(f"TOP 40 IMPORT TOKEN QUAN TRONG NHAT (theo Gain)")
print(f"{'='*75}")
print(f"{'Rank':<5} {'Import Token':<55} {'Gain %':>8}  {'Split %':>8}")
print("-"*80)
for rank, (name, g, s) in enumerate(imp_sorted[:40], 1):
    print(f"{rank:<5} {name:<55} {g:>7.3f}%  {s:>7.3f}%")

# Phan loai import tokens
print(f"\n--- Phan loai import tokens quan trong ---")
dll_tokens   = [(n,g,s) for n,g,s in imp_sorted if n.startswith("import::dll:")]
api_tokens   = [(n,g,s) for n,g,s in imp_sorted if not n.startswith("import::dll:")]
print(f"  API tokens (dll!func): {len([x for x in imp_sorted if '!' in x[0]])}")
print(f"  DLL presence tokens:   {len(dll_tokens)}")

print(f"\n  Top 15 API tokens:")
api_only = [(n,g,s) for n,g,s in imp_sorted if '!' in n]
for rank, (n,g,s) in enumerate(api_only[:15],1):
    print(f"    {rank:2}. {n:<50} gain={g:.3f}%")

print(f"\n  Top 15 DLL presence tokens:")
for rank, (n,g,s) in enumerate(dll_tokens[:15],1):
    print(f"    {rank:2}. {n:<50} gain={g:.3f}%")

# ──────────────────────────────────────────────
# 7. Handcrafted import stats
# ──────────────────────────────────────────────
hc_indices = list(range(2712, 2725))
hc_data    = [(feature_names[i], pct_gain[i], pct_split[i]) for i in hc_indices]
hc_sorted  = sorted(hc_data, key=lambda x: x[1], reverse=True)

print(f"\n{'='*75}")
print(f"HANDCRAFTED IMPORT STATS (13 features)")
print(f"{'='*75}")
print(f"{'Feature':<45} {'Gain %':>8}  {'Split %':>8}")
print("-"*65)
for name, g, s in hc_sorted:
    print(f"{name:<45} {g:>7.3f}%  {s:>7.3f}%")

# ──────────────────────────────────────────────
# 8. Section slots
# ──────────────────────────────────────────────
sect_indices = list(range(775, 785))
sect_data    = [(feature_names[i], pct_gain[i], pct_split[i]) for i in sect_indices]
sect_sorted  = sorted(sect_data, key=lambda x: x[1], reverse=True)

print(f"\n{'='*75}")
print(f"SECTION SLOTS")
print(f"{'='*75}")
for name, g, s in sect_sorted:
    print(f"  {name:<20} gain={g:.3f}%  split={s:.3f}%")

# ──────────────────────────────────────────────
# 9. Top byte histogram
# ──────────────────────────────────────────────
byte_indices = list(range(292, 548))
byte_data    = [(feature_names[i], pct_gain[i], pct_split[i]) for i in byte_indices]
byte_sorted  = sorted(byte_data, key=lambda x: x[1], reverse=True)

print(f"\n{'='*75}")
print(f"TOP 15 BYTE HISTOGRAM (theo Gain)")
print(f"{'='*75}")
for rank, (name, g, s) in enumerate(byte_sorted[:15], 1):
    print(f"  {rank:2}. {name:<25} gain={g:.3f}%  split={s:.3f}%")

# ──────────────────────────────────────────────
# 10. So sanh voi CYAIPE32.mdl
# ──────────────────────────────────────────────
print(f"\n{'='*75}")
print(f"SO SANH VOI CYAIPE32.mdl (cu)")
print(f"{'='*75}")
print(f"{'Dac diem':<40} {'CYAIPE32':>12}  {'CYAIPE32NEW':>14}")
print("-"*70)
print(f"{'Tong so features':<40} {'1040':>12}  {'2725':>14}")
print(f"{'Import representation':<40} {'255 tokens':>12}  {'1927+13':>14}")
print(f"{'Import type':<40} {'binary flag':>12}  {'token+handcraft':>14}")
print(f"{'Pe header features':<40} {'775 floats':>12}  {'775 floats':>14}")
print(f"{'Section slots':<40} {'10':>12}  {'10':>14}")

# ──────────────────────────────────────────────
# 11. Luu CSV
# ──────────────────────────────────────────────
out_path = r"E:\AV\Train_AI_Python\Data_Preprocessing\feature_importance_PE32NEW.csv"
with open(out_path, "w", encoding="utf-8") as f:
    f.write("rank,feature_name,group,gain_pct,split_pct\n")
    for rank, idx in enumerate(order, 1):
        name = feature_names[idx]
        grp = "Unknown"
        for g, rng in GROUPS.items():
            if idx in rng:
                grp = g
                break
        f.write(f"{rank},{name},{grp},{pct_gain[idx]:.6f},{pct_split[idx]:.6f}\n")

print(f"\n[OK] Da luu vao: {out_path}")
