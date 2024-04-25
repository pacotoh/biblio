import torch
from moviepy.editor import VideoFileClip
import os
import whisper
import subprocess

VIDEO_PATH = 'video/'
AUDIO_PATH = 'audio/'
TEXT_PATH = 'text/'


def transcribe_video_command() -> None:
    videos = os.listdir(VIDEO_PATH)
    for video_name in videos:
        print(f'Running whisper transcription for {video_name}...')
        command = ["whisper",
                   "--model", "large",
                   "--language", "es",
                   "--task", "transcribe",
                   f"{VIDEO_PATH}{video_name}"]

        result = subprocess.run(command, capture_output=True, text=True)
        with open(f'{TEXT_PATH}{video_name}') as transcription:
            transcription.write(result.stdout)


def transcribe_video() -> None:
    videos = os.listdir(VIDEO_PATH)
    for video_name in videos:
        print(f'Running whisper transcription for {video_name}...')
        result = model.transcribe(f'{VIDEO_PATH}{video_name}')
        with open(f'{TEXT_PATH}{video_name}') as transcription:
            transcription.write(result['text'])


def extract_audio() -> None:
    videos = os.listdir(VIDEO_PATH)
    for video_name in videos:
        video = VideoFileClip(f'{VIDEO_PATH}{video_name}')
        audio = video.audio
        audio.write_audiofile(f'{AUDIO_PATH}{video_name.split(".")[0]}.ogg')


if __name__ == '__main__':
    if torch.cuda.is_available():
        model = whisper.load_model('large', device='cuda')
    else:
        model = whisper.load_model('small')

    transcribe_video()
