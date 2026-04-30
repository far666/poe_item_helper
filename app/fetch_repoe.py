import urllib.request
import os

### 別人整理的json檔案 直接拿來用

os.makedirs("knowledge/repoe", exist_ok=True)

BASE = "https://repoe-fork.github.io/Traditional%20Chinese/"

FILES = [
    "mods.json",
    "base_items.json",
    "cluster_jewels.json",
    "cluster_jewel_notables.json",
    "stat_translations.json",
]

for filename in FILES:
    url = BASE + filename
    dest = f"knowledge/repoe/{filename}"
    print(f"下載 {filename}...")
    urllib.request.urlretrieve(url, dest)
    print(f"✅ {filename} 完成")

print("\n全部下載完畢！")