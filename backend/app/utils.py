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


def extract_timestamps_explaination(input_str):
    chunks = [chunk.strip() for chunk in input_str.strip().split("\n\n")]

    parsed_data = []
    unique_data = {}
    for chunk in chunks:
        lines = chunk.split("\n")
        timestamp = lines[0].replace("- Timestamp: ", "").strip()
        pattern = r'\b(?:[0-9]|[0-9]{2}):[0-5][0-9]:[0-5][0-9]\b'

        timestamp = re.findall(pattern, timestamp)
        if len(timestamp):
            timestamp = timestamp[0]
        reason = lines[1].replace("- Reason: ", "").strip()
        unique_data[timestamp] = reason

    parsed_data = [[timestamp, reason] for timestamp, reason in unique_data.items()]
    
    return parsed_data


def group_timestamps_with_reasons(data, interval_sec=60):
    # Extract timestamps and convert them to datetime objects
    time_objects = [(datetime.strptime(ts, "%H:%M:%S"), reason) for ts, reason in data]
    grouped = []
    previous_time = None

    for current_time, reason in time_objects:
        # If this is the first timestamp or the time difference is >= 1 minute, add to the group
        if previous_time is None or current_time - previous_time >= timedelta(seconds=interval_sec):
            grouped.append((current_time, reason))
        previous_time = current_time

    # Convert grouped datetime objects back to strings
    grouped_timestamps = [(time.strftime("%H:%M:%S"), reason) for time, reason in grouped]
    return grouped_timestamps

