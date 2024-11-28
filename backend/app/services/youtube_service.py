from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import SRTFormatter
from urllib.parse import urlparse, parse_qs
import yt_dlp
import torch
from faster_whisper import WhisperModel
import os
# from transformers import pipeline
from app.utils import merge_srt_sentences

class YouTubeService:
    def __init__(self, save_dir="subtitles/"):
        """
        Initialize the manager with a directory to save subtitles.

        Args:
            save_dir (str): path of the srt directory.

        Returns:
            None
        """
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

    @classmethod
    def extract_video_id(self, youtube_url):
        """
        Extract and return the video ID from a YouTube URL.

        Args:
            youtube_url (str): URL of the YouTube video.

        Returns:
            str: The video ID if successfully extracted, else None.
        """
        parsed_url = urlparse(youtube_url)
        if parsed_url.hostname != "www.youtube.com":
            return None
        
        parameters = parse_qs(parsed_url.query)
        if 'v' not in parameters or len(parameters['v']) == 0:
            return None
        return parameters['v'][0]
    

    def __format_timestamp(self, seconds):
        """
        Format a given time in seconds to SRT timestamp format.

        Args:
            seconds (float): Time in seconds.

        Returns:
            str: Timestamp in SRT format (HH:MM:SS,mmm).
        """
        millisec = int((seconds - int(seconds)) * 1000)
        hours, seconds = divmod(int(seconds), 3600)
        minutes, seconds = divmod(seconds, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millisec:03d}"
    

    def __generate_subtitles_from_audio(self, audio_file, model_name="medium"):
        """
        Transcribe an audio file to subtitles in SRT using faster Whisper.

        Args:
            audio_file (str): Path to the audio file.
            model_name (str): Whisper model size (default is "medium").

        Returns:
            str: Subtitles in SRT format.
        """
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        model = WhisperModel(model_name, device=device, compute_type=compute_type)
        
        segments, _ = model.transcribe(audio_file, beam_size=5)
        
        srt_str = ''
        
        for i, segment in enumerate(segments, start=1):
            srt_str += f"{i}\n"
            srt_str += f"{self.__format_timestamp(segment.start)} --> {self.__format_timestamp(segment.end)}\n"
            srt_str += f"{segment.text.strip()}\n\n"
        return srt_str
    

    def __download_audio(self, youtube_url, video_id=None):
        """
        Download the audio track of a YouTube video.

        Args:
            youtube_url (str): The full URL of the YouTube video.
            video_id (str, optional): The video ID. If None, it will be extracted from the URL.

        Returns:
            None
        """
        output_path = "audio/"
        if video_id is None:
            video_id = self.extract_video_id(youtube_url)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path + video_id + '.%(ext)s',
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])


    def fetch_subtitle(self, youtube_url):
        """
        Fetch and save the subtitle in SRT format for a YouTube video. If unavailable, download the audio 
        and generate subtitles using a Whisper model.

        Args: youtube_url (str): The full URL of the YouTube video.

        Returns: str (srt file path) or None
        """
        video_id = self.extract_video_id(youtube_url)
        if video_id is None:
            return False
        
        srt_file_path = os.path.join(self.save_dir, f"{video_id}.srt")
        
        # Attempt to fetch subtitles using YouTubeTranscriptApi
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            formatter = SRTFormatter()

            srt_formatted = formatter.format_transcript(transcript)
            with open(srt_file_path, "w", encoding="utf-8") as srt_file:
                srt_file.write(srt_formatted)
            merge_srt_sentences(srt_file_path)
            print(f"Generated and saved subtitles: {srt_file_path}")
            return srt_file_path
        except:
            pass

        # generate subtitle from audio
        audio_file = f"audio/{video_id}.webm"
        print(f"Donwnloading audio of {youtube_url}...")
        self.__download_audio(youtube_url, video_id)
        print("Transcribing...")

        srt_content = self.__generate_subtitles_from_audio(audio_file)
        if srt_content:
            with open(srt_file_path, "w", encoding="utf-8") as srt_file:
                srt_file.write(srt_content)
            merge_srt_sentences(srt_file_path)
            
            print(f"Generated and saved subtitles: {srt_file_path}")
            return srt_file_path
        
        print("Failed to generate subtitles.")
        return None
    

    def fetch_metadata(self, youtube_url):
        """ 
        Fetch the title and description for a YouTube video.

        Args: youtube_url (str): The full URL of the YouTube video.

        Returns: title (str), description (str)
        """
        ydl_opts = {"quiet": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            title = info.get("title", "Unknown")
            description = info.get("description", "No description")
        return title, description


    # def summarize_subtitle(self, srt_file, max_length=150):
    #     """
    #     Summarize the text content of an SRT file using LLM.

    #     Args:
    #         srt_file (str): Path to the SRT file.
    #         model (str): Name of the model to use for summarization.
    #         max_length (int): Maximum length of the summary.
    #     """
    #     with open(srt_file, 'r', encoding='utf-8') as file:
    #         srt_content = file.read()
        
    #     subtitles = list(srt.parse(srt_content))
    #     text_lines = [subtitle.content for subtitle in subtitles]
    #     full_text = "\n".join(text_lines)

    #     # Summarize the extracted text
    #     summarizer = pipeline("summarization", device=0 if torch.cuda.is_available() else -1, model="sshleifer/distilbart-cnn-12-6")
    #     summary = summarizer(full_text, max_length=max_length, min_length=50, do_sample=False)
    #     return summary[0]['summary_text']
    

# sub = SubtitleManager()
# s = sub.summarize_subtitle(r"subtitles\0n809nd4Zu4.srt")
# print(s)

# URL = r"https://www.youtube.com/watch?v=0n809nd4Zu4&ab_channel=freeCodeCamp.org"
# yt = YouTubeService()
# title, description = yt.fetch_metadata(URL)
# print(title, description)