from app import app
from flask import request, jsonify
from collections import Counter

from app.services import ChromaDBService, YouTubeService, LLMService

@app.route('/store_video_data', methods=['POST'])
def store_video_data():
    youtube_url = request.json['youtube_url']
    print(youtube_url)
    try:
        yt = YouTubeService()
        srt_file_path = yt.fetch_subtitle(youtube_url)
        title, description = yt.fetch_metadata(youtube_url)
        if srt_file_path is None:
            return jsonify({"message": "Fail"}), 200

        srt_content = ''
        with open(srt_file_path, 'r', encoding='utf-8') as file:
            srt_content = file.read()

        video_id = YouTubeService.extract_video_id(youtube_url)

        chroma_db = ChromaDBService()
        chroma_db.store_metadata(video_id, title, description)
        chroma_db.store_subtitles(srt_content, video_id)
        return jsonify({"message": "Sucess"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/query_timestamp', methods=['POST'])
def query_timestamp():
    query_text = request.json['query_text']
    youtube_url = request.json['youtube_url']

    try:
        video_id = YouTubeService.extract_video_id(youtube_url)

        chroma_db = ChromaDBService()
        title, description = chroma_db.get_metadata_by_video_id(video_id)

        llm = LLMService()
        keywords = llm.generate_rag_keywords(title, description, query_text)
        candidates = set(chroma_db.find_subtitle_by_query(query_text, video_id))
        # print(chroma_db.find_subtitle_by_query(query_text, video_id))

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
