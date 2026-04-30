import json
import os

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def convert_mods():
    mods = load_json("knowledge/repoe/mods.json")

    # Key: (group_name, stat_ids_tuple) — 避免 ES/Armour/Evasion 混在同一群組
    groups = {}
    for mod_id, mod in mods.items():
        if mod.get("domain") != "item":
            continue
        if mod.get("generation_type") not in ("prefix", "suffix"):
            continue
        if mod.get("is_essence_only"):
            continue
        implicit_tags = mod.get("implicit_tags", [])
        if any(t in implicit_tags for t in ("mutatedunique", "unique")):
            continue
        stats = mod.get("stats", [])
        if not stats:
            continue
        group_list = mod.get("groups", [])
        if not group_list:
            continue

        group = group_list[0]
        stat_ids = tuple(s["id"] for s in stats)
        key = (group, stat_ids)

        if key not in groups:
            groups[key] = []
        groups[key].append((mod_id, mod))

    documents = []

    for (group, stat_ids), entries in groups.items():
        gen_type = entries[0][1].get("generation_type", "")

        # 同 required_level = 同 tier（不同裝備類型的同一階）
        # 每個 level 只保留數值最高的那個（代表該 tier 的最佳範圍）
        by_level = {}
        for mod_id, mod in entries:
            req_lv = mod.get("required_level", 0)
            max_val = max(s.get("max", 0) for s in mod.get("stats", []))
            if req_lv not in by_level or max_val > by_level[req_lv][2]:
                by_level[req_lv] = (mod_id, mod, max_val)

        # 依數值由低到高排序，T1 = 最高數值
        tier_entries = sorted(
            by_level.values(),
            key=lambda x: x[2]
        )

        # 收集所有裝備部位（跨所有 entry）
        all_spawn_tags = []
        seen_tags = set()
        for mod_id, mod in entries:
            for sw in mod.get("spawn_weights", []):
                tag = sw["tag"]
                if sw["weight"] > 0 and tag not in seen_tags:
                    seen_tags.add(tag)
                    all_spawn_tags.append(tag)

        lines = [f"詞綴群組: {group} ({gen_type})"]
        lines.append(f"效果: {', '.join(stat_ids)}")
        lines.append(f"可出現部位: {', '.join(all_spawn_tags[:10])}")
        lines.append(f"詞綴階級 (T1最高):")

        total = len(tier_entries)
        for i, (mod_id, mod, _) in enumerate(tier_entries):
            tier = total - i
            name = mod.get("name", "")
            req_lv = mod.get("required_level", 0)
            stats = mod.get("stats", [])
            stat_str = ", ".join([f"{s['min']}-{s['max']}" for s in stats])
            lines.append(f"  T{tier} ({name}) 需求等級{req_lv}: {stat_str}")

        documents.append("\n".join(lines))

    return documents

def save_documents(documents):
    os.makedirs("knowledge/converted", exist_ok=True)
    output_path = "knowledge/converted/mods_converted.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        for doc in documents:
            f.write(doc + "\n\n---\n\n")
    print(f"✅ 轉換完成，共 {len(documents)} 個詞綴群組")

if __name__ == "__main__":
    documents = convert_mods()
    save_documents(documents)
