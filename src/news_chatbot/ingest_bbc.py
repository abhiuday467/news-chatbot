from dataclasses import asdict
import json
from typing import Iterable, Sequence
from datasets import load_dataset, tqdm
from tqdm.auto import tqdm
import weaviate
from .config import load_weaviate_settings
from weaviate.classes.config import Configure, DataType, Property

COLLECTION_NAME="BBCArticle"
BATCH_SIZE = 64
def _create_collection(client: weaviate.WeaviateClient) -> weaviate.collections.Collection:
    if client.collections.exists(COLLECTION_NAME):
        return client.collections.get(COLLECTION_NAME)

    client.collections.create(
        name = COLLECTION_NAME,
        vectorizer_config= Configure.Vectorizer.text2vec_transformers(),
        properties=[
            Property(name="news_id", data_type=DataType.TEXT),
            Property(name="article", data_type=DataType.TEXT),
            Property(name="summary", data_type=DataType.TEXT),
        ]
    )
    return client.collections.get(COLLECTION_NAME)

def _batched(rows: Iterable[dict], size: int) -> Iterable[Sequence[dict]]:
    batch:list[dict] = []
    for row in rows:
        batch.append(row)
        if(len(batch) == size):
            yield batch
            batch = []
    if batch:
        yield batch
        
def ingest()-> None:
    settings = load_weaviate_settings()
    dataset = load_dataset("shwet/BBC_NEWS", split="train")
    total_rows = len(dataset)
    print(dataset)
    settings = load_weaviate_settings()

    with weaviate.connect_to_local(
        host=settings.host,
        port = settings.port,
        grpc_port = settings.grpc_port,
        headers=settings.headers,
    ) as client:
        collection = _create_collection(client)
        with collection.batch.dynamic() as writer, tqdm(
            total= total_rows,
            desc="Ingesting BBC articles",
            unit = "rows",
        ) as progress:
            for rows in tqdm(_batched(dataset, BATCH_SIZE)):
                for row in rows:
                    writer.add_object(
                        properties = {
                            "news_id": str(row["ids"]),
                            "article": row["articles"],
                            "summary": row["summary"],
                        },
                    )
                progress.update(len(rows))


def delete_collection() -> bool:
    """Delete the BBCArticle collection if it exists.

    Returns True if the collection was removed, False otherwise.
    """
    settings = load_weaviate_settings()
    with weaviate.connect_to_local(
        host=settings.host,
        port=settings.port,
        grpc_port=settings.grpc_port,
        headers=settings.headers,
    ) as client:
        if not client.collections.exists(COLLECTION_NAME):
            print(f"Collection '{COLLECTION_NAME}' does not exist.")
            return False
        client.collections.delete(COLLECTION_NAME)
        print(f"Deleted collection '{COLLECTION_NAME}'.")
        return True

if __name__ == "__main__":
    # ingest()
    settings = load_weaviate_settings()
    with weaviate.connect_to_local(
        host=settings.host,
        port = settings.port,
        grpc_port = settings.grpc_port,
        headers=settings.headers,
    ) as client:
        collection = client.collections.get("BBCArticle")
        response = collection.query.near_text("Give me news about London", limit = 1, return_metadata=["distance","score"])
        print(asdict(response).keys())