import srt
import chromadb
from chromadb.config import DEFAULT_TENANT, DEFAULT_DATABASE, Settings
import ollama

class ChromaDBManager:
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


    def parse_srt(self, srt_text):
        """
        Parse SRT subtitles into structured segments.
        """
        subtitles = list(srt.parse(srt_text))
        return [{
            "start": str(sub.start),
            "end": str(sub.end),
            "text": sub.content
        } for sub in subtitles]
    

    def store_subtitles(self, srt_text, video_id):
        """
        Store subtitles into a ChromaDB collection.
        """
        segments = self.parse_srt(srt_text)

        collection_name = f"subtitles_{video_id}"
        collection = self.chroma_client.get_or_create_collection(name=collection_name)

        for i, seg in enumerate(segments):
            response = ollama.embeddings(model="llama3.2", prompt=seg['text'])
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

        ret = []
        for i, distance in enumerate(results['distances'][0]):
            if distance < results['distances'][0][0] * distance_threshold_ratio:
                ret.append(results['metadatas'][0][i])
            else:
                break

        return ret

# srt_file_path = "subtitles/0n809nd4Zu4.srt"
# with open(srt_file_path, "r", encoding="utf-8") as srt_file:
#     srt_text = srt_file.read()

# chroma_manager = ChromaDBManager()

# collection_name = chroma_manager.store_subtitles(srt_text, "0n809nd4Zu4")
# print(collection_name)

# user_query = "How to do a Chrome storage sync?"
# video_id = "0n809nd4Zu4"

# result = chroma_manager.find_subtitle_by_query(user_query, video_id)

# print(result)