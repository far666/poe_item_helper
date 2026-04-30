import chromadb
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
import os

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
CHROMA_URL = os.getenv("CHROMA_URL", "http://localhost:8000")

# 連接 ChromaDB
chroma_client = chromadb.HttpClient(host=CHROMA_URL.replace("http://", "").split(":")[0], port=8000)
collection = chroma_client.get_or_create_collection(name="poe_knowledge")

# 連接 Ollama LLM
llm = OllamaLLM(base_url=OLLAMA_URL, model="llama3.1:8b")

prompt_template = PromptTemplate(
    input_variables=["context", "item"],
    template="""
你是一個 Path of Exile 裝備專家。
根據以下知識庫資料，判斷這個裝備有沒有價值，並說明原因。

知識庫資料：
{context}

裝備資訊：
{item}


請用以下固定格式回答，不要多說其他話：

【判斷】高價值 / 低價值 / 沒價值 / 過渡裝 / 合成用 

【原因】
用2-4點條列說明，例如：
- 基底正確，物品等級足夠
- 攻擊速度詞綴達T2
- 缺少暴擊加成

【適合Build】
如果有價值，說明適合哪種build。沒價值則填「無」。
"""
)

def query_knowledge(item_text: str) -> str:
    # 從知識庫找相關資料
    results = collection.query(query_texts=[item_text], n_results=3)
    docs = results["documents"][0] if results["documents"] else []
    context = "\n".join(docs) if docs else "無相關知識庫資料"

    # 組合 prompt 交給 LLM
    chain = prompt_template | llm
    response = chain.invoke({"context": context, "item": item_text})
    return response