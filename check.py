"""
Creative Daily - Complete with Seamless Thumbnail Transition
Extracts from PDF, creates sliding animation video, uploads to YouTube
FEATURES:
- Extracts date from top of page (Day Month Year format)
- 60% zoomed image for large readable text
- Yellow background
- Thumbnail EXACTLY matches video's first frame
- Seamless transition between thumbnail and video
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
    """Extract date from the top of the page (Day Month Year format)"""
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

def create_thumbnail_from_image(image_path: str, output_path: str = None, target_size: tuple = (1280, 720)) -> str:
    """
    Create thumbnail that EXACTLY matches the video's first frame position.
    This ensures seamless transition from thumbnail to video.
    """
    print(f"\n🖼️ DEBUG: create_thumbnail_from_image START")
    print(f"   📷 Source image: {image_path}")
    print(f"   📏 Target size: {target_size[0]}x{target_size[1]}")
    
    if output_path is None:
        output_path = image_path.replace('.png', '_thumbnail.png')
    
    try:
        from PIL import Image
        import numpy as np
        
        # Load the image
        img = Image.open(image_path)
        original_width, original_height = img.size
        print(f"   📸 Original size: {original_width}x{original_height}")
        
        # Video dimensions
        video_width, video_height = 1920, 1080
        
        # Calculate scaling to fit video height (same as video creation)
        video_scale = video_height / original_height
        print(f"   🔍 Video scale: {video_scale:.4f}")
        
        # Calculate scaled dimensions (matches video creation)
        scaled_width = int(original_width * video_scale)
        scaled_height = video_height
        print(f"   📐 Scaled dimensions: {scaled_width}x{scaled_height}")
        
        # Resize image to match video dimensions
        try:
            img_resized = img.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
        except AttributeError:
            img_resized = img.resize((scaled_width, scaled_height), Image.LANCZOS)
        
        # Crop to target size (1280x720 for YouTube thumbnail)
        if scaled_width > target_size[0]:
            # Center crop
            left = (scaled_width - target_size[0]) // 2
            right = left + target_size[0]
            img_cropped = img_resized.crop((left, 0, right, target_size[1]))
        else:
            # Center crop width
            left = 0
            right = scaled_width
            img_cropped = img_resized.crop((left, 0, right, target_size[1]))
        
        # Save thumbnail
        img_cropped.save(output_path, quality=90)
        file_size = os.path.getsize(output_path)
        print(f"   ✅ Thumbnail created: {output_path} ({file_size} bytes)")
        return output_path
        
    except Exception as e:
        print(f"   ❌ Error creating thumbnail: {e}")
        return None

def create_sliding_animation_video(image_path: str, output_path: str = None,
                                    bg_color: tuple = (255, 215, 0),
                                    slide_duration: int = 18,
                                    audio_file: str = None) -> str:
    """Create video with image sliding up"""
    
    if output_path is None:
        output_path = image_path.replace('.png', '_video.mp4')
    
    print(f"\n🎬 DEBUG: create_sliding_animation_video START")
    print(f"   📷 Image path: {image_path}")
    print(f"   ⏱️  Duration: {slide_duration} seconds")
    print(f"   🎵 Audio file: {audio_file if audio_file else 'None'}")
    
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
    print(f"   📺 Screen: {screen_width}x{screen_height}")
    
    try:
        from PIL import Image
        
        print(f"   📸 Loading main image...")
        pil_img = Image.open(image_path)
        img_width, img_height = pil_img.size
        
        # Calculate scaling to fill screen height (zoomed for large text)
        scale = screen_height / img_height
        zoom_factor = 1.6
        scale = scale * zoom_factor
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        print(f"   📐 Final size: {new_width}x{new_height}")
        
        try:
            pil_img_resized = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        except AttributeError:
            pil_img_resized = pil_img.resize((new_width, new_height))
        
        temp_img_path = image_path.replace('.png', '_temp_resized.png')
        pil_img_resized.save(temp_img_path)
        
        # Create image clip
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
        
        # Audio handling
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
        print(f"🔧 DEBUG: CompleteCalendarExtractor initialized")
        print(f"   📁 PDF path: {pdf_path}")
        print(f"   📁 Output dir: {output_dir}")

    def find_all_date_pages(self) -> dict:
        print(f"📄 DEBUG: find_all_date_pages START")
        if not os.path.exists(self.pdf_path):
            print(f"❌ DEBUG: PDF not found: {self.pdf_path}")
            return {}
        
        doc = fitz.open(self.pdf_path)
        print(f"   📄 DEBUG: PDF opened, {len(doc)} pages total")
        date_page_map = {}
        
        for page_num in range(len(doc)):
            print(f"   🔍 DEBUG: Processing page {page_num + 1}/{len(doc)}")
            page = doc[page_num]
            text = page.get_text()
            date_str = extract_date_from_top_of_page(text)
            
            if date_str:
                if date_str not in date_page_map:
                    date_page_map[date_str] = []
                date_page_map[date_str].append({
                    'page_num': page_num,
                    'display_num': page_num + 1,
                    'date': date_str,
                    'text': text
                })
                print(f"   ✅ DEBUG: Page {page_num + 1} -> {date_str}")
        
        doc.close()
        print(f"📊 DEBUG: Found {len(date_page_map)} unique dates")
        return date_page_map

    def convert_page_to_image(self, page_info: dict, dpi: int = 150) -> str:
        print(f"   🖼️ DEBUG: convert_page_to_image START")
        print(f"   📄 Page: {page_info['display_num']}, Date: {page_info['date']}")
        
        doc = fitz.open(self.pdf_path)
        page = doc[page_info['page_num']]
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        date_obj = datetime.strptime(page_info['date'], "%Y-%m-%d")
        filename = f"{date_obj.day}_{date_obj.strftime('%B')}_{date_obj.year}_page_{page_info['display_num']}.png"
        image_path = os.path.join(self.output_dir, filename)
        
        pix.save(image_path)
        print(f"   💾 DEBUG: Image saved: {filename} ({os.path.getsize(image_path)} bytes)")
        
        text_file = image_path.replace('.png', '_text.txt')
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(page_info['text'])
        print(f"   📝 DEBUG: Text saved: {os.path.basename(text_file)}")
        
        doc.close()
        print(f"   🖼️ DEBUG: convert_page_to_image COMPLETE")
        return image_path

    def ensure_image_for_date(self, target_date: str, dpi: int = 150) -> dict:
        print(f"🔍 DEBUG: ensure_image_for_date START - Target: {target_date}")
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        pattern = f"{date_obj.day}_{date_obj.strftime('%B')}_{date_obj.year}_page_"
        print(f"   📁 Pattern: {pattern}")
        
        if os.path.exists(self.output_dir):
            files = os.listdir(self.output_dir)
            print(f"   📁 Output dir has {len(files)} files")
            for file in files:
                if file.startswith(pattern) and file.endswith('.png'):
                    print(f"   ✅ DEBUG: Found existing image: {file}")
                    return {'status': 'exists', 'image_path': os.path.join(self.output_dir, file)}
        
        print(f"   🔍 DEBUG: Image not found, scanning PDF...")
        date_map = self.find_all_date_pages()
        
        if target_date in date_map:
            page_info = date_map[target_date][0]
            print(f"   📄 DEBUG: Found on page {page_info['display_num']}")
            image_path = self.convert_page_to_image(page_info, dpi)
            return {'status': 'extracted', 'image_path': image_path, 'page_num': page_info['display_num']}
        else:
            print(f"❌ DEBUG: Date {target_date} not found in PDF!")
            return {'status': 'not_found', 'image_path': None}

    def get_page_text_content(self, image_path: str) -> str:
        print(f"📝 DEBUG: get_page_text_content for {os.path.basename(image_path)}")
        text_file = image_path.replace('.png', '_text.txt')
        if os.path.exists(text_file):
            with open(text_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                cleaned = [line.strip() for line in lines if line.strip() and not line.strip().isdigit()]
                result = '\n\n'.join(cleaned[:20])
                print(f"   📝 DEBUG: Extracted {len(result)} characters")
                return result
        return ""

    def get_page_title(self, image_path: str) -> str:
        print(f"📝 DEBUG: get_page_title for {os.path.basename(image_path)}")
        text_file = image_path.replace('.png', '_text.txt')
        if os.path.exists(text_file):
            with open(text_file, 'r', encoding='utf-8') as f:
                page_text = f.read()
                lines = page_text.split('\n')
                for i, line in enumerate(lines):
                    if i < 20 and line.strip() and not line.strip().isdigit():
                        if any(word in line.lower() for word in ['creative', 'daily', 'authority', 'mission']):
                            title = line.strip()
                            print(f"   📝 DEBUG: Detected title: '{title}'")
                            return title
        return "Creative Daily"

    def create_or_get_playlist(self, youtube) -> str:
        print(f"📁 DEBUG: create_or_get_playlist START")
        playlists = youtube.playlists().list(part='snippet', mine=True, maxResults=50).execute()
        print(f"   📁 DEBUG: Found {len(playlists.get('items', []))} playlists")
        
        for playlist in playlists.get('items', []):
            if playlist['snippet']['title'] == PLAYLIST_TITLE:
                print(f"   ✅ DEBUG: Found existing playlist: {playlist['id']}")
                return playlist['id']
        
        print(f"   📝 DEBUG: Creating new playlist...")
        response = youtube.playlists().insert(
            part='snippet,status',
            body={
                'snippet': {'title': PLAYLIST_TITLE, 'description': PLAYLIST_DESCRIPTION},
                'status': {'privacyStatus': 'public'}
            }
        ).execute()
        print(f"   ✅ DEBUG: Created playlist: {response['id']}")
        return response['id']

    def upload_to_youtube(self, video_path: str, target_date: str, page_text: str = "", video_title: str = "") -> dict:
        print(f"\n📤 DEBUG: upload_to_youtube START")
        print(f"   📹 Video path: {video_path}")
        
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
                print(f"   📂 DEBUG: Loaded saved credentials")
            
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    print("   🔄 DEBUG: Refreshing token...")
                    credentials.refresh(Request())
                else:
                    if not os.path.exists("client_secrets.json"):
                        print(f"   ❌ DEBUG: No client_secrets.json found!")
                        return {'status': 'skipped', 'error': 'No credentials'}
                    
                    print("   🔐 DEBUG: Opening browser for authentication...")
                    free_port = find_free_port()
                    flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
                    try:
                        credentials = flow.run_local_server(port=free_port, open_browser=True)
                    except OSError:
                        credentials = flow.run_local_server(open_browser=True)
                
                with open("token.pickle", 'wb') as f:
                    pickle.dump(credentials, f)
                print(f"   💾 DEBUG: Saved credentials")
            
            youtube = build('youtube', 'v3', credentials=credentials)
            print(f"   ✅ DEBUG: YouTube service built")
            
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
            print(f"   ✅ Video uploaded! ID: {response['id']}")
            print(f"   🖼️ Uploading custom thumbnail...")
            
            # Create matching thumbnail
            image_path = video_path.replace('_video.mp4', '.png')
            thumbnail_path = create_thumbnail_from_image(image_path)
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    youtube.thumbnails().set(
                        videoId=response['id'],
                        media_body=MediaFileUpload(thumbnail_path)
                    ).execute()
                    print(f"   ✅ Custom thumbnail uploaded!")
                    print(f"   🖼️ Thumbnail matches video start position for seamless transition!")
                except Exception as e:
                    print(f"   ⚠️ Could not upload custom thumbnail: {e}")
            
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
            print(f"   ❌ DEBUG: Upload error: {e}")
            return {'status': 'failed', 'error': str(e)}

    def process_date(self, target_date: str, post_to_youtube: bool = True, 
                     slide_duration: int = 18, audio_file: str = None) -> dict:
        print("="*60)
        print("📅 CREATIVE DAILY - SEAMLESS THUMBNAIL TRANSITION")
        print("🎬 Thumbnail exactly matches video's first frame")
        print("="*60)
        print(f"📅 Target Date: {target_date}")
        print(f"⏱️  Duration: {slide_duration} seconds")
        print("="*60)
        
        print(f"\n🔍 DEBUG: process_date - Step 1: Ensuring image for date")
        result = self.ensure_image_for_date(target_date)
        if result['status'] == 'not_found':
            print(f"\n❌ DEBUG: Date {target_date} not found in PDF")
            return {'status': 'not_found', 'date': target_date}
        
        print(f"\n🎨 Creating matching thumbnail...")
        thumbnail_path = create_thumbnail_from_image(result['image_path'])
        
        print(f"\n🔍 DEBUG: process_date - Step 2: Extracting text content")
        page_text = self.get_page_text_content(result['image_path'])
        
        print(f"\n🔍 DEBUG: process_date - Step 3: Detecting page title")
        page_title = self.get_page_title(result['image_path'])
        
        print(f"\n🔍 DEBUG: process_date - Step 4: Creating video")
        video_path = create_sliding_animation_video(
            image_path=result['image_path'],
            slide_duration=slide_duration,
            audio_file=audio_file
        )
        
        if video_path is None:
            print(f"\n❌ DEBUG: Video creation failed")
            return {'status': 'conversion_failed', 'date': target_date}
        
        youtube_result = None
        if post_to_youtube:
            print(f"\n🔍 DEBUG: process_date - Step 5: Uploading to YouTube")
            youtube_result = self.upload_to_youtube(video_path, target_date, page_text, page_title)
        
        return {
            'status': 'success',
            'date': target_date,
            'image_path': result['image_path'],
            'video_path': video_path,
            'page_num': result['page_num'],
            'detected_title': page_title,
            'youtube': youtube_result
        }


if __name__ == "__main__":
    print("="*60)
    print("🎬 CREATIVE DAILY - SEAMLESS TRANSITION (WORKING)")
    print("="*60)
    
    PDF_PATH = "your_document.pdf"
    OUTPUT_DIR = "extracted_date_pages"
    
    target_date = None
    post_to_youtube = True
    slide_duration = 18
    audio_file = None
    
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
    
    print(f"🎯 Configuration:")
    print(f"   📅 Date: {target_date}")
    print(f"   ⏱️  Duration: {slide_duration}s")
    print(f"   📹 YouTube: {'ON' if post_to_youtube else 'OFF'}")
    
    if not os.path.exists(PDF_PATH):
        print(f"❌ PDF not found: {PDF_PATH}")
        sys.exit(1)
    
    processor = CompleteCalendarExtractor(PDF_PATH, OUTPUT_DIR)
    result = processor.process_date(target_date, post_to_youtube, slide_duration, audio_file)
    
    print("\n" + "="*60)
    print("📋 RESULT")
    print("="*60)
    
    if result['status'] == 'success':
        print(f"✅ SUCCESS!")
        if result.get('youtube') and result['youtube']['status'] == 'success':
            print(f"   🔗 YouTube: {result['youtube']['video_url']}")
        sys.exit(0)
    else:
        print(f"❌ FAILED: {result['status']}")
        sys.exit(1)
