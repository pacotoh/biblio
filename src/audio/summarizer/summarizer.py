from moviepy.editor import VideoFileClip
import os


VIDEO_PATH = 'video/'
AUDIO_PATH = 'audio/'
TEXT_PATH = 'text/'


def extract_audio() -> None:
    videos = os.listdir(VIDEO_PATH)
    for video_name in videos:
        video = VideoFileClip(f'{VIDEO_PATH}{video_name}')
        audio = video.audio
        audio.write_audiofile(f'{AUDIO_PATH}{video_name.split(".")[0]}.ogg')


def transcribe_audio() -> None:
    # TODO: Use whisper to transcribe audio and save into text
    pass


if __name__ == '__main__':
    extract_audio()
