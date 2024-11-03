from flask import Flask, request, jsonify, send_from_directory
import yt_dlp
import os
import threading
import schedule
import time

app = Flask(__name__)

def download_video(url, file_type):
    try:
        # Step 1: Set up output directory
        output_path = 'audio' if file_type == 'mp3' else 'video'
        
        # Step 2: Create directory if it doesn't exist
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            
        # Step 3: Check write permissions
        if not os.access(output_path, os.W_OK):
            return {"error": "The output path is not writable."}

        # Step 4: Configure download options
        ydl_opts = {}
        
        # Step 5: For MP3 downloads
        if file_type == "mp3":
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(output_path, '%(title)s.mp3'),
                'cookiefile': 'youtube_cookies.txt'
            }
            
        # Step 6: For MP4 downloads (360p)
        elif file_type == "mp4":
            ydl_opts = {
                # This line specifies 360p quality
                'format': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'cookiefile': 'youtube_cookies.txt',
                'merge_output_format': 'mp4'
            }
            
        # Step 7: Handle invalid file type
        else:
            return {"error": "Invalid file type. Please choose 'mp3' or 'mp4'."}

        # Step 8: Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info_dict)
            file_name = os.path.basename(file_name)
            return {"message": "Download successful", "file_name": file_name}

    # Step 9: Handle errors
    except yt_dlp.utils.DownloadError as e:
        return {"error": f"Download error: {str(e)}"}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

@app.route('/download', methods=['GET'])
def download():
    url = request.args.get('url')
    file_type = request.args.get('type')

    result = download_video(url, file_type)
    if "error" in result:
        return jsonify(result), 400

    file_name = result["file_name"]
    file_type_folder = 'audio' if file_type == 'mp3' else 'video'
    return jsonify({"download_url": f"{file_type_folder}/{file_name}"})

@app.route('/audio/<filename>', methods=['GET'])
def get_audio_file(filename):
    return send_from_directory('audio', filename)

@app.route('/video/<filename>', methods=['GET'])
def get_video_file(filename):
    return send_from_directory('video', filename)

def clear_files():
    folders = ['audio', 'video']
    for folder in folders:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    print(f"Deleted {file_path}")
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {str(e)}")

def schedule_clear_files():
    schedule.every(20).minutes.do(clear_files)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    # Start the file cleanup scheduler in a separate thread
    cleanup_thread = threading.Thread(target=schedule_clear_files)
    cleanup_thread.daemon = True
    cleanup_thread.start()

    app.run(port=3000)
