import pinecone

pinecone.init(
    api_key="cda81b35-cc39-444b-a75a-d531b1444678",
    environment="asia-southeast1-gcp-free",
)
index = pinecone.Index("qna")
index.delete(delete_all=True)
