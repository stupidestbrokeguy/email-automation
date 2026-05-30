"""
Creative Daily - Thumbnail from Visible PNG Portion at t=1 second
- Takes ONLY the part of PNG visible on screen at t=1 second
- Removes yellow background from ALL sides
- Stretches content to fill all 4 corners of 1920x1080
- NO yellow, NO black bars, just image content
"""

import os
import re
import sys
import pickle
import socket
import numpy as np
from datetime import datetime
import fitz  # PyMuPDF

# ========== CONFIGURATION ==========
PLAYLIST_TITLE = "Creative Daily | Stupid Orange | Stupidest Broke Guy"
PLAYLIST_DESCRIPTION = """Welcome to the Official Playlist of the Creative Daily from Stupid Orange. Here you will keep up to date with the message from Stupidest Broke Guy helping people to start collecting royalties from their creativity and live a true royal lifestyle.

#Dubai #creativedaily #stupidestbrokeguy #UAE"""

# Video settings
VIDEO_DURATION = 18                     # Seconds
ZOOM_FACTOR = 2.5                       # Zoom level
BACKGROUND_COLOR = (255, 215, 0)        # Yellow background

# Start position - adjust this to control what part of PNG is visible at t=0
# Lower number = less visible, Higher number = more visible
START_Y_POSITION = 780                  # ← CHANGE THIS

EASING = "ease_in_out"                  # Animation easing

# Thumbnail settings
THUMBNAIL_CAPTURE_TIME = 1.0            # Capture thumbnail at t=1 second (or adjust)
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

def get_position_at_time(t: float, start_y: float, end_y: float, duration: float, easing: str = "ease_in_out") -> float:
    """Calculate Y position at specific time t using same easing as video"""
    progress = min(1.0, t / duration)
    
    if easing == "linear":
        eased = progress
    elif easing == "ease_in":
        eased = progress * progress
    elif easing == "ease_out":
        eased = 1 - (1 - progress) ** 2
    else:  # ease_in_out
        eased = progress * progress * (3 - 2 * progress)
    
    return start_y + (end_y - start_y) * eased

def create_thumbnail_from_visible_area(image_path: str, start_y_position: float, capture_time: float = 1.0, 
                                       output_path: str = None, target_size: tuple = (1920, 1080)) -> str:
    """
    Create thumbnail from ONLY the part of PNG visible on screen at t=capture_time.
    Crops out yellow from ALL sides. Stretches content to fill all 4 corners.
    """
    print(f"\n🎬 Creating thumbnail from visible area at t={capture_time} second...")
    print(f"   📷 Source: {image_path}")
    print(f"   📐 Target: {target_size[0]}x{target_size[1]} (stretch to fill)")
    print(f"   🟡 Cropping out yellow from ALL sides")
    
    if output_path is None:
        output_path = image_path.replace('.png', f'_thumbnail_t{capture_time}.png')
    
    try:
        from PIL import Image
        
        # Get position at capture time
        video_duration = VIDEO_DURATION
        end_y = 0
        current_y = get_position_at_time(capture_time, start_y_position, end_y, video_duration, EASING)
        print(f"   📍 Y position at t={capture_time}: {current_y:.1f}")
        
        img = Image.open(image_path)
        img_array = np.array(img)
        original_height, original_width = img_array.shape[:2]
        print(f"   📸 Original PNG: {original_width}x{original_height}")
        
        # Calculate visible portion at this time (MATCHING VIDEO RENDERING)
        screen_width, screen_height = 1920, 1080
        fit_scale = min(screen_width / original_width, screen_height / original_height)
        scale = fit_scale * ZOOM_FACTOR
        scaled_height = int(original_height * scale)
        scaled_width = int(original_width * scale)
        
        print(f"   🔍 Scale factor: {scale:.3f}")
        print(f"   📐 Scaled dimensions: {scaled_width}x{scaled_height}")
        
        # Calculate which part of original PNG is visible at current_y
        # The image clip is positioned with its top edge at current_y (screen coordinates)
        # So the visible portion in original PNG coordinates is:
        # crop_top = max(0, -current_y / scale) when current_y is negative
        # crop_bottom = min(original_height, (screen_height - current_y) / scale)
        
        if current_y < 0:
            # Image is positioned off-screen top (partially visible)
            crop_top = int(abs(current_y) / scale)
            visible_height_screen = min(screen_height, scaled_height + current_y)
        else:
            # Image starts below screen top
            crop_top = 0
            visible_height_screen = min(screen_height - current_y, scaled_height)
        
        crop_bottom = int(crop_top + (visible_height_screen / scale))
        
        # Ensure bounds
        crop_top = max(0, min(crop_top, original_height))
        crop_bottom = max(0, min(crop_bottom, original_height))
        
        print(f"   ✂️ Visible PNG portion: Y={crop_top} to Y={crop_bottom} (height: {crop_bottom - crop_top}px)")
        
        # Crop to visible portion
        visible_portion = img.crop((0, crop_top, original_width, crop_bottom))
        
        # Remove yellow background from ALL sides
        visible_array = np.array(visible_portion)
        
        # Define yellow range (adjust these values based on your actual yellow)
        yellow_lower = np.array([200, 180, 0])
        yellow_upper = np.array([255, 240, 100])
        
        # Create mask for non-yellow pixels
        is_not_yellow = np.any((visible_array < yellow_lower) | (visible_array > yellow_upper), axis=2)
        
        if len(is_not_yellow.shape) == 3:
            is_not_yellow = is_not_yellow[:, :, 0]
        
        non_yellow_coords = np.argwhere(is_not_yellow)
        
        if len(non_yellow_coords) > 0:
            # Get bounding box of non-yellow content
            y_min = non_yellow_coords[:, 0].min()
            y_max = non_yellow_coords[:, 0].max()
            x_min = non_yellow_coords[:, 1].min()
            x_max = non_yellow_coords[:, 1].max()
            
            # Add small padding (2 pixels)
            padding = 2
            y_min = max(0, y_min - padding)
            y_max = min(visible_array.shape[0], y_max + padding)
            x_min = max(0, x_min - padding)
            x_max = min(visible_array.shape[1], x_max + padding)
            
            # Crop to content only (no yellow)
            content_only = visible_portion.crop((x_min, y_min, x_max, y_max))
            print(f"   ✂️ Content only (yellow removed): {content_only.size}")
            print(f"   📦 Content bounding box: x={x_min}-{x_max}, y={y_min}-{y_max}")
        else:
            content_only = visible_portion
            print(f"   ⚠️ No yellow detected - using full visible portion")
        
        # STRETCH to fill target (touches all 4 corners)
        # Using LANCZOS for high quality
        stretched_img = content_only.resize(target_size, Image.Resampling.LANCZOS)
        print(f"   📐 Stretched to fill all corners: {stretched_img.size}")
        
        # Ensure no transparency (fill with black if any alpha)
        if stretched_img.mode == 'RGBA':
            background = Image.new('RGB', stretched_img.size, (0, 0, 0))
            background.paste(stretched_img, mask=stretched_img.split()[3])
            stretched_img = background
        
        stretched_img.save(output_path, quality=95)
        print(f"   ✅ Thumbnail saved: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_sliding_animation_video(image_path: str, output_path: str = None,
                                    bg_color: tuple = BACKGROUND_COLOR,
                                    slide_duration: int = VIDEO_DURATION,
                                    audio_file: str = None,
                                    start_y: float = START_Y_POSITION) -> str:
    """Create video starting at specified Y position."""
    
    if output_path is None:
        output_path = image_path.replace('.png', '_video.mp4')
    
    print(f"\n🎬 Creating video...")
    print(f"   📷 Image: {image_path}")
    print(f"   ⏱️  Duration: {slide_duration}s")
    print(f"   📍 t=0 position: Y={start_y}")
    
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
        
        fit_scale = min(screen_width / img_width, screen_height / img_height)
        scale = fit_scale * ZOOM_FACTOR
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        try:
            pil_img_resized = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        except AttributeError:
            pil_img_resized = pil_img.resize((new_width, new_height))
        
        temp_img_path = image_path.replace('.png', '_temp_resized.png')
        pil_img_resized.save(temp_img_path)
        
        image_clip = ImageClip(temp_img_path, duration=slide_duration)
        
        end_y = 0
        
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
                        break
                    except:
                        pass
        
        if not audio_added:
            print(f"   ℹ️ No audio - video will be silent")
        
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
            
            # Create thumbnail from visible PNG portion at t=THUMBNAIL_CAPTURE_TIME
            image_path = video_path.replace('_video.mp4', '.png')
            thumbnail_path = create_thumbnail_from_visible_area(
                image_path, 
                START_Y_POSITION, 
                capture_time=THUMBNAIL_CAPTURE_TIME,  # ← NOW USING 1 SECOND
                target_size=(1920, 1080)
            )
            
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    youtube.thumbnails().set(
                        videoId=response['id'],
                        media_body=MediaFileUpload(thumbnail_path)
                    ).execute()
                    print(f"   ✅ Thumbnail uploaded (visible PNG portion at t={THUMBNAIL_CAPTURE_TIME}s, yellow removed, stretched to fill)")
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
        print(f"🎬 Start Y: {START_Y_POSITION} (controls visible PNG portion at t=0)")
        print(f"🎬 Thumbnail capture at t={THUMBNAIL_CAPTURE_TIME} second")
        print("🎬 Thumbnail: Visible PNG portion only, yellow removed, stretched to fill")
        print("="*60)
        print(f"📅 Target Date: {target_date}")
        print(f"⏱️  Duration: {slide_duration}s")
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
            audio_file=audio_file,
            start_y=START_Y_POSITION
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
    print(f"🎬 Start Y: {START_Y_POSITION}")
    print(f"🎬 Thumbnail capture at t={THUMBNAIL_CAPTURE_TIME} second")
    
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
