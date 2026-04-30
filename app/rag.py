import chromadb
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
import os
from base_evaluator import evaluate_base, analyze_weapon_mods, compute_verdict

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
CHROMA_URL = os.getenv("CHROMA_URL", "http://localhost:8000")

chroma_client = chromadb.HttpClient(host=CHROMA_URL.replace("http://", "").split(":")[0], port=8000)
collection = chroma_client.get_or_create_collection(name="poe_knowledge")

llm = OllamaLLM(base_url=OLLAMA_URL, model="llama3.1:8b")

tier_build_template = PromptTemplate(
    input_variables=["context", "item", "verdict"],
    template="""
你是一個 Path of Exile 裝備專家。
根據知識庫資料完成以下兩項任務，不要多說其他話。

知識庫資料：
{context}

裝備資訊：
{item}

任務一【詞綴Tier識別】
逐一列出裝備上的每個詞綴（implicit 除外），對照知識庫 T1/T2/T3 數值範圍判斷 Tier。
知識庫無對應數值則標「Tier 未知」，廢詞直接標「廢詞」。

任務二【適合Build】
最終判斷為「{verdict}」。
若判斷為高價值或低價值，說明適合哪種 build；否則填「無」。

請用以下固定格式回答：

【詞綴Tier】
- <詞綴>：<Tier或廢詞>

【適合Build】
<build 說明或「無」>
"""
)


INFLUENCE_KEYWORDS = ["塑者", "古老", "十字軍", "救贖者", "獵人", "督軍",
                      "Shaper", "Elder", "Crusader", "Redeemer", "Hunter", "Warlord"]


def extract_item_facts(item_text: str) -> dict:
    """從 POE tooltip 解析關鍵事實欄位，避免讓 LLM 自行判斷數字與標記。"""
    lines = [l.strip() for l in item_text.splitlines() if l.strip() and not l.strip().startswith("---")]

    base_type = lines[3] if len(lines) >= 4 else ""

    item_level = None
    for line in lines:
        if line.startswith("物品等級:"):
            try:
                item_level = int(line.split(":")[1].strip())
            except ValueError:
                pass
            break

    influences = [kw for kw in INFLUENCE_KEYWORDS if kw in item_text]

    return {
        "base_type": base_type,
        "item_level": item_level,
        "influences": influences,
        "has_influence": len(influences) > 0,
        "ilvl_ge_80": item_level is not None and item_level >= 80,
    }


def extract_base_type(item_text: str) -> str:
    return extract_item_facts(item_text)["base_type"]


def query_knowledge(item_text: str) -> str:
    facts = extract_item_facts(item_text)
    base_type = facts["base_type"]

    docs_base = []
    if base_type:
        res = collection.query(query_texts=[base_type], n_results=3)
        docs_base = res["documents"][0] if res["documents"] else []

    res2 = collection.query(query_texts=[item_text], n_results=5)
    docs_item = res2["documents"][0] if res2["documents"] else []

    seen = set()
    docs = []
    for d in docs_base + docs_item:
        if d not in seen:
            seen.add(d)
            docs.append(d)

    context = "\n\n".join(docs) if docs else "無相關知識庫資料"

    base_verdict, _ = evaluate_base(
        facts["base_type"], facts["has_influence"], facts["ilvl_ge_80"]
    )

    mods = analyze_weapon_mods(item_text)
    verdict_label, reasons = compute_verdict(base_verdict, mods, item_text)

    llm_result = (tier_build_template | llm).invoke({
        "context": context,
        "item": item_text,
        "verdict": verdict_label,
    })

    reasons_str = "\n".join(f"- {r}" for r in reasons)
    return f"【判斷】{verdict_label}\n\n{llm_result}\n\n【原因】\n{reasons_str}"
