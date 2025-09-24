import json
import weaviate
from weaviate.classes.config import Configure, DataType, Property

from .config import load_weaviate_settings


def embed_prompt(prompt: str) -> list[float]:
    settings = load_weaviate_settings()

    with weaviate.connect_to_local(
        host=settings.host,
        port=settings.port,
        grpc_port=settings.grpc_port,
        headers=settings.headers,
    ) as client:
        # optional: ensure a collection exists if you plan to store objects later
        collection_name = "MyVectorizerClass"
        if not client.collections.exists(collection_name):
            client.collections.create(
                name=collection_name,
                vectorizer_config=Configure.Vectorizer.text2vec_transformers(),
                properties=[Property(name="content", data_type=DataType.TEXT)],
            )

        # ask Weaviate’s vectorizer module to embed the prompt
        response = client._connection.post(
            "/v1/vectors",
            json={"text": [prompt]},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["data"][0]["vector"]

    # result.vectors is a list of floats per text item


if __name__ == "__main__":
    vec = embed_prompt("Describe the latest advances in renewable energy.")
    print(json.dumps(vec[:10], indent=2))
