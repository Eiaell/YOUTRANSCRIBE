import os
import sys
import argparse
import yt_dlp
from faster_whisper import WhisperModel
from pathvalidate import sanitize_filename
import concurrent.futures
import queue
import time

TRANSCRIPTIONS_DIR = "transcriptions"

def download_audio(youtube_url, download_queue):
    try:
        print(f"Queueing {youtube_url}")
        ydl_info_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_info_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=False)
        if 'entries' in info_dict:
            info_dict = info_dict['entries'][0]
        video_title = info_dict.get('title', 'Untitled')
        sanitized_title = sanitize_filename(video_title)
        audio_filename_template = os.path.join(os.getcwd(), f"{sanitized_title}.%(ext)s")

        print(f"Downloading {video_title}...")
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
        
        download_queue.put({"status": "success", "filepath": audio_filepath, "title": video_title})
        return f"SUCCESS: Downloaded {video_title}"
    except Exception as e:
        error_message = f"FAILED to download: {youtube_url} - Reason: {e}"
        download_queue.put({"status": "error", "message": error_message})
        return error_message

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
        print(f"Loading faster-whisper model '{model_name}'...")
        model = WhisperModel(model_name, device="cuda", compute_type="float16")
        
        print("Transcribing audio... (This may take a while)")
        start_time = time.perf_counter()
        segments, info = model.transcribe(audio_filepath, beam_size=5)
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        # 4. Save transcription as a Markdown file
        markdown_content = f"# {video_title}\n\n"
        for segment in segments:
            markdown_content += segment.text + " "

        markdown_filename = f"{sanitized_title}.md"
        markdown_path = os.path.join(TRANSCRIPTIONS_DIR, markdown_filename)
        
        os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"✓ Transcription for '{video_title}' completed in {duration:.2f} seconds.")

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

def transcribe_from_file(file_path, model_name):
    with open(file_path, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    if not urls:
        print("File is empty or contains no valid URLs.")
        return

    print(f"Loading faster-whisper model '{model_name}'...")
    model = WhisperModel(model_name, device="cuda", compute_type="float16")

    download_queue = queue.Queue()
    successful_transcriptions = 0
    failed_downloads = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_url = {executor.submit(download_audio, url, download_queue): url for url in urls}

        for future in concurrent.futures.as_completed(future_to_url):
            try:
                result_message = future.result()
                print(result_message)
            except Exception as exc:
                failed_downloads += 1
                print(f'URL {future_to_url[future]} generated an exception: {exc}')

    while not download_queue.empty():
        item = download_queue.get()
        if item["status"] == "success":
            try:
                print(f"Transcribing {item['title']}...")
                start_time = time.perf_counter()
                segments, info = model.transcribe(item["filepath"], beam_size=5)
                end_time = time.perf_counter()
                duration = end_time - start_time
                markdown_content = f"# {item['title']}\n\n"
                for segment in segments:
                    markdown_content += segment.text + " "
                markdown_filename = f"{sanitize_filename(item['title'])}.md"
                markdown_path = os.path.join(TRANSCRIPTIONS_DIR, markdown_filename)
                os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)
                with open(markdown_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                print(f"✓ Transcription for '{item['title']}' completed in {duration:.2f} seconds.")
                successful_transcriptions += 1
            except Exception as e:
                print(f"Error during transcription for {item['title']}: {e}")
            finally:
                if os.path.exists(item["filepath"]):
                    os.remove(item["filepath"])
        else:
            failed_downloads += 1
            print(item["message"]) # Print the FAILED message

    print(f"\nBatch process complete. {successful_transcriptions} successful, {failed_downloads} failed.")

def main():
    parser = argparse.ArgumentParser(description="Transcribe a YouTube video or a list of videos from a file.")
    parser.add_argument("url_or_file", help="The URL of the YouTube video or the path to a text file with a list of URLs.")
    parser.add_argument("-m", "--model", default="base", help="The Whisper model to use (e.g., tiny, base, small, medium, large).")
    
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    
    if os.path.isfile(args.url_or_file):
        transcribe_from_file(args.url_or_file, args.model)
    else:
        transcribe_youtube_video(args.url_or_file, args.model)

if __name__ == "__main__":
    main()