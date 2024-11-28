import srt
import re
from datetime import datetime, timedelta

def parse_srt(srt_text):
    """
    Parse SRT subtitles into structured segments. 
    """
    subtitles = list(srt.parse(srt_text))
    return [{"start": str(sub.start), "text": sub.content} for sub in subtitles]


def merge_srt_sentences(file_path: str):
    """
    Reads an SRT file, merges subtitle fragments into complete sentences,
    and rewrites the SRT file with adjusted timestamps.

    Args:
        file_path (str): Path to the SRT file to process.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        subtitles = list(srt.parse(file.read()))
    
    merged_subtitles = []
    buffer_text = ""
    start_time = None

    for subtitle in subtitles:
        buffer_text += " " + subtitle.content.strip()
        buffer_text = buffer_text.strip()  
        
        if start_time is None:
            start_time = subtitle.start
        
        if buffer_text.endswith(('.', '!', '?')):
            merged_subtitles.append(
                srt.Subtitle(
                    index=len(merged_subtitles) + 1,
                    start=start_time,
                    end=subtitle.end,
                    content=buffer_text
                )
            )
            buffer_text = ""
            start_time = None

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(srt.compose(merged_subtitles))


def extract_timestamps(input_string):
    pattern = r'\b(?:[0-9]|[0-9]{2}):[0-5][0-9]:[0-5][0-9]\b'

    timestamps = re.findall(pattern, input_string)
    return timestamps



def group_timestamps(timestamps, interval_sec=60):
    time_objects = [datetime.strptime(ts, "%H:%M:%S") for ts in timestamps]
    grouped = []
    previous_time = None

    for current_time in time_objects:
        # If this is the first timestamp or the time difference is >= 1 minute, add to the group
        if previous_time is None or current_time - previous_time >= timedelta(seconds=interval_sec):
            grouped.append(current_time)
        previous_time = current_time

    grouped_timestamps = [time.strftime("%H:%M:%S") for time in grouped]
    return grouped_timestamps

