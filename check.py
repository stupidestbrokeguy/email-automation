"""
Creative Daily - Complete with Full Debug & Thumbnail Support
Extracts from PDF, creates sliding animation video, uploads to YouTube
FEATURES:
- Full debug output for every step
- 60% zoomed image for large readable text
- Yellow background
- Background music support
- AUTO DATE MAPPING - assigns dates sequentially (Day 1 = start date)
- RANDOM VIDEO DURATION (17-21 seconds)
"""

import os
import re
import sys
import pickle
import socket
import random
from datetime import datetime, timedelta
import fitz  # PyMuPDF

# ========== CONFIGURATION ==========
PLAYLIST_TITLE = "Creative Daily | Stupid Orange | Stupidest Broke Guy"
PLAYLIST_DESCRIPTION = """Welcome to the Official Playlist of the Creative Daily from Stupid Orange. Here you will keep up to date with the message from Stupidest Broke Guy helping people to start collecting royalties from their creativity and live a true royal lifestyle.

#Dubai #creativedaily #stupidestbrokeguy #UAE"""
# ===================================

# Set a fixed start date for the Creative Daily series
# This is Day 1 of your Creative Daily (June 1, 2026)
CREATIVE_DAILY_START_DATE = datetime(2026, 6, 1)

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

def detect_page_title(page_text: str) -> str:
    """Detect title from page structure"""
    lines = page_text.split('\n')
    clean_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.isdigit() and not re.search(r'Page\s+\d+', line):
            clean_lines.append(line)
    
    # Look for the day's title (e.g., "1 June 2026" or similar)
    for i, line in enumerate(clean_lines):
        if "Creative Daily" in line or "creative daily" in line.lower():
            if i + 1 < len(clean_lines):
                return clean_lines[i + 1]
    
    return "Creative Daily"

def extract_thumbnail_from_video(video_path: str, output_path: str = None, time_seconds: float = 2.0) -> str:
    """Extract thumbnail from video - cropping to JUST the image content"""
    print(f"\n🎬 DEBUG: extract_thumbnail_from_video START")
    
    if output_path is None:
        output_path = video_path.replace('.mp4', '_thumbnail.png')
    
    try:
        from moviepy import VideoFileClip
        clip = VideoFileClip(video_path)
        frame = clip.get_frame(time_seconds)
        clip.close()
        
        from PIL import Image
        import numpy as np
        
        img = Image.fromarray(frame.astype('uint8'), 'RGB')
        
        # Detect and crop out yellow background
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
    """Create video with image sliding up"""
    
    if output_path is None:
        output_path = image_path.replace('.png', '_video.mp4')
    
    print(f"\n🎬 Creating video: {os.path.basename(image_path)}")
    print(f"   ⏱️  Duration: {slide_duration} seconds")
    
    try:
        from moviepy import ImageClip, CompositeVideoClip, ColorClip
        from moviepy.audio.io.AudioFileClip import AudioFileClip
    except ImportError:
        try:
            from moviepy.editor import ImageClip, CompositeVideoClip, ColorClip, AudioFileClip
        except ImportError as e:
            print(f"   ❌ moviepy import failed: {e}")
            return None
    
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
        
        # Audio
        audio_added = False
        if audio_file and os.path.exists(audio_file):
            try:
                audio = AudioFileClip(audio_file)
                if audio.duration < slide_duration:
                    loops = int(slide_duration / audio.duration) + 1
                    audio = audio.loop(loops)
                audio = audio.subclipped(0, slide_duration)
                final_clip = final_clip.with_audio(audio)
                audio_added = True
            except Exception as e:
                print(f"   ⚠️ Audio error: {e}")
        
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
        import traceback
        traceback.print_exc()
        return None


class CompleteCalendarExtractor:
    def __init__(self, pdf_path: str, output_dir: str = "extracted_date_pages"):
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.playlist_id = None
        self.page_date_map = {}  # Maps page index to date
        print(f"🔧 Initialized: {pdf_path} -> {output_dir}")

    def build_page_date_map(self):
        """Build mapping from page index to date (sequential)"""
        if not os.path.exists(self.pdf_path):
            print(f"❌ PDF not found: {self.pdf_path}")
            return False
        
        try:
            doc = fitz.open(self.pdf_path)
            total_pages = len(doc)
            print(f"📄 PDF has {total_pages} pages")
            
            # Map each page to a date (Day 1 = CREATIVE_DAILY_START_DATE)
            for page_num in range(total_pages):
                page_date = CREATIVE_DAILY_START_DATE + timedelta(days=page_num)
                date_str = page_date.strftime("%Y-%m-%d")
                self.page_date_map[date_str] = {
                    'page_num': page_num,
                    'display_num': page_num + 1,
                    'date': date_str,
                    'text': doc[page_num].get_text()
                }
                print(f"   📄 Page {page_num + 1} -> {date_str}")
            
            doc.close()
            print(f"✅ Mapped {len(self.page_date_map)} pages to dates")
            return True
            
        except Exception as e:
            print(f"❌ Error reading PDF: {e}")
            return False

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
        print(f"🔍 Looking for date: {target_date}")
        
        # Build mapping if not already done
        if not self.page_date_map:
            if not self.build_page_date_map():
                return {'status': 'not_found', 'image_path': None}
        
        if target_date in self.page_date_map:
            page_info = self.page_date_map[target_date]
            
            # Check if image already exists
            date_obj = datetime.strptime(target_date, "%Y-%m-%d")
            pattern = f"{date_obj.day}_{date_obj.strftime('%B')}_{date_obj.year}_page_"
            
            for file in os.listdir(self.output_dir):
                if file.startswith(pattern) and file.endswith('.png'):
                    print(f"   ✅ Found existing image: {file}")
                    return {'status': 'exists', 'image_path': os.path.join(self.output_dir, file)}
            
            # Create new image
            image_path = self.convert_page_to_image(page_info, dpi)
            return {'status': 'extracted', 'image_path': image_path, 'page_num': page_info['display_num']}
        else:
            print(f"❌ Date {target_date} not in range")
            return {'status': 'not_found', 'image_path': None}

    def get_page_text_content(self, image_path: str) -> str:
        text_file = image_path.replace('.png', '_text.txt')
        if os.path.exists(text_file):
            with open(text_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                cleaned = [line.strip() for line in lines if line.strip() and not line.strip().isdigit()]
                return '\n\n'.join(cleaned[:20])  # First 20 lines
        return ""

    def get_page_title(self, image_path: str) -> str:
        text_file = image_path.replace('.png', '_text.txt')
        if os.path.exists(text_file):
            with open(text_file, 'r', encoding='utf-8') as f:
                page_text = f.read()
                return detect_page_title(page_text)
        return "Creative Daily"

    def create_or_get_playlist(self, youtube) -> str:
        print(f"📁 Creating/getting playlist...")
        playlists = youtube.playlists().list(part='snippet', mine=True, maxResults=50).execute()
        
        for playlist in playlists.get('items', []):
            if playlist['snippet']['title'] == PLAYLIST_TITLE:
                print(f"   ✅ Found existing playlist")
                return playlist['id']

        response = youtube.playlists().insert(
            part='snippet,status',
            body={
                'snippet': {'title': PLAYLIST_TITLE, 'description': PLAYLIST_DESCRIPTION},
                'status': {'privacyStatus': 'public'}
            }
        ).execute()
        print(f"   ✅ Created playlist")
        return response['id']

    def upload_to_youtube(self, video_path: str, target_date: str, page_text: str = "", video_title: str = "") -> dict:
        print(f"\n📤 Uploading to YouTube...")

        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%B %d, %Y")

        if video_title and video_title != "Creative Daily":
            main_title = video_title
        else:
            main_title = f"Creative Daily | Day {date_obj.day} | {formatted_date}"

        full_title = f"{main_title} | Stupid Orange | Stupidest Broke Guy | #creativedaily #stupidestbrokeguy"

        video_description = f"""{page_text[:2000] if page_text else ''}

📅 Creative Daily - {formatted_date}

👉 Join the Stupid Solomon Fashion Line: www.stupidorange.com
👉 Get the latest Creative Daily: creativedaily.stupidorange.com

Follow:
🎬 YouTube: @stupidestbrokeguy
📱 TikTok: @stupidestbrokeguy

{full_title}
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

            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                else:
                    if not os.path.exists("client_secrets.json"):
                        return {'status': 'skipped', 'error': 'No credentials'}
                    
                    flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
                    credentials = flow.run_local_server(port=find_free_port(), open_browser=True)
                
                with open("token.pickle", 'wb') as f:
                    pickle.dump(credentials, f)

            youtube = build('youtube', 'v3', credentials=credentials)

            if self.playlist_id is None:
                self.playlist_id = self.create_or_get_playlist(youtube)

            body = {
                'snippet': {
                    'title': full_title[:100],
                    'description': video_description[:5000],
                    'tags': ['Dubai', 'creativedaily', 'stupidestbrokeguy', 'UAE', target_date],
                    'categoryId': '22'
                },
                'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
            }

            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
            response = request.execute()
            video_url = f"https://youtu.be/{response['id']}"
            print(f"   ✅ Uploaded! URL: {video_url}")

            # Upload thumbnail
            thumbnail_path = extract_thumbnail_from_video(video_path, time_seconds=0.0)
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    youtube.thumbnails().set(
                        videoId=response['id'],
                        media_body=MediaFileUpload(thumbnail_path)
                    ).execute()
                    os.remove(thumbnail_path)
                    print(f"   ✅ Thumbnail uploaded")
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
        # Random duration if not specified
        if slide_duration is None:
            slide_duration = random.randint(17, 21)
            print(f"🎲 Random duration: {slide_duration}s")
        
        print("="*60)
        print(f"📅 Creative Daily - {target_date}")
        print(f"⏱️  Duration: {slide_duration}s")
        print(f"📹 YouTube: {'ON' if post_to_youtube else 'OFF'}")
        print("="*60)

        # Get image for date
        result = self.ensure_image_for_date(target_date)
        if result['status'] == 'not_found':
            print(f"❌ Date {target_date} not available")
            return {'status': 'not_found', 'date': target_date}

        # Extract content
        page_text = self.get_page_text_content(result['image_path'])
        page_title = self.get_page_title(result['image_path'])

        # Create video
        video_path = create_sliding_animation_video(
            image_path=result['image_path'],
            slide_duration=slide_duration,
            audio_file=audio_file
        )

        if video_path is None:
            return {'status': 'conversion_failed', 'date': target_date}

        # Upload to YouTube
        youtube_result = None
        if post_to_youtube:
            youtube_result = self.upload_to_youtube(video_path, target_date, page_text, page_title)

        return {
            'status': 'success',
            'date': target_date,
            'image_path': result['image_path'],
            'video_path': video_path,
            'page_num': result.get('page_num', 0),
            'detected_title': page_title,
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
        elif arg.startswith("--duration="):
            slide_duration = int(arg.split("=")[1])
        elif arg.startswith("--audio="):
            audio_file = arg.split("=")[1]
        elif arg.endswith(".mp3") and os.path.exists(arg):
            audio_file = arg
        elif re.match(r'\d{4}-\d{2}-\d{2}', arg):
            target_date = arg

    # Default to random duration
    if slide_duration is None:
        slide_duration = random.randint(17, 21)
        print(f"🎲 Random duration: {slide_duration}s")

    # Default to today
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")
        print(f"📅 Using today: {target_date}")

    print(f"🎯 Target: {target_date}, Duration: {slide_duration}s")

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

    if result['status'] == 'success':
        print(f"\n✅ SUCCESS!")
        if result.get('youtube') and result['youtube']['status'] == 'success':
            print(f"📹 YouTube: {result['youtube']['video_url']}")
        sys.exit(0)
    else:
        print(f"\n❌ FAILED: {result['status']}")
        sys.exit(1)
