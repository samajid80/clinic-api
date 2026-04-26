import os
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

def get_search_client() -> SearchClient:
    return SearchClient(
        endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
        index_name=os.environ["AZURE_SEARCH_INDEX"],
        credential=AzureKeyCredential(os.environ["AZURE_SEARCH_KEY"])
    )

def embed_query(query: str) -> list[float]:
    # client = OpenAI(
    #     base_url=os.environ["AZURE_OPENAI_ENDPOINT"] + "openai/v1/",
    #     api_key=os.environ["AZURE_OPENAI_KEY"]
    # )

    client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version="2024-02-01"  # <--- Use this version
)
    response = client.embeddings.create(
        input=query,
        model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]
    )
    return response.data[0].embedding

def search_clinic_docs(query: str, top: int = 3) -> list[dict]:
    search_client = get_search_client()
    query_vector = embed_query(query)

    vector_query = VectorizedQuery(
        vector=query_vector,
        k_nearest_neighbors=top,
        fields="text_vector"   # the field AI Search stores embeddings in
    )

    results = search_client.search(
        search_text=query,          # keyword search component
        vector_queries=[vector_query],  # vector search component
        select=["chunk", "title", "chunk_id"],
        top=top
    )

    return [
        {
            "content": r["chunk"],
            "source": r["chunk_id"],
            "score": r["@search.score"]
        }
        for r in results
    ]


# if __name__ == "__main__":
#     results = search_clinic_docs("What time does the clinic open?")
#     for r in results:
#         print(f"Score: {r['score']:.3f} | Source: {r['source']}")
#         print(f"Content: {r['content'][:200]}...")
#         print("---")