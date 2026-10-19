import sys, re, collections, numpy as np
sys.stdout.reconfigure(encoding='utf-8')

MODEL_PATH = r"E:\AV\Train_AI_Python\Data_Preprocessing\CYAIPE32NEW.mdl"
PE32D_PATH = r"E:\AV\Train_AI_Python\Data_Preprocessing\PE32D"

# Parse model text to get split counts per feature (fast, no lgb load needed)
with open(MODEL_PATH, "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

# Feature count
m = re.search(r'max_feature_idx=(\d+)', text)
num_features = int(m.group(1)) + 1
print(f"num_features: {num_features}")

# Count splits per feature from "split_feature=" lines
split_counter = collections.Counter()
for line in text.splitlines():
    if line.startswith("split_feature="):
        vals = line[len("split_feature="):].split()
        for v in vals:
            split_counter[int(v)] += 1

# Gain per feature from "threshold=" is complex; use split count as proxy
# Also try to get gain from "leaf_value" / "internal_value" — use split_gain lines
gain_counter = collections.Counter()
for line in text.splitlines():
    if line.startswith("split_gain="):
        gains = line[len("split_gain="):].split()
        # pair with corresponding split_feature line — need index alignment
        break  # too complex without full parser; use split count only

# Rebuild split array
split_arr = np.zeros(num_features, dtype=np.float64)
for feat_id, cnt in split_counter.items():
    split_arr[feat_id] = cnt

pct_split = split_arr / split_arr.sum() * 100

# Build feature names
with open(PE32D_PATH, "r", encoding="utf-8", errors="ignore") as f:
    pe32d_tokens = [l.strip() for l in f if l.strip()]

HAND_KEYS = ['n_imports_total','n_dlls_total','n_ordinals_total','cnt_crt_imports','ratio_crt',
    'cnt_dynload','cnt_mem','cnt_proc_enum','cnt_reg','has_net_dll','has_crypto_dll',
    'has_dynload_and_mem','has_proc_enum_and_mem']

feature_names = []
for i in range(292): feature_names.append(f"header1_{i:03d}")
for b in range(256): feature_names.append(f"byte_freq_0x{b:02X}")
for i in range(227): feature_names.append(f"header2_{i:03d}")
for s in range(10):  feature_names.append(f"section_slot{s}")
for tok in pe32d_tokens: feature_names.append(f"import::{tok}")
for k in HAND_KEYS: feature_names.append(f"handcraft::{k}")

assert len(feature_names) == num_features, f"{len(feature_names)} vs {num_features}"
print(f"Feature names OK: {len(feature_names)}")

# --- Now use lightgbm in a proper way: gain from split_gain lines ---
# Parse per-tree: zip split_feature and split_gain arrays together
feat_gain = collections.defaultdict(float)
feat_split = collections.defaultdict(int)

split_feat_line = None
for line in text.splitlines():
    if line.startswith("split_feature="):
        split_feat_line = list(map(int, line[len("split_feature="):].split()))
    elif line.startswith("split_gain=") and split_feat_line is not None:
        gains = list(map(float, line[len("split_gain="):].split()))
        for fid, g in zip(split_feat_line, gains):
            feat_gain[fid] += g
            feat_split[fid] += 1
        split_feat_line = None

gain_arr  = np.array([feat_gain.get(i, 0.0) for i in range(num_features)])
split_arr = np.array([feat_split.get(i, 0)   for i in range(num_features)], dtype=float)

pct_gain  = gain_arr  / gain_arr.sum()  * 100
pct_split = split_arr / split_arr.sum() * 100

GROUPS = {
    "PE Header 1":   range(0,   292),
    "Byte Histogram":range(292, 548),
    "PE Header 2":   range(548, 775),
    "Section Slots": range(775, 785),
    "Import Token":  range(785, 2712),
    "Handcrafted":   range(2712, 2725),
}

print("\n" + "="*65)
print("DONG GOP THEO NHOM (Gain%)")
print("="*65)
print(f"{'Nhom':<25} {'Gain%':>8}  {'Split%':>8}  {'So FT':>7}")
print("-"*55)
for g, rng in GROUPS.items():
    idx = list(rng)
    print(f"{g:<25} {pct_gain[idx].sum():>7.2f}%  {pct_split[idx].sum():>7.2f}%  {len(idx):>7}")

order = np.argsort(gain_arr)[::-1]

print("\n" + "="*72)
print("TOP 50 DAC TRUNG QUAN TRONG NHAT (theo Gain)")
print("="*72)
print(f"{'Rank':<5} {'Feature':<55} {'Gain%':>8}  {'Split%':>7}")
print("-"*75)
for rank, idx in enumerate(order[:50], 1):
    print(f"{rank:<5} {feature_names[idx]:<55} {pct_gain[idx]:>7.3f}%  {pct_split[idx]:>6.3f}%")

# Top import tokens
imp_indices = list(range(785, 785+len(pe32d_tokens)))
imp_data = [(feature_names[i], pct_gain[i], pct_split[i]) for i in imp_indices]
imp_sorted = sorted(imp_data, key=lambda x: x[1], reverse=True)

print("\n" + "="*72)
print("TOP 30 IMPORT TOKEN (theo Gain)")
print("="*72)
print(f"{'Rank':<5} {'Token':<55} {'Gain%':>8}")
print("-"*70)
for rank, (n, g, s) in enumerate(imp_sorted[:30], 1):
    print(f"{rank:<5} {n:<55} {g:>7.3f}%")

# API vs DLL breakdown
api_only = [(n,g,s) for n,g,s in imp_sorted if '!' in n]
dll_only = [(n,g,s) for n,g,s in imp_sorted if n.startswith("import::dll:")]
print(f"\n  API tokens (dll!func): {len(api_only)} | DLL tokens: {len(dll_only)}")
print(f"\n  Top 10 API tokens:")
for r,(n,g,s) in enumerate(api_only[:10],1):
    print(f"    {r:2}. {n:<52} gain={g:.3f}%")
print(f"\n  Top 10 DLL tokens:")
for r,(n,g,s) in enumerate(dll_only[:10],1):
    print(f"    {r:2}. {n:<52} gain={g:.3f}%")

# Handcrafted
hc_indices = list(range(2712, 2725))
hc_data = [(feature_names[i], pct_gain[i], pct_split[i]) for i in hc_indices]
print("\n" + "="*65)
print("HANDCRAFTED IMPORT STATS (13 features)")
print("="*65)
for n,g,s in sorted(hc_data, key=lambda x: x[1], reverse=True):
    print(f"  {n:<45} gain={g:.3f}%  split={s:.3f}%")

# Save CSV
out = r"E:\AV\Train_AI_Python\Data_Preprocessing\feature_importance_PE32NEW.csv"
with open(out, "w", encoding="utf-8") as f:
    f.write("rank,feature_name,group,gain_pct,split_pct\n")
    for rank, idx in enumerate(order, 1):
        n = feature_names[idx]
        grp = "Unknown"
        for g, rng in GROUPS.items():
            if idx in rng: grp = g; break
        f.write(f"{rank},{n},{grp},{pct_gain[idx]:.6f},{pct_split[idx]:.6f}\n")
print(f"\n[OK] Saved: {out}")
