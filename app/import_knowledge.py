import chromadb
import os

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")

client = chromadb.HttpClient(host=CHROMA_HOST, port=8000)
collection = client.get_or_create_collection(name="poe_knowledge")

def import_file(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    documents = []
    ids = []
    idx = 0

    for line in lines:
        line = line.strip()
        # 跳過空行和標題行
        if not line or line.startswith("#"):
            continue
        documents.append(line)
        ids.append(f"doc_{idx}")
        idx += 1

    if documents:
        collection.upsert(documents=documents, ids=ids)
        print(f"✅ 匯入完成，共 {len(documents)} 筆資料")

if __name__ == "__main__":
    import_file("knowledge/poe_mods.txt")