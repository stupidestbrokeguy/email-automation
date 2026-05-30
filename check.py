"""
Creative Daily - Extract from PDF, create video, upload to YouTube
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
PLAYLIST_DESCRIPTION = """Welcome to the Official Playlist of the Creative Daily from Stupid Orange.

#Dubai #creativedaily #stupidestbrokeguy #UAE"""
CREATIVE_DAILY_START_DATE = datetime(2026, 6, 1)
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

def extract_thumbnail_from_video(video_path: str, output_path: str = None) -> str:
    if output_path is None:
        output_path = video_path.replace('.mp4', '_thumbnail.png')
    try:
        from moviepy import VideoFileClip
        clip = VideoFileClip(video_path)
        frame = clip.get_frame(0.0)
        clip.close()
        from PIL import Image
        img = Image.fromarray(frame.astype('uint8'), 'RGB')
        img.save(output_path, quality=90)
        return output_path
    except Exception as e:
        print(f"   ⚠️ Thumbnail error: {e}")
        return None

def create_sliding_animation_video(image_path: str, output_path: str = None,
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
    bg_color = (255, 215, 0)
    
    from PIL import Image
    pil_img = Image.open(image_path)
    img_width, img_height = pil_img.size
    
    fit_scale = min(screen_width / img_width, screen_height / img_height)
    scale = fit_scale * 1.6
    new_width = int(img_width * scale)
    new_height = int(img_height * scale)
    pil_img_resized = pil_img.resize((new_width, new_height))
    
    temp_img_path = image_path.replace('.png', '_temp.png')
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
    
    if audio_file and os.path.exists(audio_file):
        try:
            audio = AudioFileClip(audio_file)
            if audio.duration < slide_duration:
                audio = audio.loop(int(slide_duration / audio.duration) + 1)
            audio = audio.subclipped(0, slide_duration)
            final_clip = final_clip.with_audio(audio)
        except Exception as e:
            print(f"   ⚠️ Audio error: {e}")
    
    final_clip.write_videofile(output_path, codec='libx264', fps=30, bitrate="5000k")
    final_clip.close()
    if os.path.exists(temp_img_path):
        os.remove(temp_img_path)
    
    return output_path


class CompleteCalendarExtractor:
    def __init__(self, pdf_path: str, output_dir: str = "extracted_date_pages"):
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.playlist_id = None
        self.page_date_map = {}

    def build_page_date_map(self):
        doc = fitz.open(self.pdf_path)
        total_pages = len(doc)
        print(f"📄 PDF has {total_pages} pages")
        
        for page_num in range(total_pages):
            page_date = CREATIVE_DAILY_START_DATE + timedelta(days=page_num)
            date_str = page_date.strftime("%Y-%m-%d")
            self.page_date_map[date_str] = {
                'page_num': page_num,
                'display_num': page_num + 1,
                'date': date_str,
                'text': doc[page_num].get_text()
            }
            print(f"   Page {page_num + 1} -> {date_str}")
        doc.close()
        return True

    def ensure_image_for_date(self, target_date: str, dpi: int = 150) -> dict:
        if not self.page_date_map:
            self.build_page_date_map()
        
        if target_date not in self.page_date_map:
            return {'status': 'not_found', 'image_path': None}
        
        page_info = self.page_date_map[target_date]
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        pattern = f"{date_obj.day}_{date_obj.strftime('%B')}_{date_obj.year}_page_"
        
        for file in os.listdir(self.output_dir):
            if file.startswith(pattern) and file.endswith('.png'):
                return {'status': 'exists', 'image_path': os.path.join(self.output_dir, file)}
        
        # Convert page to image
        doc = fitz.open(self.pdf_path)
        page = doc[page_info['page_num']]
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        filename = f"{date_obj.day}_{date_obj.strftime('%B')}_{date_obj.year}_page_{page_info['display_num']}.png"
        image_path = os.path.join(self.output_dir, filename)
        pix.save(image_path)
        
        doc.close()
        return {'status': 'extracted', 'image_path': image_path, 'page_num': page_info['display_num']}

    def get_page_text_content(self, image_path: str) -> str:
        text_file = image_path.replace('.png', '_text.txt')
        if os.path.exists(text_file):
            with open(text_file, 'r') as f:
                return f.read()[:2000]
        return ""

    def upload_to_youtube(self, video_path: str, target_date: str, page_text: str = "") -> dict:
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

            date_obj = datetime.strptime(target_date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%B %d, %Y")
            title = f"Creative Daily | {formatted_date} | Stupid Orange | Stupidest Broke Guy"
            full_title = f"{title} | #creativedaily #stupidestbrokeguy #UAE #Dubai"
            
            description = f"""{page_text[:1000]}

📅 Creative Daily - {formatted_date}

Subscribe for daily creativity training!
#creativedaily #stupidestbrokeguy #UAE #Dubai
"""

            body = {
                'snippet': {
                    'title': full_title[:100],
                    'description': description[:5000],
                    'tags': ['creativedaily', 'stupidestbrokeguy', 'Dubai', 'UAE'],
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
            thumb_path = extract_thumbnail_from_video(video_path)
            if thumb_path and os.path.exists(thumb_path):
                try:
                    youtube.thumbnails().set(
                        videoId=response['id'],
                        media_body=MediaFileUpload(thumb_path)
                    ).execute()
                    os.remove(thumb_path)
                except Exception as e:
                    print(f"   ⚠️ Thumbnail error: {e}")

            return {'status': 'success', 'video_url': video_url}

        except Exception as e:
            print(f"   ❌ Upload error: {e}")
            return {'status': 'failed', 'error': str(e)}

    def process_date(self, target_date: str, post_to_youtube: bool = True, 
                     slide_duration: int = 18, audio_file: str = None) -> dict:
        print("="*60)
        print(f"📅 Creative Daily - {target_date}")
        print(f"⏱️ Duration: {slide_duration}s")
        print("="*60)

        result = self.ensure_image_for_date(target_date)
        if result['status'] == 'not_found':
            return {'status': 'not_found', 'date': target_date}

        page_text = self.get_page_text_content(result['image_path'])
        video_path = create_sliding_animation_video(
            image_path=result['image_path'],
            slide_duration=slide_duration,
            audio_file=audio_file
        )

        if video_path is None:
            return {'status': 'conversion_failed'}

        youtube_result = None
        if post_to_youtube:
            youtube_result = self.upload_to_youtube(video_path, target_date, page_text)

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
    slide_duration = random.randint(17, 21)
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

    print(f"🎯 Target: {target_date}, Duration: {slide_duration}s")

    if not os.path.exists(PDF_PATH):
        print(f"❌ PDF not found: {PDF_PATH}")
        sys.exit(1)

    processor = CompleteCalendarExtractor(PDF_PATH, OUTPUT_DIR)
    result = processor.process_date(target_date, post_to_youtube, slide_duration, audio_file)

    if result['status'] == 'success':
        print(f"\n✅ SUCCESS!")
        if result.get('youtube') and result['youtube']['status'] == 'success':
            print(f"📹 YouTube: {result['youtube']['video_url']}")
        sys.exit(0)
    else:
        print(f"\n❌ FAILED: {result['status']}")
        sys.exit(1)
