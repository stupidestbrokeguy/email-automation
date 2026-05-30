"""
Creative Daily - Complete with Full Debug & Thumbnail Support
Extracts from PDF, creates sliding animation video, uploads to YouTube
FEATURES:
- Extracts date from top of page (Day Month Year format)
- 60% zoomed image for large readable text
- Yellow background
- Background music support
- THUMBNAIL: FIXED 25 seconds capture, LANDSCAPE format (1920x1080)
- Random video duration (17-21 seconds) - video only
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
    """Find a free port for OAuth callback"""
    for port in range(start_port, end_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except socket.error:
                continue
    return 8080

def extract_date_from_top_of_page(page_text: str) -> str:
    """
    Extract date from the top of the page
    Looks for patterns like: "1 June 2026", "2 June 2026", etc.
    Returns date in YYYY-MM-DD format
    """
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
                    
                    month_map = {
                        'January': 1, 'February': 2, 'March': 3, 'April': 4,
                        'May': 5, 'June': 6, 'July': 7, 'August': 8,
                        'September': 9, 'October': 10, 'November': 11, 'December': 12
                    }
                    month = month_map.get(month_str, 1)
                    
                    date_obj = datetime(year, month, day)
                    result = date_obj.strftime("%Y-%m-%d")
                    print(f"   ✅ Found date: {result}")
                    return result
                except:
                    continue
    return None

def extract_thumbnail_from_video(video_path: str, output_path: str = None, time_seconds: float = 5.0) -> str:
    """
    Extract thumbnail from video - FIXED at 25 seconds,
    crops yellow background, stretches to fill landscape format (1920x1080)
    """
    print(f"\n🎬 Extracting thumbnail from video...")
    print(f"   📹 Video: {video_path}")
    print(f"   ⏱️  Time: {time_seconds} seconds (FIXED)")
    print(f"   📐 Target format: Landscape (1920x1080) - standard YouTube thumbnail")
    
    if output_path is None:
        output_path = video_path.replace('.mp4', '_thumbnail.png')
    
    try:
        from moviepy import VideoFileClip
        from PIL import Image
        import numpy as np
        
        clip = VideoFileClip(video_path)
        
        # Check if video is long enough
        if clip.duration < time_seconds:
            print(f"   ⚠️ Video duration ({clip.duration:.1f}s) < {time_seconds}s, using last frame")
            time_seconds = clip.duration - 1.0
        
        frame = clip.get_frame(time_seconds)
        clip.close()
        
        # Convert frame to PIL Image
        img = Image.fromarray(frame.astype('uint8'), 'RGB')
        original_width, original_height = img.size
        print(f"   📸 Original frame size: {original_width}x{original_height}")
        
        # Detect yellow background and find the image content
        img_array = np.array(img)
        
        # Define yellow color range (with tolerance)
        yellow_lower = np.array([200, 180, 0])
        yellow_upper = np.array([255, 240, 100])
        
        # Find non-yellow pixels (the actual image content)
        is_not_yellow = np.any((img_array < yellow_lower) | (img_array > yellow_upper), axis=2)
        non_yellow_coords = np.argwhere(is_not_yellow)
        
        if len(non_yellow_coords) > 0:
            # Get bounding box of the image content
            y_min = non_yellow_coords[:, 0].min()
            y_max = non_yellow_coords[:, 0].max()
            x_min = non_yellow_coords[:, 1].min()
            x_max = non_yellow_coords[:, 1].max()
            
            # Add small padding
            padding = 5
            y_min = max(0, y_min - padding)
            y_max = min(original_height, y_max + padding)
            x_min = max(0, x_min - padding)
            x_max = min(original_width, x_max + padding)
            
            # Crop to JUST the image content
            cropped_img = img.crop((x_min, y_min, x_max, y_max))
            print(f"   ✂️ Cropped image size: {cropped_img.size}")
            
            # Target standard YouTube thumbnail size (LANDSCAPE 16:9)
            target_width, target_height = 1920, 1080
            
            # Stretch the cropped image to fill landscape format
            stretched_img = cropped_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            print(f"   📐 Stretched to LANDSCAPE: {stretched_img.size} (1920x1080)")
            
            stretched_img.save(output_path, quality=95)
        else:
            # If no yellow detected, stretch the full frame to landscape
            print(f"   ⚠️ No yellow background detected, stretching full frame to landscape")
            target_width, target_height = 1920, 1080
            stretched_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            stretched_img.save(output_path, quality=95)
        
        print(f"   ✅ Thumbnail saved: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"   ❌ Thumbnail extraction failed: {e}")
        return None

def create_sliding_animation_video(image_path: str, text_content: str = None,
                                    output_path: str = None,
                                    bg_color: tuple = (255, 215, 0),
                                    slide_duration: int = 18,
                                    audio_file: str = None) -> str:
    """Create video with image sliding up and audio"""
    
    if output_path is None:
        output_path = image_path.replace('.png', '_video.mp4')
    
    print(f"\n🎬 Creating video: {os.path.basename(image_path)}")
    print(f"   ⏱️  Duration: {slide_duration} seconds")
    
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
        
        # 60% ZOOM for larger, readable text
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
        
        # Create image clip with sliding animation
        image_clip = ImageClip(temp_img_path, duration=slide_duration)
        
        # Slide up from bottom
        start_y = screen_height
        end_y = -new_height + screen_height * 0.2
        
        def image_slide_position(t):
            progress = min(1.0, t / slide_duration)
            eased = progress * progress * (3 - 2 * progress)
            y = start_y + (end_y - start_y) * eased
            return ('center', y)
        
        image_clip = image_clip.with_position(image_slide_position)
        
        # Background
        background = ColorClip(size=(screen_width, screen_height), color=bg_color, duration=slide_duration)
        final_clip = CompositeVideoClip([background, image_clip], size=(screen_width, screen_height))
        
        # ========== AUDIO HANDLING ==========
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
                print(f"   🎵 Audio added: {audio_file}")
            except Exception as e:
                print(f"   ⚠️ Audio error: {e}")
        
        # Try default audio files
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
                        print(f"   🎵 Audio added from: {audio}")
                        break
                    except:
                        pass
        
        if not audio_added:
            print(f"   ℹ️ No audio added - video will be silent")
        
        # Render
        audio_codec = 'aac' if audio_added else None
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec=audio_codec,
            fps=30,
            bitrate="5000k",
            preset='medium'
        )
        
        final_clip.close()
        if os.path.exists(temp_img_path):
            os.remove(temp_img_path)
        
        print(f"   ✅ Video created: {os.path.basename(output_path)}")
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
        print(f"🔧 Initialized: {pdf_path} -> {output_dir}")

    def find_page_by_date(self, target_date: str) -> dict:
        """Find which page contains the target date"""
        print(f"🔍 Looking for date: {target_date}")
        
        if not os.path.exists(self.pdf_path):
            print(f"❌ PDF not found")
            return None
        
        doc = fitz.open(self.pdf_path)
        total_pages = len(doc)
        print(f"📄 PDF has {total_pages} pages")
        
        for page_num in range(total_pages):
            page = doc[page_num]
            text = page.get_text()
            found_date = extract_date_from_top_of_page(text)
            
            if found_date and found_date == target_date:
                print(f"   ✅ Found on page {page_num + 1}")
                doc.close()
                return {
                    'page_num': page_num,
                    'display_num': page_num + 1,
                    'date': target_date,
                    'text': text
                }
        
        doc.close()
        print(f"❌ Date {target_date} not found")
        return None

    def convert_page_to_image(self, page_info: dict, dpi: int = 150) -> str:
        print(f"   🖼️ Converting page {page_info['display_num']} to image")
        
        doc = fitz.open(self.pdf_path)
        page = doc[page_info['page_num']]

        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        date_obj = datetime.strptime(page_info['date'], "%Y-%m-%d")
        filename = f"{date_obj.day}_{date_obj.strftime('%B')}_{date_obj.year}_page_{page_info['display_num']}.png"
        image_path = os.path.join(self.output_dir, filename)

        pix.save(image_path)
        print(f"   💾 Saved: {filename}")

        text_file = image_path.replace('.png', '_text.txt')
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(page_info['text'])

        doc.close()
        return image_path

    def ensure_image_for_date(self, target_date: str, dpi: int = 150) -> dict:
        # Check existing
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        pattern = f"{date_obj.day}_{date_obj.strftime('%B')}_{date_obj.year}_page_"
        
        if os.path.exists(self.output_dir):
            for file in os.listdir(self.output_dir):
                if file.startswith(pattern) and file.endswith('.png'):
                    return {'status': 'exists', 'image_path': os.path.join(self.output_dir, file)}
        
        # Find and convert
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
            body={
                'snippet': {'title': PLAYLIST_TITLE, 'description': PLAYLIST_DESCRIPTION},
                'status': {'privacyStatus': 'public'}
            }
        ).execute()
        return response['id']

    def upload_to_youtube(self, video_path: str, target_date: str, page_text: str = "") -> dict:
        print(f"\n📤 Uploading to YouTube...")

        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%B %d, %Y")
        
        title = f"Creative Daily | {formatted_date} | Stupid Orange | Stupidest Broke Guy"
        full_title = f"{title} | #creativedaily #stupidestbrokeguy #UAE #Dubai"

        description = f"""{page_text[:1500]}

📅 Creative Daily - {formatted_date}

👉 Share your stupid broke moment: www.stupidorange.com/share-moment/
👉 Get the Creative Daily: creativedaily.stupidorange.com

#creativedaily #stupidestbrokeguy #UAE #Dubai
"""

        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload

            SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
            credentials = None

            if os.path.exists("token.pickle"):
                with open("token.pickle", 'rb') as f:
                    credentials = pickle.load(f)
                print(f"   📂 Loaded saved credentials")

            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    print("   🔄 Refreshing token...")
                    credentials.refresh(Request())
                else:
                    if not os.path.exists("client_secrets.json"):
                        print(f"   ❌ No client_secrets.json found!")
                        return {'status': 'skipped', 'error': 'No credentials'}
                    
                    print("   🔐 Opening browser for authentication...")
                    flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
                    credentials = flow.run_local_server(port=find_free_port(), open_browser=True)
                
                with open("token.pickle", 'wb') as f:
                    pickle.dump(credentials, f)
                print(f"   💾 Saved credentials")

            youtube = build('youtube', 'v3', credentials=credentials)

            if self.playlist_id is None:
                self.playlist_id = self.create_or_get_playlist(youtube)

            body = {
                'snippet': {
                    'title': full_title[:100],
                    'description': description[:5000],
                    'tags': ['creativedaily', 'stupidestbrokeguy', 'Dubai', 'UAE', target_date],
                    'categoryId': '22'
                },
                'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
            }

            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
            response = request.execute()
            video_url = f"https://youtu.be/{response['id']}"
            print(f"   ✅ Uploaded! URL: {video_url}")

            # Extract and upload thumbnail - FIXED at 25 seconds, LANDSCAPE format
            thumbnail_path = extract_thumbnail_from_video(video_path, time_seconds=25.0)
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    youtube.thumbnails().set(
                        videoId=response['id'],
                        media_body=MediaFileUpload(thumbnail_path)
                    ).execute()
                    os.remove(thumbnail_path)
                    print(f"   ✅ Thumbnail uploaded (FIXED 25 seconds, LANDSCAPE 1920x1080)")
                except Exception as e:
                    print(f"   ⚠️ Thumbnail error: {e}")

            # Add to playlist
            youtube.playlistItems().insert(
                part='snippet',
                body={
                    'snippet': {
                        'playlistId': self.playlist_id,
                        'resourceId': {'kind': 'youtube#video', 'videoId': response['id']}
                    }
                }
            ).execute()
            print(f"   ✅ Added to playlist")

            return {'status': 'success', 'video_url': video_url}

        except Exception as e:
            print(f"   ❌ Upload error: {e}")
            return {'status': 'failed', 'error': str(e)}

    def process_date(self, target_date: str, post_to_youtube: bool = True, 
                     slide_duration: int = None, audio_file: str = None) -> dict:
        if slide_duration is None:
            slide_duration = random.randint(17, 21)
            print(f"🎲 Random video duration: {slide_duration}s (17-21 range)")
        
        print("="*60)
        print(f"📅 Creative Daily - {target_date}")
        print(f"⏱️  Video Duration: {slide_duration}s (random 17-21)")
        print(f"🖼️  Thumbnail: FIXED 25 seconds, LANDSCAPE (1920x1080)")
        print(f"🎵 Audio: {audio_file if audio_file else 'Auto-detect'}")
        print(f"📹 YouTube: {'ON' if post_to_youtube else 'OFF'}")
        print("="*60)

        # Get image for date
        result = self.ensure_image_for_date(target_date)
        if result['status'] == 'not_found':
            print(f"❌ Date {target_date} not found in PDF")
            return {'status': 'not_found', 'date': target_date}

        print(f"✅ Image ready: {os.path.basename(result['image_path'])}")

        # Extract content
        page_text = self.get_page_text_content(result['image_path'])

        # Create video
        video_path = create_sliding_animation_video(
            image_path=result['image_path'],
            slide_duration=slide_duration,
            audio_file=audio_file
        )

        if video_path is None:
            return {'status': 'conversion_failed', 'date': target_date}

        print(f"✅ Video created: {video_path}")

        # Upload to YouTube
        youtube_result = None
        if post_to_youtube:
            youtube_result = self.upload_to_youtube(video_path, target_date, page_text)

        return {
            'status': 'success',
            'date': target_date,
            'image_path': result['image_path'],
            'video_path': video_path,
            'page_num': result.get('page_num', 0),
            'youtube': youtube_result
        }


if __name__ == "__main__":
    print("="*60)
    print("🎬 CREATIVE DAILY SCRIPT")
    print("="*60)
    
    PDF_PATH = "your_document.pdf"
    OUTPUT_DIR = "extracted_date_pages"

    target_date = None
    post_to_youtube = True
    slide_duration = None
    audio_file = None

    # Parse arguments
    for arg in sys.argv[1:]:
        if arg == "--no-youtube":
            post_to_youtube = False
            print("📹 YouTube upload disabled")
        elif arg.startswith("--duration="):
            slide_duration = int(arg.split("=")[1])
            print(f"⏱️ Video duration set to {slide_duration}s")
        elif arg.startswith("--audio="):
            audio_file = arg.split("=")[1]
            print(f"🎵 Audio file: {audio_file}")
        elif arg.endswith(".mp3") and os.path.exists(arg):
            audio_file = arg
            print(f"🎵 Audio file detected: {audio_file}")
        elif re.match(r'\d{4}-\d{2}-\d{2}', arg):
            target_date = arg
            print(f"📅 Target date: {target_date}")

    # Default to random video duration (17-21 seconds)
    if slide_duration is None:
        slide_duration = random.randint(17, 21)
        print(f"🎲 Random video duration: {slide_duration}s (17-21 range)")

    # Default to today
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")
        print(f"📅 Using today: {target_date}")

    print(f"\n🎯 Final: {target_date}")
    print(f"   📹 Video duration: {slide_duration}s (RANDOM 17-21)")
    print(f"   🖼️ Thumbnail capture: FIXED 25 seconds, LANDSCAPE 1920x1080")

    # Check PDF
    if not os.path.exists(PDF_PATH):
        print(f"❌ PDF not found: {PDF_PATH}")
        sys.exit(1)
    
    pdf_size = os.path.getsize(PDF_PATH) / (1024 * 1024)
    print(f"✅ PDF: {PDF_PATH} ({pdf_size:.1f} MB)")

    # Process
    processor = CompleteCalendarExtractor(PDF_PATH, OUTPUT_DIR)
    result = processor.process_date(target_date, post_to_youtube, 
                                     slide_duration=slide_duration, 
                                     audio_file=audio_file)

    print("\n" + "="*60)
    print("📋 FINAL RESULT")
    print("="*60)

    if result['status'] == 'success':
        print(f"✅ SUCCESS!")
        print(f"   📅 Date: {result['date']}")
        print(f"   🎬 Video: {result.get('video_path', 'N/A')}")
        print(f"   ⏱️ Video length: {slide_duration}s")
        print(f"   🖼️ Thumbnail: FIXED 25 seconds, LANDSCAPE 1920x1080")
        
        if result.get('youtube') and result['youtube']['status'] == 'success':
            print(f"\n📹 POSTED TO YOUTUBE!")
            print(f"   🔗 URL: {result['youtube']['video_url']}")
        sys.exit(0)
    else:
        print(f"❌ FAILED: {result['status']}")
        sys.exit(1)
