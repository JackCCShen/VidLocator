import os
import openai
from dotenv import load_dotenv
from app.utils import extract_timestamps, group_timestamps

class LLMService():
    def __init__(self, model="llama-3.2-90b-vision-preview") -> None:
        load_dotenv()
        self.PUBLIC_API_MODEL = model
        self.PUBLIC_API_KEY = os.getenv("PUBLIC_API_KEY") or os.environ.get("PUBLIC_API_KEY")
        self.API_URL = "https://api.groq.com/openai/v1"

    def __llm_generate(self, prompt):
        client = openai.Client(base_url=self.API_URL, api_key=self.PUBLIC_API_KEY)

        response = client.chat.completions.create(
            model=self.PUBLIC_API_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        return response.choices[0].message.content

    def generate_rag_keywords(self, title, description, user_query):
        prompt = (
            "You are a helpful assistant specialized in extracting specific and detailed keywords for document retrieval.\n"
            "Your task is to analyze the given video title, description, and user query to generate concise, specific, and "
            "highly relevant keywords that capture the precise focus of the user's intent.\n"
            "These keywords will be used to match subtitles in the video to help identify the exact segments.\n"
            "### Inputs:\n"
            f"- Video Title: \"{title}\"\n"
            f"- Video Description: \"{description}\"\n"
            f"- User Query: \"{user_query}\"\n"
            "### Instructions:\n"
            "1. Analyze the main topic and context of the video based on the title and description.\n"
            "2. Break down the user's query to understand its specific focus and intent.\n"
            "3. Generate a list of related keywords or sentences that are:\n"
            "   - Highly relevant to the user's query.\n"
            "   - Likely to appear verbatim or in a very similar form in the video's subtitles.\n"
            "   - Detailed enough to narrow down the search to precise video segments.\n"
            "4. Avoid overly broad or generic keywords; prioritize specificity and relevance to the query.\n"
            "### Output Format:\n"
            "Provide the keywords as a comma-separated list."
        )

        res = self.__llm_generate(prompt)
        res = [keyword.strip() for keyword in res.split(',')]
        return res


    def get_recommended_timestamps(self, title, description, query_text, candidates):
        candidates_str = "\n".join([f"- {ts}: {text}" for ts, text in candidates])

        prompt = (
            "You are a helpful assistant tasked with identifying the most relevant video timestamps based on a user's query.\n"
            "The video provides the following context:\n\n"
            "### Video Title:\n"
            f"{title}\n\n"
            "### Video Description:\n"
            f"{description}\n\n"
            "### User Query:\n"
            f"{query_text}\n\n"
            "### Instructions:\n"
            "1. Carefully review the provided video title and description to understand the video's main topics.\n"
            "2. Analyze the user's query to infer their intent and identify the most relevant part of the video.\n"
            "3. Evaluate the given timestamp-text pairs, selecting the segment(s) that best match the user's query.\n"
            "4. If multiple timestamps are relevant, prioritize those with clearer and more specific connections to the query.\n\n"
            "### Timestamp-Text Candidates:\n"
            f"{candidates_str}\n\n"
            "### Output Format:\n"
            "Provide the relevant timestamp(s) and a brief explanation for your choice, formatted as follows:\n\n"
            "- Timestamp: [HH:MM:SS]\n"
            "- Reason: [Explanation]\n\n"
            "If no candidate is relevant, respond with:\n"
            "\"No relevant timestamp found.\""
        )

        res = self.__llm_generate(prompt)
        timestamps = extract_timestamps(res)
        for i in range(len(timestamps)):
            if timestamps[i][2] != ':':
                timestamps[i] = '0' + timestamps[i]
        timestamps = sorted(list(set(timestamps)))
        timestamps = group_timestamps(timestamps, interval_sec=60)

        return timestamps