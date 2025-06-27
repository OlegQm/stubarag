from chromadb.api import AsyncClientAPI
from app.routers.schemas import Chunks, Chunk, ChunkMetedata
from app.utils import initialize_embedding_function

async def get_chunks(chroma_client: AsyncClientAPI, url: str) -> Chunks:
    """
    The function retrieves all "chunks" (content fragments) associated with the given URL 
    from the asynchronous ChromaDB client (chroma_client). These chunks are stored in 
    the "webscraper" collection.

    - If the URL is not provided, a ValueError is raised.
    - Under the hood, the function:
      1. Retrieves or creates a collection in ChromaDB named "webscraper".
      2. Uses the embedding initialization function (initialize_embedding_function())
         to create the collection with vector embedding support, if necessary.
      3. Filters entries in the collection by the "url" field, returning documents (texts) 
         and their associated metadata.
      4. Converts the results into Chunks and Chunk objects containing:
         - The document (text content),
         - Metadata (ChunkMetadata) such as URL, description, MD5, etc.
      5. Returns a Chunks object containing all the retrieved results.

    :param chroma_client: An instance of the asynchronous ChromaDB client for interacting 
                          with collections.
    :param url: The URL for which corresponding chunks are being retrieved.
    :return: A Chunks object containing a list of all chunks found for the given URL.
    :raises ValueError: If the URL parameter is empty or invalid.
    :raises KeyError: If expected metadata keys are missing.
    :raises Exception: If an unexpected error occurs during the interaction with ChromaDB.
    """

    webscraper_colection_name = "webscraper"

    if not url.strip():
        raise ValueError("Invalid URL: must be a non-empty string.")

    try:
        chromadb_collection = await chroma_client.get_or_create_collection(
            name=webscraper_colection_name,
            embedding_function=initialize_embedding_function(),
            metadata={"hnsw:space": "cosine"}
        )

        if chromadb_collection is None:
            raise RuntimeError(
                "Failed to retrieve or create the ChromaDB collection."
            )

        existing_chunks = await chromadb_collection.get(
            where={"url": url},
            include=["metadatas", "documents"]
        )

        if not isinstance(existing_chunks, dict):
            raise TypeError("Unexpected response format from ChromaDB.")

        if (
            "documents" not in existing_chunks
            or "metadatas" not in existing_chunks
        ):
            raise KeyError(
                "Missing 'documents' or 'metadatas' in ChromaDB response."
            )

        documents = existing_chunks.get("documents", [])
        metadatas = existing_chunks.get("metadatas", [])

        if len(documents) != len(metadatas):
            raise ValueError(
                "Mismatch between number of documents and metadata entries."
            )

        chunks = Chunks(chunks=[])

        for document, metadata in zip(documents, metadatas):
            chunk_metadata = ChunkMetedata(
                url=metadata["url"],
                description=metadata["description"],
                md5=metadata["md5"],
                date=metadata["date"],
                owner=metadata["owner"],
                chunk_number=metadata["chunk_number"],
                chunk_md5=metadata["chunk_md5"]
            )
            chunk = Chunk(document=document, metadata=chunk_metadata)
            chunks.chunks.append(chunk)

        return chunks

    except ValueError as ve:
        raise ValueError(f"Value error: {ve}") from ve
    except KeyError as ke:
        raise KeyError(f"Missing expected metadata keys: {ke}") from ke
    except TypeError as te:
        raise TypeError(f"Type error: {te}") from te
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}") from e
