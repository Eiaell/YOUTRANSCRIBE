import os
import sys
import argparse
import yt_dlp
import whisper
from pathvalidate import sanitize_filename

TRANSCRIPTIONS_DIR = "transcriptions"

def transcribe_youtube_video(youtube_url, model_name):
    """Downloads audio from a YouTube video and transcribes it to Markdown."""
    try:
        # 1. Get video metadata using yt-dlp
        print("Fetching video metadata...")
        ydl_info_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_info_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=False)

        # Handle potential playlists by taking the first video
        if 'entries' in info_dict:
            info_dict = info_dict['entries'][0]

        if not isinstance(info_dict, dict):
            print(f"Error: yt-dlp returned unexpected data format: {type(info_dict)}")
            return

        video_title = info_dict.get('title', 'Untitled')
        sanitized_title = sanitize_filename(video_title)
        
        # Define full paths for audio files
        audio_filename_template = os.path.join(os.getcwd(), f"{sanitized_title}.%(ext)s")
        audio_filepath = os.path.join(os.getcwd(), f"{sanitized_title}.mp3")

        # 2. Download audio using the sanitized title
        print(f"Downloading audio for: {video_title}")
        ydl_download_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': audio_filename_template,
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_download_opts) as ydl:
            ydl.download([youtube_url])
        
        print("Audio download complete.")

        # 3. Transcribe audio using Whisper
        print(f"Loading Whisper model '{model_name}'...")
        model = whisper.load_model(model_name)
        
        print("Transcribing audio... (This may take a while)")
        result = model.transcribe(audio_filepath, verbose=True)
        
        # 4. Save transcription as a Markdown file
        markdown_content = f"# {video_title}\n\n"
        markdown_content += result["text"]

        markdown_filename = f"{sanitized_title}.md"
        markdown_path = os.path.join(TRANSCRIPTIONS_DIR, markdown_filename)
        
        os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"Transcription saved to: {markdown_path}")

        # 5. Clean up the downloaded audio file
        if os.path.exists(audio_filepath):
            os.remove(audio_filepath)
            print(f"Cleaned up temporary audio file: {audio_filepath}")

    except yt_dlp.utils.DownloadError as e:
        print(f"Error downloading video: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description="Transcribe a YouTube video using Whisper.")
    parser.add_argument("url", help="The URL of the YouTube video.")
    parser.add_argument("-m", "--model", default="base", help="The Whisper model to use (e.g., tiny, base, small, medium, large).")
    
    # Check if any arguments were passed
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    
    transcribe_youtube_video(args.url, args.model)

if __name__ == "__main__":
    main()