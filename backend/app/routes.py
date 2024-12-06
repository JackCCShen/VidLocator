from app import app
from flask import request, jsonify
from collections import Counter
import time 
import logging
from app.services import ChromaDBService, YouTubeService, LLMService
log = True
queue_set = set()

store_video_logger = logging.getLogger("store_video_logger")
store_video_handler = logging.FileHandler("store_video_data.log")
store_video_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
store_video_logger.addHandler(store_video_handler)
store_video_logger.setLevel(logging.INFO)

@app.route('/store_video_data', methods=['POST'])
def store_video_data():
    store_video_data_start_time = time.time()
    youtube_url = request.json['youtube_url']
    try:
        chroma_db = ChromaDBService()
        yt = YouTubeService()
        video_id = YouTubeService.extract_video_id(youtube_url)
        if video_id in queue_set:
            return jsonify({"message": "Processing"}), 200
        queue_set.add(video_id)

        # Check if the data has existed in db
        if chroma_db.video_exists(video_id):
            return jsonify({"message": "Existed"}), 200

        fetch_metadata_start_time = time.time()
        title, description = yt.fetch_metadata(youtube_url)
        fetch_metadata_end_time = time.time()
        if log:
            store_video_logger.info(f"{video_id} Fetch metadata Time taken: {fetch_metadata_end_time - fetch_metadata_start_time:.2f} seconds.")
     
        chroma_db.store_metadata(video_id, title, description)
        store_metadata_end_time = time.time()
        if log:
            store_video_logger.info(f"{video_id} Store metadata Time taken: {store_metadata_end_time - fetch_metadata_end_time:.2f} seconds.")
        
        # Attempt to fetch subtitle
        srt_file_path = yt.fetch_subtitle(youtube_url, log, store_video_logger, force_download_audio=False)
        if srt_file_path is None:
            return jsonify({"message": "Fail"}), 200

        srt_content = ''
        with open(srt_file_path, 'r', encoding='utf-8') as file:
            srt_content = file.read()

        store_subtitles_start_time = time.time()
        chroma_db.store_subtitles(srt_content, video_id)
        store_subtitles_end_time = time.time()
        if log:
            store_video_logger.info(f"{video_id} Store Subtitle Data Time taken: {store_subtitles_end_time - store_subtitles_start_time:.2f} seconds.")
        
        queue_set.remove(video_id)

        store_video_data_end_time = time.time()
        if log:
            store_video_logger.info(f"{video_id} Store Video Data Time taken: {store_video_data_end_time - store_video_data_start_time:.2f} seconds.")
        return jsonify({"message": "Sucess"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/query_timestamp', methods=['POST'])
def query_timestamp():
    print(request.json)
    query_text = request.json['query_text']
    youtube_url = request.json['youtube_url']

    try:
        video_id = YouTubeService.extract_video_id(youtube_url)

        chroma_db = ChromaDBService()
        title, description = chroma_db.get_metadata_by_video_id(video_id)

        llm = LLMService()
        keywords = llm.generate_rag_keywords(title, description, query_text)
        candidates = set(chroma_db.find_subtitle_by_query(query_text, video_id))

        # candidates = []
        for k in keywords:
            # candidates += [s[0] for s in chroma_db.find_subtitle_by_query(k, video_id)]
            pairs = chroma_db.find_subtitle_by_query(k, video_id)
            for p in pairs:
                candidates.add(p)

        # cnt = Counter(candidates)
        candidates = list(candidates)
        timestamps = llm.get_recommended_timestamps(title, description, query_text, candidates)
        
        return jsonify(timestamps), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
