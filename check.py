"""
Creative Daily - Top Quarter Thumbnail + Reveal Animation
- Thumbnail: Top quarter of image ONLY, stretched to fill 1920x1080 (no yellow)
- Video: Starts with top quarter visible (matches thumbnail), reveals rest over time
"""

import os
import re
import sys
import pickle
import socket
from datetime import datetime
import fitz  # PyMuPDF

# ========== CONFIGURATION ==========
PLAYLIST_TITLE = "Creative Daily | Stupid Orange | Stupidest Broke Guy"
PLAYLIST_DESCRIPTION = """Welcome to the Official Playlist of the Creative Daily from Stupid Orange. Here you will keep up to date with the message from Stupidest Broke Guy helping people to start collecting royalties from their creativity and live a true royal lifestyle.

#Dubai #creativedaily #stupidestbrokeguy #UAE"""

# Video settings
VIDEO_DURATION = 18                     # Seconds
ZOOM_FACTOR = 1.6                       # Zoom level
START_VISIBLE_PERCENT = 25              # At t=0, only top 25% visible
BACKGROUND_COLOR = (255, 215, 0)        # Yellow background
EASING = "ease_in_out"                  # Animation easing

# Thumbnail settings
THUMBNAIL_SIZE = (1920, 1080)           # YouTube thumbnail size
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
    for line in lines[:15]:
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
                    return date_obj.strftime("%Y-%m-%d")
                except:
                    continue
    return None

def create_thumbnail_from_visible_area(image_path: str, output_path: str = None, target_size: tuple = (1920, 1080)) -> str:
    """
    Create thumbnail from ONLY the visible portion at t=0 (top quarter).
    Crops out yellow background, then stretches image content to fill entire canvas.
    NO BLACK BARS - image ONLY, fills all 4 corners.
    """
    print(f"\n🎬 Creating thumbnail from visible area (top quarter)...")
    print(f"   📷 Source: {image_path}")
    print(f"   📐 Target: {target_size[0]}x{target_size[1]} (fills all corners, no black bars)")
    
    if output_path is None:
        output_path = image_path.replace('.png', '_thumbnail.png')
    
    try:
        from PIL import Image
        
        img = Image.open(image_path)
        original_width, original_height = img.size
        print(f"   📸 Original: {original_width}x{original_height}")
        
        # Step 1: Crop to visible area at t=0 (top quarter)
        crop_height = int(original_height * START_VISIBLE_PERCENT / 100)
        visible_area = img.crop((0, 0, original_width, crop_height))
        print(f"   ✂️ Visible area (top {START_VISIBLE_PERCENT}%): {visible_area.size}")
        
        # Step 2: Stretch visible area to fill target size (touches all 4 corners)
        # This ensures NO yellow background and NO black bars
        stretched_img = visible_area.resize(target_size, Image.Resampling.LANCZOS)
        print(f"   📐 Stretched to fill target: {stretched_img.size}")
        
        stretched_img.save(output_path, quality=95)
        print(f"   ✅ Thumbnail saved (image only, fills all corners)")
        return output_path
        
    except Exception as e:
        print(f"   ❌ Error creating thumbnail: {e}")
        return None

def create_sliding_animation_video(image_path: str, output_path: str = None,
                                    bg_color: tuple = BACKGROUND_COLOR,
                                    slide_duration: int = VIDEO_DURATION,
                                    audio_file: str = None) -> str:
    """
    Create video where at t=0 only top quarter is visible (matches thumbnail).
    Reveals remaining image over time.
    """
    
    if output_path is None:
        output_path = image_path.replace('.png', '_video.mp4')
    
    print(f"\n🎬 Creating video...")
    print(f"   📷 Image: {image_path}")
    print(f"   ⏱️  Duration: {slide_duration}s")
    print(f"   📍 t=0: Top {START_VISIBLE_PERCENT}% visible (matches thumbnail)")
    
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
        
        # Apply zoom
        fit_scale = min(screen_width / img_width, screen_height / img_height)
        scale = fit_scale * ZOOM_FACTOR
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Resize image
        try:
            pil_img_resized = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        except AttributeError:
            pil_img_resized = pil_img.resize((new_width, new_height))
        
        temp_img_path = image_path.replace('.png', '_temp_resized.png')
        pil_img_resized.save(temp_img_path)
        
        # Create image clip
        image_clip = ImageClip(temp_img_path, duration=slide_duration)
        
        # ============================================================
        # ANIMATION: At t=0, only top quarter visible (matches thumbnail)
        # ============================================================
        
        # Calculate visible heights
        visible_height_start = (new_height * START_VISIBLE_PERCENT) / 100
        visible_height_end = new_height
        
        # Y positions to achieve the visible heights
        start_y = screen_height - visible_height_start
        end_y = screen_height - visible_height_end
        
        print(f"   📍 t=0 position: Y={start_y:.1f} (top {START_VISIBLE_PERCENT}% visible)")
        print(f"   📍 End position: Y={end_y:.1f} (full image visible)")
        
        def get_easing(progress):
            if EASING == "linear":
                return progress
            elif EASING == "ease_in":
                return progress * progress
            elif EASING == "ease_out":
                return 1 - (1 - progress) ** 2
            else:
                return progress * progress * (3 - 2 * progress)
        
        def image_slide_position(t):
            progress = min(1.0, t / slide_duration)
            eased = get_easing(progress)
            y = start_y + (end_y - start_y) * eased
            return ('center', y)
        
        image_clip = image_clip.with_position(image_slide_position)
        
        # Create yellow background (only visible in video while image reveals)
        background = ColorClip(size=(screen_width, screen_height), color=bg_color, duration=slide_duration)
        final_clip = CompositeVideoClip([background, image_clip], size=(screen_width, screen_height))
        
        # Audio handling
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
                print(f"   🎵 Audio added: {audio_file}")
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
                        print(f"   🎵 Audio added from: {audio}")
                        break
                    except:
                        pass
        
        if not audio_added:
            print(f"   ℹ️ No audio - video will be silent")
        
        # Render video
        print(f"   💾 Rendering video...")
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
        
        print(f"   ✅ Video created: {output_path}")
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
        if not os.path.exists(self.pdf_path):
            return None
        
        doc = fitz.open(self.pdf_path)
        total_pages = len(doc)
        print(f"📄 PDF has {total_pages} pages")
        
        for page_num in range(total_pages):
            page = doc[page_num]
            text = page.get_text()
            found_date = extract_date_from_top_of_page(text)
            if found_date and found_date == target_date:
                doc.close()
                return {
                    'page_num': page_num,
                    'display_num': page_num + 1,
                    'date': target_date,
                    'text': text
                }
        
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
                content = f.read()
                lines = content.split('\n')
                cleaned = [line.strip() for line in lines if line.strip() and not line.strip().isdigit()]
                return '\n\n'.join(cleaned[:20])
        return ""

    def get_page_title(self, image_path: str) -> str:
        text_file = image_path.replace('.png', '_text.txt')
        if os.path.exists(text_file):
            with open(text_file, 'r', encoding='utf-8') as f:
                page_text = f.read()
                lines = page_text.split('\n')
                for line in lines[:20]:
                    if line.strip() and not line.strip().isdigit():
                        return line.strip()
        return "Creative Daily"

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

    def upload_to_youtube(self, video_path: str, target_date: str, page_text: str = "", video_title: str = "") -> dict:
        print(f"\n📤 Uploading to YouTube...")

        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%B %d, %Y")
        
        if video_title and video_title != "Creative Daily":
            main_title = video_title
        else:
            main_title = f"Creative Daily | {formatted_date} | Stupid Orange | Stupidest Broke Guy"
        
        full_title = f"{main_title} | #creativedaily #stupidestbrokeguy #UAE #Dubai"
        
        video_description = f"""{page_text[:1500] if page_text else ''}

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
            
            # Create thumbnail from visible area ONLY (top quarter), stretched to fill canvas
            image_path = video_path.replace('_video.mp4', '.png')
            thumbnail_path = create_thumbnail_from_visible_area(image_path, target_size=THUMBNAIL_SIZE)
            
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    youtube.thumbnails().set(
                        videoId=response['id'],
                        media_body=MediaFileUpload(thumbnail_path)
                    ).execute()
                    print(f"   ✅ Thumbnail uploaded (visible area only, stretched to fill)")
                except Exception as e:
                    print(f"   ⚠️ Thumbnail error: {e}")
            
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
                     slide_duration: int = VIDEO_DURATION, audio_file: str = None) -> dict:
        print("="*60)
        print("📅 CREATIVE DAILY")
        print("🎬 Thumbnail: Visible area only (top quarter), stretched to fill 1920x1080")
        print("🎬 Video: t=0 matches thumbnail, reveals rest over time")
        print("="*60)
        print(f"📅 Target Date: {target_date}")
        print(f"⏱️  Duration: {slide_duration}s")
        print(f"🖼️  Thumbnail: Top {START_VISIBLE_PERCENT}% only, stretched to fill")
        print("="*60)
        
        result = self.ensure_image_for_date(target_date)
        if result['status'] == 'not_found':
            print(f"❌ Date {target_date} not found")
            return {'status': 'not_found', 'date': target_date}
        
        page_text = self.get_page_text_content(result['image_path'])
        page_title = self.get_page_title(result['image_path'])
        
        video_path = create_sliding_animation_video(
            image_path=result['image_path'],
            slide_duration=slide_duration,
            audio_file=audio_file
        )
        
        if video_path is None:
            return {'status': 'conversion_failed', 'date': target_date}
        
        youtube_result = None
        if post_to_youtube:
            youtube_result = self.upload_to_youtube(video_path, target_date, page_text, page_title)
        
        return {
            'status': 'success',
            'date': target_date,
            'video_path': video_path,
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
    audio_file = None
    
    for arg in sys.argv[1:]:
        if arg == "--no-youtube":
            post_to_youtube = False
        elif arg.startswith("--audio="):
            audio_file = arg.split("=")[1]
        elif arg.endswith(".mp3") and os.path.exists(arg):
            audio_file = arg
        elif re.match(r'\d{4}-\d{2}-\d{2}', arg):
            target_date = arg
    
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"🎯 Target: {target_date}")
    
    if not os.path.exists(PDF_PATH):
        print(f"❌ PDF not found: {PDF_PATH}")
        sys.exit(1)
    
    processor = CompleteCalendarExtractor(PDF_PATH, OUTPUT_DIR)
    result = processor.process_date(target_date, post_to_youtube, VIDEO_DURATION, audio_file)
    
    if result['status'] == 'success':
        print(f"\n✅ SUCCESS!")
        if result.get('youtube') and result['youtube']['status'] == 'success':
            print(f"   🔗 YouTube: {result['youtube']['video_url']}")
        sys.exit(0)
    else:
        print(f"❌ FAILED")
        sys.exit(1)
