import chromadb
from chromadb.config import DEFAULT_TENANT, DEFAULT_DATABASE, Settings
import ollama
from app.utils import parse_srt

class ChromaDBService:
    def __init__(self, chroma_persist_dir="db/chroma"):
        """
        Initialize ChromaDB manager.
        """
        self.chroma_persist_dir = chroma_persist_dir
        self.chroma_client = chromadb.PersistentClient(
            path=self.chroma_persist_dir,
            settings=Settings(),
            tenant=DEFAULT_TENANT,
            database=DEFAULT_DATABASE,
        )


    def video_exists(self, video_id):
        """
        Check if the data of a video exists in ChromaDB.

        Args:
            video_id (str): Id of the video to check.

        Returns:
            bool: True if the video data exists, False otherwise.
        """
        collection_name = f"subtitles_{video_id}"
        collections = self.chroma_client.list_collections()
        return any(collection.name == collection_name for collection in collections)


    def store_metadata(self, video_id, title, description):
        """
        Store title, description into a ChromaDB collection.
        """
        metadata_collection = self.chroma_client.get_or_create_collection(name="metadata")
        metadata_collection.add(
            documents=[title, description],
            metadatas=[
                {"type": "title"},
                {"type": "description"},
            ],
            ids=[f"{video_id}_title", f"{video_id}_description"]
        )
    

    def store_subtitles(self, srt_text, video_id):
        """
        Store subtitles into a ChromaDB collection.
        """
        segments = parse_srt(srt_text)

        collection_name = f"subtitles_{video_id}"
        collection = self.chroma_client.get_or_create_collection(name=collection_name)

        for i, seg in enumerate(segments):
            response = ollama.embeddings(model="llama3.2", prompt=seg["text"])
            embedding = response["embedding"]
            collection.add(
                ids=[f"{video_id}_segment_{i}"],
                embeddings=[embedding],
                metadatas=[seg]
            )
        return collection_name
    

    def find_subtitle_by_query(self, user_query, video_id, max_results_len=5, distance_threshold_ratio=1.03):
        """
        Find the most relevant subtitle segment based on user input.

        Args:
            user_query (str): The user's text query.
            video_id (str): The video ID for the corresponding subtitle collection.

        Returns:
            list of dict: The most relevant subtitle segment, including timestamps and text.
        """
        collection_name = f"subtitles_{video_id}"
        collection = self.chroma_client.get_or_create_collection(name=collection_name)

        response = ollama.embeddings(model="llama3.2", prompt=user_query)
        query_embedding = response["embedding"]

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=max_results_len
        )

        # ret = []
        # for i, distance in enumerate(results['distances'][0]):
        #     if distance < results['distances'][0][0] * distance_threshold_ratio:
        #         ret.append(results['metadatas'][0][i])
        #     else:
        #         break
        

        return [(metadata['start'], metadata['text']) for metadata in results['metadatas'][0]]
    
    def get_metadata_by_video_id(self, video_id):
        """
        Get metadata_by_video_id
        """
        metadata_collection = self.chroma_client.get_or_create_collection(name="metadata")
        ids_to_query = [f"{video_id}_title", f"{video_id}_description"]
        result = metadata_collection.get(ids=ids_to_query)

        title, description = result["documents"]
        
        return title, description

