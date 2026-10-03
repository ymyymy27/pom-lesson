"""离线检索实验：字符二元组TF-IDF，不冒充语义Embedding或真实LLM。"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re

def tokens(text):
    chunks = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]+", text.lower())
    result = []
    for chunk in chunks:
        if re.fullmatch(r"[a-z0-9]+", chunk) or len(chunk) == 1:
            result.append(chunk)
        else:
            result.extend(chunk[i:i+2] for i in range(len(chunk)-1))
    return result

def retrieve(question, documents, method="vector", limit=2):
    if method not in {"keyword", "vector"}:
        raise ValueError("不支持的检索方式")
    if not question.strip() or not documents:
        return []
    corpus = [Counter(tokens(d["title"]+" "+d["text"])) for d in documents]
    query = Counter(tokens(question))
    idf = {token: math.log((1+len(corpus))/(1+sum(token in row for row in corpus)))+1
           for row in corpus for token in row}
    def vector(counts):
        return {token: count*idf[token] for token,count in counts.items() if token in idf}
    q = vector(query)
    qnorm = math.sqrt(sum(v*v for v in q.values()))
    scores=[]
    for document, counts in zip(documents, corpus):
        if method == "keyword":
            score = len(set(query)&set(counts))
        else:
            values=vector(counts)
            denominator=qnorm*math.sqrt(sum(v*v for v in values.values()))
            score=sum(value*values.get(token,0) for token,value in q.items())/denominator if denominator else 0
        if score>0:
            scores.append({"source":document["id"],"title":document["title"],"text":document["text"],"score":round(score,4)})
    return sorted(scores,key=lambda row:(-row["score"],row["source"]))[:limit]

def ask(question, documents, method="vector"):
    hits=retrieve(question,documents,method)
    if not hits:
        return {"mode":"离线摘录", "answer":"资料中没有匹配依据。", "sources":[]}
    return {"mode":"离线摘录", "answer":hits[0]["text"], "sources":hits}

def main():
    parser=argparse.ArgumentParser(description="无需账号的检索与引用实验")
    parser.add_argument("question",nargs="?",default="Git提交前检查什么")
    parser.add_argument("--method",choices=["keyword","vector"],default="vector")
    args=parser.parse_args()
    documents=json.loads(Path(__file__).with_name("课程资料.json").read_text(encoding="utf-8"))
    print(json.dumps(ask(args.question,documents,args.method),ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
