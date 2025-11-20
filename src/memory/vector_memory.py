import google.genai as genai
import os
import json

class VectorMemory:
    def __init__(self):
        self.client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        self.model = "text-embedding-004"
        self.store = []  # simple in-memory index (can replace w/ Chroma or Pinecone)

    def embed(self, text):
        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
        )
        return response.embeddings[0].values

    def add(self, text, metadata=None):
        vector = self.embed(text)
        self.store.append({
            "vector": vector,
            "text": text,
            "metadata": metadata or {}
        })

    def search(self, query, top_k=3):
        qvec = self.embed(query)

        def cosine(v1, v2):
            import numpy as np
            return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

        scored = [
            (cosine(qvec, item["vector"]), item)
            for item in self.store
        ]

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:top_k]]
