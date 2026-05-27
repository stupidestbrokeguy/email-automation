"""
Creative Daily - Complete Working Script
Extracts from PDF, creates sliding animation video, uploads to YouTube
Image starts at 4.8-second position (already visible) + 30% zoom + Yellow background
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
    
    found_creative_daily = False
    for line in clean_lines:
        if found_creative_daily and line and len(line) > 2 and not line.startswith('#'):
            return line
        if "Creative Daily" in line or "creative daily" in line.lower():
            found_creative_daily = True
    return "Creative Daily"

def create_sliding_animation_video(image_path: str, text_content: str,
                                    output_path: str = None,
                                    bg_color: tuple = (255, 215, 0),
                                    text_color: str = "white",
                                    slide_duration: int = 18) -> str:
    """
    Create video with image sliding up and text scrolling
    Image starts at position where it would be at 4.8 seconds in original
    30% more zoom - Yellow background
    """
    
    if output_path is None:
        output_path = image_path.replace('.png', '_video.mp4')
    
    print(f"\n🎬 Creating sliding animation video...")
    print(f"   Image: {os.path.basename(image_path)}")
    print(f"   Duration: {slide_duration} seconds")
    
    try:
        from moviepy import ImageClip, CompositeVideoClip, ColorClip, TextClip
        print(f"   Using moviepy v2.0+")
    except ImportError:
        try:
            from moviepy.editor import ImageClip, CompositeVideoClip, ColorClip, TextClip
            print(f"   Using moviepy (legacy)")
        except ImportError as e:
            print(f"   ❌ moviepy import failed: {e}")
            return None
    
    screen_width, screen_height = 1920, 1080
    
    try:
        from PIL import Image
        
        pil_img = Image.open(image_path)
        img_width, img_height = pil_img.size
        
        # Calculate zoom (30% more than fit-to-screen)
        fit_scale = min(screen_width / img_width, screen_height / img_height)
        zoom_factor = 1.3
        scale = fit_scale * zoom_factor
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        print(f"   Original: {img_width}x{img_height}")
        print(f"   Fit scale: {fit_scale:.2f}, Zoom factor: {zoom_factor}")
        print(f"   Resized to: {new_width}x{new_height}")
        
        # Resize image
        try:
            pil_img_resized = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        except AttributeError:
            try:
                pil_img_resized = pil_img.resize((new_width, new_height), Image.LANCZOS)
            except:
                pil_img_resized = pil_img.resize((new_width, new_height))
        
        temp_img_path = image_path.replace('.png', '_temp_resized.png')
        pil_img_resized.save(temp_img_path)
        
        image_clip = ImageClip(temp_img_path, duration=slide_duration)
        
        # =========================================================
        # Image starts at the position it would be at 4.8 seconds
        # =========================================================
        
        # Original animation parameters
        start_y_original = screen_height
        end_y_original = -new_height + screen_height * 0.2
        progress_at_4_8s = 4.8 / slide_duration  # 0.2667
        # Easing function: eased = progress * progress * (3 - 2 * progress)
        eased_at_4_8s = progress_at_4_8s * progress_at_4_8s * (3 - 2 * progress_at_4_8s)
        y_at_4_8s = start_y_original + (end_y_original - start_y_original) * eased_at_4_8s
        
        print(f"   Original animation would be at Y = {y_at_4_8s:.1f} at 4.8 seconds")
        
        # NEW animation: Start at that Y position
        new_start_y = y_at_4_8s
        new_end_y = end_y_original
        
        print(f"   NEW animation: start Y = {new_start_y:.1f}, end Y = {new_end_y:.1f}")
        
        def image_slide_position(t):
            progress = min(1.0, t / slide_duration)
            eased = progress * progress * (3 - 2 * progress)
            y = new_start_y + (new_end_y - new_start_y) * eased
            return ('center', y)
        
        image_clip = image_clip.with_position(image_slide_position)
        
        # Yellow background
        background = ColorClip(size=(screen_width, screen_height),
                                color=bg_color,
                                duration=slide_duration)
        
        # Process text for scrolling
        lines = text_content.split('\n')
        clean_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.isdigit() and len(line) > 1 and not line.startswith('Page'):
                if len(line) > 85:
                    words = line.split()
                    current_line = ""
                    for word in words:
                        if len(current_line) + len(word) + 1 <= 85:
                            current_line += (" " + word if current_line else word)
                        else:
                            if current_line:
                                clean_lines.append(current_line)
                            current_line = word
                    if current_line:
                        clean_lines.append(current_line)
                else:
                    clean_lines.append(line)
        
        if not clean_lines:
            clean_lines = ["Creative Daily", datetime.now().strftime("%B %d, %Y")]
        
        print(f"   📝 Creating {len(clean_lines)} text lines...")
        full_text = '\n'.join(clean_lines)
        
        # Create text clip with larger font and stroke
        text_clip = None
        font_size = 52
        font_options = ["DejaVu-Sans-Bold", "DejaVu-Sans", "Liberation-Sans", "FreeSans", None]
        
        for font in font_options:
            try:
                if font:
                    text_clip = TextClip(
                        text=full_text,
                        color=text_color,
                        font=font,
                        fontsize=font_size,
                        stroke_width=2,
                        stroke_color='black'
                    )
                else:
                    text_clip = TextClip(
                        text=full_text,
                        color=text_color,
                        fontsize=font_size,
                        stroke_width=2,
                        stroke_color='black'
                    )
                break
            except:
                continue
        
        if text_clip is None:
            print(f"   ⚠️ Could not create text clip - continuing without text")
            final_clip = CompositeVideoClip([background, image_clip], size=(screen_width, screen_height))
            final_clip.write_videofile(output_path, codec='libx264', fps=30, bitrate="5000k", logger=None)
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
            return output_path
        
        text_clip = text_clip.with_duration(slide_duration)
        
        text_height = text_clip.size[1]
        text_start_y = screen_height
        text_end_y = -text_height - 50
        
        def text_scroll_position(t):
            progress = min(1.0, t / slide_duration)
            eased = progress * progress * (3 - 2 * progress)
            y = text_start_y + (text_end_y - text_start_y) * eased
            return ('center', y)
        
        text_clip = text_clip.with_position(text_scroll_position)
        
        # Composite all layers
        final_clip = CompositeVideoClip([background, image_clip, text_clip],
                                         size=(screen_width, screen_height))
        
        # Write video with high quality
        print(f"   💾 Writing video...")
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            fps=30,
            bitrate="5000k",
            preset='medium',
            logger=None
        )
        
        # Cleanup
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
        self.date_patterns = [
            r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b',
        ]
        os.makedirs(output_dir, exist_ok=True)
        self.playlist_id = None

    def extract_date_from_text(self, text: str) -> str:
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    dt = datetime.strptime(match.strip(), "%d %B %Y")
                    return dt.strftime("%Y-%m-%d")
                except:
                    try:
                        dt = datetime.strptime(match.strip(), "%B %d, %Y")
                        return dt.strftime("%Y-%m-%d")
                    except:
                        continue
        return None

    def find_all_date_pages(self) -> dict:
        print(f"📄 Scanning PDF: {self.pdf_path}")
        if not os.path.exists(self.pdf_path):
            print(f"❌ PDF not found: {self.pdf_path}")
            return {}

        doc = fitz.open(self.pdf_path)
        date_page_map = {}

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            date_str = self.extract_date_from_text(text)

            if date_str:
                if date_str not in date_page_map:
                    date_page_map[date_str] = []
                date_page_map[date_str].append({
                    'page_num': page_num,
                    'display_num': page_num + 1,
                    'date': date_str,
                    'text': text
                })
                print(f"   ✓ Page {page_num + 1} -> {date_str}")

        doc.close()
        print(f"\n📊 Found {len(date_page_map)} unique dates")
        return date_page_map

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
        print(f"   🖼️ Saved: {filename}")
        return image_path

    def ensure_image_for_date(self, target_date: str, dpi: int = 150) -> dict:
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        pattern = f"{date_obj.day}_{date_obj.strftime('%B')}_{date_obj.year}_page_"

        if os.path.exists(self.output_dir):
            for file in os.listdir(self.output_dir):
                if file.startswith(pattern) and file.endswith('.png'):
                    return {'status': 'exists', 'image_path': os.path.join(self.output_dir, file)}

        date_map = self.find_all_date_pages()
        if target_date in date_map:
            page_info = date_map[target_date][0]
            image_path = self.convert_page_to_image(page_info, dpi)
            return {'status': 'extracted', 'image_path': image_path, 'page_num': page_info['display_num']}

        return {'status': 'not_found'}

    def get_page_text_content(self, image_path: str) -> str:
        text_file = image_path.replace('.png', '_text.txt')
        if os.path.exists(text_file):
            with open(text_file, 'r', encoding='utf-8') as f:
                lines = f.read().split('\n')
                cleaned = []
                for line in lines:
                    line = line.strip()
                    if line and not line.isdigit() and not line.startswith('Page'):
                        cleaned.append(line)
                return '\n\n'.join(cleaned)
        return ""

    def get_page_title(self, image_path: str) -> str:
        text_file = image_path.replace('.png', '_text.txt')
        if os.path.exists(text_file):
            with open(text_file, 'r', encoding='utf-8') as f:
                return detect_page_title(f.read())
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
            main_title = f"Creative Daily | {formatted_date}"

        full_title = f"{main_title} | #Dubai #creativedaily #stupidestbrokeguy #UAE"

        video_description = f"""{page_text[:4500] if page_text else ''}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ Creative Daily | {formatted_date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#Dubai #creativedaily #stupidestbrokeguy #UAE
"""

        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload

            SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
            CLIENT_SECRETS_FILE = "client_secrets.json"
            TOKEN_FILE = "token.pickle"

            credentials = None

            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, 'rb') as f:
                    credentials = pickle.load(f)
                print("   📂 Loaded saved credentials")

            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    print("   🔄 Refreshing token...")
                    credentials.refresh(Request())
                else:
                    if not os.path.exists(CLIENT_SECRETS_FILE):
                        return {'status': 'skipped', 'error': 'No credentials'}
                    print("   🔐 Opening browser for auth...")
                    free_port = find_free_port()
                    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
                    try:
                        credentials = flow.run_local_server(port=free_port, open_browser=True)
                    except OSError:
                        credentials = flow.run_local_server(open_browser=True)
                with open(TOKEN_FILE, 'wb') as f:
                    pickle.dump(credentials, f)
                print("   💾 Saved credentials")

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
            print(f"   ⬆️ Uploading video...")
            request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
            response = request.execute()
            video_url = f"https://youtu.be/{response['id']}"
            print(f"   ✅ Uploaded: {video_url}")

            youtube.playlistItems().insert(
                part='snippet',
                body={
                    'snippet': {
                        'playlistId': self.playlist_id,
                        'resourceId': {'kind': 'youtube#video', 'videoId': response['id']}
                    }
                }
            ).execute()
            print(f"   ✅ Added to playlist: {PLAYLIST_TITLE}")

            return {'status': 'success', 'video_url': video_url}

        except Exception as e:
            print(f"   ❌ Upload error: {e}")
            return {'status': 'failed', 'error': str(e)}

    def process_date(self, target_date: str, post_to_youtube: bool = True, slide_duration: int = 18) -> dict:
        print("="*60)
        print("📅 CREATIVE DAILY - SLIDING ANIMATION VIDEO")
        print("🎬 Image starts visible (4.8s position) | 30% zoom | Yellow background")
        print("="*60)
        print(f"Target Date: {target_date}")

        result = self.ensure_image_for_date(target_date)
        if result['status'] == 'not_found':
            print(f"\n❌ Date {target_date} not found")
            return {'status': 'not_found', 'date': target_date}

        print(f"\n✅ Image ready: {os.path.basename(result['image_path'])}")

        page_text = self.get_page_text_content(result['image_path'])
        page_title = self.get_page_title(result['image_path'])
        print(f"   📝 Detected title: '{page_title}'")
        print(f"   📝 Text length: {len(page_text)} chars")

        video_path = create_sliding_animation_video(
            image_path=result['image_path'],
            text_content=page_text,
            slide_duration=slide_duration
        )

        if video_path is None:
            return {'status': 'conversion_failed', 'date': target_date}

        youtube_result = None
        if post_to_youtube:
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
    PDF_PATH = "your_document.pdf"
    OUTPUT_DIR = "extracted_date_pages"

    target_date = None
    post_to_youtube = True
    slide_duration = 18

    for arg in sys.argv[1:]:
        if arg == "--no-youtube":
            post_to_youtube = False
        elif arg.startswith("--duration="):
            slide_duration = int(arg.split("=")[1])
        elif re.match(r'\d{4}-\d{2}-\d{2}', arg):
            target_date = arg

    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    print(f"\n🎯 Processing: {target_date}")
    print(f"📹 YouTube: {'ON' if post_to_youtube else 'OFF'}")
    print(f"⏱️  Duration: {slide_duration}s")
    print(f"📁 Playlist: {PLAYLIST_TITLE}\n")

    if not os.path.exists(PDF_PATH):
        print(f"❌ PDF not found: {PDF_PATH}")
        sys.exit(1)

    processor = CompleteCalendarExtractor(PDF_PATH, OUTPUT_DIR)
    result = processor.process_date(target_date, post_to_youtube, slide_duration=slide_duration)

    print("\n" + "="*60)
    print("📋 FINAL RESULT")
    print("="*60)

    if result['status'] == 'success':
        print(f"✅ SUCCESS!")
        print(f"   Date: {result['date']}")
        print(f"   Title: {result.get('detected_title', 'N/A')}")
        print(f"   Video: {result.get('video_path', 'N/A')}")

        if result.get('youtube') and result['youtube']['status'] == 'success':
            print(f"\n📹 POSTED TO YOUTUBE!")
            print(f"   URL: {result['youtube']['video_url']}")
            print(f"   Playlist: {PLAYLIST_TITLE}")

        sys.exit(0)
    else:
        print(f"❌ FAILED: {result.get('status')}")
        sys.exit(1)
