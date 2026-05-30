"""
Creative Daily - Complete with Full Debug & Thumbnail Support
Extracts from PDF, creates sliding animation video, uploads to YouTube
"""

import os
import re
import sys
import pickle
import socket
import random
from datetime import datetime
import fitz  # PyMuPDF

# ========== CONFIGURATION ==========
PLAYLIST_TITLE = "Creative Daily | Stupid Orange | Stupidest Broke Guy"
PLAYLIST_DESCRIPTION = """Welcome to the Official Playlist of the Creative Daily from Stupid Orange. Here you will keep up to date with the message from Stupidest Broke Guy helping people to start collecting royalties from their creativity and live a true royal lifestyle.

#Dubai #creativedaily #stupidestbrokeguy #UAE"""
# ===================================

def find_free_port(start_port=8080, end_port=8090):
    for port in range(start_port, end_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except socket.error:
                continue
    return 8080

def extract_date_from_top_of_page(page_text: str) -> str:
    patterns = [
        r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})',
    ]
    
    lines = page_text.split('\n')
    for line in lines[:10]:
        line = line.strip()
        if not line:
            continue
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()
                try:
                    if groups[0].isdigit() and len(groups[0]) <= 2:
                        day = int(groups[0])
                        month_str = groups[1]
                        year = int(groups[2])
                    else:
                        month_str = groups[0]
                        day = int(groups[1])
                        year = int(groups[2])
                    
                    month_map = {'January':1,'February':2,'March':3,'April':4,'May':5,'June':6,'July':7,'August':8,'September':9,'October':10,'November':11,'December':12}
                    month = month_map.get(month_str, 1)
                    date_obj = datetime(year, month, day)
                    return date_obj.strftime("%Y-%m-%d")
                except:
                    continue
    return None

# ========== WORKING THUMBNAIL FUNCTION (AS PROVIDED) ==========
def extract_thumbnail_from_video(video_path: str, output_path: str = None, time_seconds: float = 2.0) -> str:
    """
    Extract thumbnail from video - cropping to JUST the image content (no yellow background)
    
    At 0 seconds, the image is positioned starting from bottom center.
    This function extracts just the image region, removing the yellow background.
    
    Args:
        video_path: Path to video file
        output_path: Where to save thumbnail (auto-generated if None)
        time_seconds: Time in seconds to capture frame (default 0.0 = first frame)
    
    Returns:
        Path to saved thumbnail image (image-only, cropped)
    """
    print(f"\n🎬 DEBUG: extract_thumbnail_from_video START")
    print(f"   📹 Video: {video_path}")
    print(f"   ⏱️  Time: {time_seconds} seconds")
    
    if output_path is None:
        output_path = video_path.replace('.mp4', '_thumbnail.png')
    
    try:
        # Try using moviepy first
        from moviepy import VideoFileClip
        print(f"   ✅ Using moviepy for thumbnail extraction")
        
        clip = VideoFileClip(video_path)
        frame = clip.get_frame(time_seconds)
        clip.close()
        
        from PIL import Image
        import numpy as np
        
        # Convert frame to PIL Image
        img = Image.fromarray(frame.astype('uint8'), 'RGB')
        
        print(f"   📸 Original frame size: {img.size}")
        
        # Detect and crop out the yellow background
        # The yellow background is RGB (255, 215, 0)
        # We'll find where the image content starts and ends
        
        # Convert to numpy array for analysis
        img_array = np.array(img)
        
        # Define yellow color range (with some tolerance)
        yellow_lower = np.array([240, 200, 0])   # Lower bound for yellow
        yellow_upper = np.array([255, 230, 50])  # Upper bound for yellow
        
        # Find non-yellow pixels (these are the image content)
        is_not_yellow = np.any((img_array < yellow_lower) | (img_array > yellow_upper), axis=2)
        
        # Find bounding box of non-yellow pixels
        non_yellow_coords = np.argwhere(is_not_yellow)
        
        if len(non_yellow_coords) > 0:
            y_min = non_yellow_coords[:, 0].min()
            y_max = non_yellow_coords[:, 0].max()
            x_min = non_yellow_coords[:, 1].min()
            x_max = non_yellow_coords[:, 1].max()
            
            # Add small padding (optional)
            padding = 5
            y_min = max(0, y_min - padding)
            y_max = min(img.height, y_max + padding)
            x_min = max(0, x_min - padding)
            x_max = min(img.width, x_max + padding)
            
            # Crop to just the image content
            cropped_img = img.crop((x_min, y_min, x_max, y_max))
            print(f"   ✂️ Cropped to: {cropped_img.size} (removed yellow background)")
            
            cropped_img.save(output_path, quality=90)
        else:
            # Fallback: save full frame if detection fails
            print(f"   ⚠️ Could not detect image content, saving full frame")
            img.save(output_path, quality=90)
        
        print(f"   ✅ Thumbnail saved: {output_path} ({os.path.getsize(output_path)} bytes)")
        
    except ImportError:
        try:
            # Fallback to OpenCV
            import cv2
            print(f"   ✅ Using OpenCV for thumbnail extraction")
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception("Cannot open video")
            
            # Set frame position
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_num = int(time_seconds * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            
            ret, frame = cap.read()
            if ret:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                
                # Same cropping logic as above
                img_array = np.array(img)
                yellow_lower = np.array([240, 200, 0])
                yellow_upper = np.array([255, 230, 50])
                is_not_yellow = np.any((img_array < yellow_lower) | (img_array > yellow_upper), axis=2)
                non_yellow_coords = np.argwhere(is_not_yellow)
                
                if len(non_yellow_coords) > 0:
                    y_min = non_yellow_coords[:, 0].min()
                    y_max = non_yellow_coords[:, 0].max()
                    x_min = non_yellow_coords[:, 1].min()
                    x_max = non_yellow_coords[:, 1].max()
                    
                    padding = 5
                    y_min = max(0, y_min - padding)
                    y_max = min(img.height, y_max + padding)
                    x_min = max(0, x_min - padding)
                    x_max = min(img.width, x_max + padding)
                    
                    cropped_img = img.crop((x_min, y_min, x_max, y_max))
                    cropped_img.save(output_path, quality=90)
                else:
                    cv2.imwrite(output_path, frame)
                
                print(f"   ✅ Thumbnail saved: {output_path}")
            else:
                raise Exception("Cannot read frame")
            
            cap.release()
            
        except ImportError:
            # Fallback to ffmpeg with cropping
            print(f"   ✅ Using ffmpeg for thumbnail extraction")
            import subprocess
            
            # First extract frame
            temp_frame = output_path.replace('.png', '_temp_frame.png')
            cmd_extract = [
                'ffmpeg', '-y',
                '-ss', str(time_seconds),
                '-i', video_path,
                '-vframes', '1',
                '-q:v', '2',
                temp_frame
            ]
            
            result = subprocess.run(cmd_extract, capture_output=True, text=True)
            if result.returncode == 0:
                # Now crop using PIL
                from PIL import Image
                import numpy as np
                
                img = Image.open(temp_frame)
                img_array = np.array(img)
                yellow_lower = np.array([240, 200, 0])
                yellow_upper = np.array([255, 230, 50])
                is_not_yellow = np.any((img_array < yellow_lower) | (img_array > yellow_upper), axis=2)
                non_yellow_coords = np.argwhere(is_not_yellow)
                
                if len(non_yellow_coords) > 0:
                    y_min = non_yellow_coords[:, 0].min()
                    y_max = non_yellow_coords[:, 0].max()
                    x_min = non_yellow_coords[:, 1].min()
                    x_max = non_yellow_coords[:, 1].max()
                    
                    padding = 5
                    y_min = max(0, y_min - padding)
                    y_max = min(img.height, y_max + padding)
                    x_min = max(0, x_min - padding)
                    x_max = min(img.width, x_max + padding)
                    
                    cropped_img = img.crop((x_min, y_min, x_max, y_max))
                    cropped_img.save(output_path, quality=90)
                else:
                    img.save(output_path, quality=90)
                
                # Cleanup
                if os.path.exists(temp_frame):
                    os.remove(temp_frame)
                
                print(f"   ✅ Thumbnail saved: {output_path}")
            else:
                raise Exception(f"ffmpeg error: {result.stderr}")
    
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path) / 1024
        print(f"   📁 Thumbnail size: {file_size:.1f} KB")
        print(f"🎬 DEBUG: extract_thumbnail_from_video COMPLETE")
        return output_path
    else:
        print(f"   ❌ Failed to extract thumbnail")
        return None

def create_sliding_animation_video(image_path: str, text_content: str = None,
                                    output_path: str = None,
                                    bg_color: tuple = (255, 215, 0),
                                    slide_duration: int = 18,
                                    audio_file: str = None) -> str:
    if output_path is None:
        output_path = image_path.replace('.png', '_video.mp4')
    
    try:
        from moviepy import ImageClip, CompositeVideoClip, ColorClip
        from moviepy.audio.io.AudioFileClip import AudioFileClip
    except ImportError:
        from moviepy.editor import ImageClip, CompositeVideoClip, ColorClip, AudioFileClip
    
    screen_width, screen_height = 1920, 1080
    
    try:
        from PIL import Image
        
        pil_img = Image.open(image_path)
        img_width, img_height = pil_img.size
        
        fit_scale = min(screen_width / img_width, screen_height / img_height)
        zoom_factor = 1.6
        scale = fit_scale * zoom_factor
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        try:
            pil_img_resized = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        except AttributeError:
            pil_img_resized = pil_img.resize((new_width, new_height))
        
        temp_img_path = image_path.replace('.png', '_temp_resized.png')
        pil_img_resized.save(temp_img_path)
        
        image_clip = ImageClip(temp_img_path, duration=slide_duration)
        start_y = screen_height
        end_y = -new_height + screen_height * 0.2
        
        def image_slide_position(t):
            progress = min(1.0, t / slide_duration)
            eased = progress * progress * (3 - 2 * progress)
            y = start_y + (end_y - start_y) * eased
            return ('center', y)
        
        image_clip = image_clip.with_position(image_slide_position)
        background = ColorClip(size=(screen_width, screen_height), color=bg_color, duration=slide_duration)
        final_clip = CompositeVideoClip([background, image_clip], size=(screen_width, screen_height))
        
        audio_added = False
        if audio_file and os.path.exists(audio_file):
            try:
                audio = AudioFileClip(audio_file)
                if audio.duration < slide_duration:
                    loops = int(slide_duration / audio.duration) + 1
                    audio = audio.loop(loops)
                audio = audio.subclipped(0, slide_duration)
                try:
                    audio = audio.with_volume_scaled(0.25)
                except:
                    pass
                final_clip = final_clip.with_audio(audio)
                audio_added = True
            except Exception as e:
                print(f"   ⚠️ Audio error: {e}")
        
        if not audio_added:
            default_audio = ["background_music.mp3", "audio.mp3", "music.mp3", "bgm.mp3"]
            for audio in default_audio:
                if os.path.exists(audio):
                    try:
                        audio_clip = AudioFileClip(audio)
                        if audio_clip.duration < slide_duration:
                            audio_clip = audio_clip.loop(int(slide_duration / audio_clip.duration) + 1)
                        audio_clip = audio_clip.subclipped(0, slide_duration)
                        final_clip = final_clip.with_audio(audio_clip)
                        audio_added = True
                        break
                    except:
                        pass
        
        audio_codec = 'aac' if audio_added else None
        final_clip.write_videofile(output_path, codec='libx264', audio_codec=audio_codec, fps=30, bitrate="5000k", preset='medium')
        final_clip.close()
        if os.path.exists(temp_img_path):
            os.remove(temp_img_path)
        
        return output_path
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


class CompleteCalendarExtractor:
    def __init__(self, pdf_path: str, output_dir: str = "extracted_date_pages"):
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.playlist_id = None

    def find_page_by_date(self, target_date: str) -> dict:
        if not os.path.exists(self.pdf_path):
            return None
        doc = fitz.open(self.pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            found_date = extract_date_from_top_of_page(text)
            if found_date and found_date == target_date:
                doc.close()
                return {'page_num': page_num, 'display_num': page_num + 1, 'date': target_date, 'text': text}
        doc.close()
        return None

    def convert_page_to_image(self, page_info: dict, dpi: int = 150) -> str:
        doc = fitz.open(self.pdf_path)
        page = doc[page_info['page_num']]
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        date_obj = datetime.strptime(page_info['date'], "%Y-%m-%d")
        filename = f"{date_obj.day}_{date_obj.strftime('%B')}_{date_obj.year}_page_{page_info['display_num']}.png"
        image_path = os.path.join(self.output_dir, filename)
        pix.save(image_path)
        text_file = image_path.replace('.png', '_text.txt')
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(page_info['text'])
        doc.close()
        return image_path

    def ensure_image_for_date(self, target_date: str, dpi: int = 150) -> dict:
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        pattern = f"{date_obj.day}_{date_obj.strftime('%B')}_{date_obj.year}_page_"
        if os.path.exists(self.output_dir):
            for file in os.listdir(self.output_dir):
                if file.startswith(pattern) and file.endswith('.png'):
                    return {'status': 'exists', 'image_path': os.path.join(self.output_dir, file)}
        page_info = self.find_page_by_date(target_date)
        if page_info is None:
            return {'status': 'not_found', 'image_path': None}
        image_path = self.convert_page_to_image(page_info, dpi)
        return {'status': 'extracted', 'image_path': image_path, 'page_num': page_info['display_num']}

    def get_page_text_content(self, image_path: str) -> str:
        text_file = image_path.replace('.png', '_text.txt')
        if os.path.exists(text_file):
            with open(text_file, 'r', encoding='utf-8') as f:
                return f.read()[:2000]
        return ""

    def create_or_get_playlist(self, youtube) -> str:
        playlists = youtube.playlists().list(part='snippet', mine=True, maxResults=50).execute()
        for playlist in playlists.get('items', []):
            if playlist['snippet']['title'] == PLAYLIST_TITLE:
                return playlist['id']
        response = youtube.playlists().insert(
            part='snippet,status',
            body={'snippet': {'title': PLAYLIST_TITLE, 'description': PLAYLIST_DESCRIPTION}, 'status': {'privacyStatus': 'public'}}
        ).execute()
        return response['id']

    def upload_to_youtube(self, video_path: str, target_date: str, page_text: str = "") -> dict:
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%B %d, %Y")
        title = f"Creative Daily | {formatted_date} | Stupid Orange | Stupidest Broke Guy"
        full_title = f"{title} | #creativedaily #stupidestbrokeguy #UAE #Dubai"
        description = f"""{page_text[:1500]}
📅 Creative Daily - {formatted_date}
👉 Share your stupid broke moment: www.stupidorange.com/share-moment/
👉 Get the Creative Daily: creativedaily.stupidorange.com
#creativedaily #stupidestbrokeguy #UAE #Dubai"""

        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload

            credentials = None
            if os.path.exists("token.pickle"):
                with open("token.pickle", 'rb') as f:
                    credentials = pickle.load(f)

            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", ["https://www.googleapis.com/auth/youtube.force-ssl"])
                    credentials = flow.run_local_server(port=find_free_port(), open_browser=True)
                with open("token.pickle", 'wb') as f:
                    pickle.dump(credentials, f)

            youtube = build('youtube', 'v3', credentials=credentials)
            if self.playlist_id is None:
                self.playlist_id = self.create_or_get_playlist(youtube)

            body = {
                'snippet': {'title': full_title[:100], 'description': description[:5000], 'tags': ['creativedaily', 'stupidestbrokeguy', 'Dubai', 'UAE', target_date], 'categoryId': '22'},
                'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
            }
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
            response = request.execute()
            video_url = f"https://youtu.be/{response['id']}"

            thumbnail_path = extract_thumbnail_from_video(video_path, time_seconds=2.0)
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    youtube.thumbnails().set(videoId=response['id'], media_body=MediaFileUpload(thumbnail_path)).execute()
                    os.remove(thumbnail_path)
                except Exception as e:
                    print(f"   ⚠️ Thumbnail error: {e}")

            youtube.playlistItems().insert(part='snippet', body={'snippet': {'playlistId': self.playlist_id, 'resourceId': {'kind': 'youtube#video', 'videoId': response['id']}}}).execute()
            return {'status': 'success', 'video_url': video_url}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}

    def process_date(self, target_date: str, post_to_youtube: bool = True, slide_duration: int = None, audio_file: str = None) -> dict:
        if slide_duration is None:
            slide_duration = random.randint(17, 21)
        print(f"\n📅 Creative Daily - {target_date} | Duration: {slide_duration}s")
        result = self.ensure_image_for_date(target_date)
        if result['status'] == 'not_found':
            return {'status': 'not_found'}
        page_text = self.get_page_text_content(result['image_path'])
        video_path = create_sliding_animation_video(result['image_path'], slide_duration=slide_duration, audio_file=audio_file)
        if video_path is None:
            return {'status': 'conversion_failed'}
        youtube_result = None
        if post_to_youtube:
            youtube_result = self.upload_to_youtube(video_path, target_date, page_text)
        return {'status': 'success', 'video_path': video_path, 'youtube': youtube_result}


if __name__ == "__main__":
    print("🎬 CREATIVE DAILY SCRIPT")
    PDF_PATH = "your_document.pdf"
    target_date = None
    for arg in sys.argv[1:]:
        if arg == "--no-youtube":
            post_to_youtube = False
        elif arg.startswith("--duration="):
            slide_duration = int(arg.split("=")[1])
        elif arg.startswith("--audio="):
            audio_file = arg.split("=")[1]
        elif re.match(r'\d{4}-\d{2}-\d{2}', arg):
            target_date = arg
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists(PDF_PATH):
        print(f"❌ PDF not found")
        sys.exit(1)
    processor = CompleteCalendarExtractor(PDF_PATH)
    result = processor.process_date(target_date, post_to_youtube, slide_duration, audio_file)
    if result['status'] == 'success':
        print(f"✅ SUCCESS!")
        if result.get('youtube') and result['youtube']['status'] == 'success':
            print(f"📹 {result['youtube']['video_url']}")
        sys.exit(0)
    else:
        print(f"❌ FAILED")
        sys.exit(1)
