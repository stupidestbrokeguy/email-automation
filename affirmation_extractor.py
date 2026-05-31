#!/usr/bin/env python3
"""
Creative Daily - Affirmation Focused
Extracts from PDF, creates 30-second affirmation video with sliding animation
Features:
- Extracts "Affirmation:" content from each page
- Creates 30-second clip (shorter than standard 18s)
- Yellow background with 60% zoom for readable text
- Auto thumbnail from top 25% of PNG at T=0
- YouTube upload with custom title "Affirmation of the Day"
"""

import os
import re
import sys
import pickle
import socket
from datetime import datetime
import fitz  # PyMuPDF

# ========== CONFIGURATION ==========
PLAYLIST_TITLE = "Creative Daily Affirmations | Stupid Orange"
PLAYLIST_DESCRIPTION = """Welcome to the Official Affirmation Playlist of the Creative Daily from Stupid Orange. Daily affirmations to help you start collecting royalties from your creativity and live a true royal lifestyle.

#Dubai #creativedaily #stupidestbrokeguy #UAE #affirmation #dailyaffirmation"""
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

def extract_affirmation_from_text(page_text: str) -> str:
    """
    Extract the affirmation text from a page.
    Looks for 'Affirmation:' pattern and captures everything until the next 
    section (like 'creativelydaily.stupidorange.com' or 'Related Saying')
    """
    print(f"   🔍 DEBUG: extract_affirmation_from_text called with {len(page_text)} chars")
    
    # Pattern to find Affirmation section
    # Looks for "Affirmation:" or "Affirmation" at start of line, case insensitive
    patterns = [
        r'(?:Affirmation:?\s*)([^A-Z]+?)(?=(?:creativelydaily|Related Saying|$))',
        r'(?:Affirmation:?\s*)(.+?)(?=(?:creativelydaily|Related Saying|$))',
        r'(?:Affirmation:?\s*\n)((?:.+\n)+?)(?=\n*(?:creativelydaily|Related Saying|\n\n|$))',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
        if match:
            affirmation = match.group(1).strip()
            # Clean up the affirmation text
            affirmation = re.sub(r'\s+', ' ', affirmation)  # Normalize whitespace
            affirmation = affirmation.replace('creativelydaily.stupidorange.com', '')
            affirmation = affirmation.strip()
            if len(affirmation) > 20:  # Valid affirmation should be substantial
                print(f"   ✅ DEBUG: Found affirmation ({len(affirmation)} chars): {affirmation[:80]}...")
                return affirmation
    
    # Fallback: Look for any paragraph after "Affirmation" keyword
    lines = page_text.split('\n')
    affirmation_lines = []
    capture = False
    
    for line in lines:
        line_stripped = line.strip()
        if 'affirmation' in line_stripped.lower():
            capture = True
            # If the affirmation is on the same line, extract it
            parts = re.split(r'Affirmation:?\s*', line_stripped, flags=re.IGNORECASE)
            if len(parts) > 1 and parts[1]:
                affirmation_lines.append(parts[1])
            continue
        
        if capture:
            if line_stripped and not line_stripped.startswith('http') and 'creativelydaily' not in line_stripped.lower():
                if 'Related Saying' in line_stripped or 'creativelydaily' in line_stripped.lower():
                    break
                affirmation_lines.append(line_stripped)
    
    if affirmation_lines:
        result = ' '.join(affirmation_lines).strip()
        print(f"   ✅ DEBUG: Found affirmation via fallback ({len(result)} chars)")
        return result
    
    print(f"   ⚠️ DEBUG: No affirmation found in text")
    return None

def detect_page_title(page_text: str) -> str:
    """Detect title from page structure"""
    lines = page_text.split('\n')
    clean_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.isdigit() and not re.search(r'Page\s+\d+', line):
            clean_lines.append(line)
    
    found_creative_daily = False
    for i, line in enumerate(clean_lines):
        if found_creative_daily and line and len(line) > 2 and not line.startswith('#'):
            return f"Affirmation: {line[:50]}..."
        if "Creative Daily" in line or "creative daily" in line.lower():
            found_creative_daily = True
    
    # If no title, use date-based title
    return "Daily Affirmation"

def extract_thumbnail_from_video(video_path: str, output_path: str = None, time_seconds: float = 0.0) -> str:
    """
    Extract thumbnail from video - capturing the TOP 25% of the image visible at T=0
    """
    print(f"\n🎬 DEBUG: extract_thumbnail_from_video START (Top 25% cropping mode)")
    
    if output_path is None:
        output_path = video_path.replace('.mp4', '_thumbnail.png')
    
    THUMBNAIL_WIDTH = 1280
    THUMBNAIL_HEIGHT = 720
    
    try:
        from moviepy import VideoFileClip
        from PIL import Image
        import numpy as np
        
        clip = VideoFileClip(video_path)
        frame = clip.get_frame(time_seconds)
        clip.close()
        
        img = Image.fromarray(frame.astype('uint8'), 'RGB')
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
            
            png_height = y_max - y_min
            top_visible_height = int(png_height * 0.25)
            crop_y_max = y_min + top_visible_height
            
            cropped_img = img.crop((x_min, y_min, x_max, crop_y_max))
            
            target_ratio = THUMBNAIL_WIDTH / THUMBNAIL_HEIGHT
            cropped_ratio = cropped_img.width / cropped_img.height
            
            if cropped_ratio > target_ratio:
                new_height = THUMBNAIL_HEIGHT
                new_width = int(cropped_img.width * (THUMBNAIL_HEIGHT / cropped_img.height))
                resized_img = cropped_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                left = (new_width - THUMBNAIL_WIDTH) // 2
                right = left + THUMBNAIL_WIDTH
                final_img = resized_img.crop((left, 0, right, THUMBNAIL_HEIGHT))
            else:
                new_width = THUMBNAIL_WIDTH
                new_height = int(cropped_img.height * (THUMBNAIL_WIDTH / cropped_img.width))
                resized_img = cropped_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                top = (new_height - THUMBNAIL_HEIGHT) // 2
                bottom = top + THUMBNAIL_HEIGHT
                final_img = resized_img.crop((0, top, THUMBNAIL_WIDTH, bottom))
            
            final_img.save(output_path, quality=90)
        else:
            height = img.height
            crop_height = int(height * 0.25)
            cropped_img = img.crop((0, 0, img.width, crop_height))
            final_img = cropped_img.resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)
            final_img.save(output_path, quality=90)
        
        print(f"   ✅ Thumbnail saved: {output_path}")
        
    except Exception as e:
        print(f"   ❌ Thumbnail extraction failed: {e}")
        return None
    
    return output_path

def create_affirmation_video(image_path: str, affirmation_text: str,
                              output_path: str = None,
                              bg_color: tuple = (255, 215, 0),
                              slide_duration: int = 30,
                              audio_file: str = None) -> str:
    """Create 30-second video with affirmation text overlay"""
    
    if output_path is None:
        output_path = image_path.replace('.png', '_affirmation_30s.mp4')
    
    print(f"\n🎬 DEBUG: create_affirmation_video START (30 sec)")
    print(f"   📷 Image path: {image_path}")
    print(f"   💬 Affirmation: {affirmation_text[:100]}...")
    print(f"   ⏱️  Duration: {slide_duration} seconds")
    
    try:
        from moviepy import ImageClip, CompositeVideoClip, ColorClip, TextClip
        from moviepy.audio.io.AudioFileClip import AudioFileClip
    except ImportError:
        try:
            from moviepy.editor import ImageClip, CompositeVideoClip, ColorClip, TextClip, AudioFileClip
        except ImportError as e:
            print(f"   ❌ moviepy import failed: {e}")
            return None
    
    screen_width, screen_height = 1920, 1080
    
    try:
        from PIL import Image
        import numpy as np
        
        pil_img = Image.open(image_path)
        img_width, img_height = pil_img.size
        
        # 60% ZOOM for larger text
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
        
        # Calculate animation positions (slower slide for 30 seconds)
        start_y_original = screen_height
        end_y_original = -new_height + screen_height * 0.2
        progress_at_5s = 5.0 / slide_duration
        eased_at_5s = progress_at_5s * progress_at_5s * (3 - 2 * progress_at_5s)
        y_at_5s = start_y_original + (end_y_original - start_y_original) * eased_at_5s
        
        new_start_y = y_at_5s
        new_end_y = end_y_original
        
        def image_slide_position(t):
            progress = min(1.0, t / slide_duration)
            eased = progress * progress * (3 - 2 * progress)
            y = new_start_y + (new_end_y - new_start_y) * eased
            return ('center', y)
        
        image_clip = image_clip.with_position(image_slide_position)
        
        # Create yellow background
        background = ColorClip(size=(screen_width, screen_height), color=bg_color, duration=slide_duration)
        
        # Create affirmation text overlay (bottom of screen)
        # Wrap text for better display
        wrapped_text = affirmation_text
        if len(affirmation_text) > 80:
            # Simple word wrapping
            words = affirmation_text.split()
            lines = []
            current_line = []
            current_len = 0
            for word in words:
                if current_len + len(word) + 1 <= 60:
                    current_line.append(word)
                    current_len += len(word) + 1
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_len = len(word)
            if current_line:
                lines.append(' '.join(current_line))
            wrapped_text = '\n'.join(lines)
        
        # Create text clip at bottom with semi-transparent background
        try:
            text_clip = TextClip(
                text=wrapped_text,
                font_size=48,
                color='white',
                font='Arial',
                stroke_color='black',
                stroke_width=2,
                method='caption',
                size=(screen_width - 100, None)
            ).with_position(('center', screen_height - 150)).with_duration(slide_duration)
            
            # Add semi-transparent background for text readability
            text_bg = ColorClip(size=(screen_width, 120), color=(0, 0, 0), duration=slide_duration)
            text_bg = text_bg.with_opacity(0.6).with_position(('center', screen_height - 180))
            
            final_clip = CompositeVideoClip([background, image_clip, text_bg, text_clip], 
                                            size=(screen_width, screen_height))
        except Exception as e:
            print(f"   ⚠️ Text overlay failed: {e}, creating video without text overlay")
            final_clip = CompositeVideoClip([background, image_clip], size=(screen_width, screen_height))
        
        # Handle audio
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
            # Try to find background music
            for audio in ["background_music.mp3", "audio.mp3", "music.mp3", "bgm.mp3"]:
                if os.path.exists(audio):
                    try:
                        audio_clip = AudioFileClip(audio)
                        if audio_clip.duration < slide_duration:
                            audio_clip = audio_clip.loop(int(slide_duration / audio_clip.duration) + 1)
                        audio_clip = audio_clip.subclipped(0, slide_duration)
                        final_clip = final_clip.with_audio(audio_clip)
                        audio_added = True
                        print(f"   🎵 Auto-detected audio: {audio}")
                        break
                    except:
                        continue
        
        # Write video
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac' if audio_added else None,
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
        import traceback
        traceback.print_exc()
        return None


class AffirmationExtractor:
    def __init__(self, pdf_path: str, output_dir: str = "affirmation_pages"):
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.date_patterns = [
            r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b',
        ]
        os.makedirs(output_dir, exist_ok=True)
        self.playlist_id = None
        print(f"🔧 AffirmationExtractor initialized")

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
        print(f"📄 Scanning PDF for dated pages...")
        if not os.path.exists(self.pdf_path):
            return {}

        doc = fitz.open(self.pdf_path)
        date_page_map = {}

        for page_num in range(len(doc)):
            text = doc[page_num].get_text()
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

        doc.close()
        print(f"   Found {len(date_page_map)} unique dates")
        return date_page_map

    def convert_page_to_image(self, page_info: dict, dpi: int = 150) -> str:
        doc = fitz.open(self.pdf_path)
        page = doc[page_info['page_num']]
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        date_obj = datetime.strptime(page_info['date'], "%Y-%m-%d")
        filename = f"affirmation_{date_obj.day}_{date_obj.strftime('%B')}_{date_obj.year}.png"
        image_path = os.path.join(self.output_dir, filename)

        pix.save(image_path)
        
        # Save text content
        text_file = image_path.replace('.png', '_text.txt')
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(page_info['text'])

        doc.close()
        return image_path

    def get_affirmation_from_page(self, image_path: str) -> str:
        text_file = image_path.replace('.png', '_text.txt')
        if os.path.exists(text_file):
            with open(text_file, 'r', encoding='utf-8') as f:
                page_text = f.read()
                return extract_affirmation_from_text(page_text)
        return None

    def ensure_image_for_date(self, target_date: str, dpi: int = 150) -> dict:
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        pattern = f"affirmation_{date_obj.day}_{date_obj.strftime('%B')}_{date_obj.year}"

        if os.path.exists(self.output_dir):
            for file in os.listdir(self.output_dir):
                if file.startswith(pattern) and file.endswith('.png'):
                    return {'status': 'exists', 'image_path': os.path.join(self.output_dir, file)}

        date_map = self.find_all_date_pages()
        
        if target_date in date_map:
            page_info = date_map[target_date][0]
            image_path = self.convert_page_to_image(page_info, dpi)
            return {'status': 'extracted', 'image_path': image_path, 'page_num': page_info['display_num']}
        else:
            return {'status': 'not_found', 'image_path': None}

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

    def upload_to_youtube(self, video_path: str, target_date: str, affirmation_text: str) -> dict:
        print(f"\n📤 Uploading to YouTube...")
        
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%B %d, %Y")

        full_title = f"✨ Affirmation of the Day | {formatted_date} | Creative Daily | Stupid Orange ✨"
        
        # Clean affirmation for description
        clean_affirmation = affirmation_text.replace('\n', ' ').strip()
        
        video_description = f"""🌟 DAILY AFFIRMATION - {formatted_date} 🌟

"{clean_affirmation}"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ Join the Creative Daily community and start collecting royalties from your creativity!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 Help someone collect their first royalty: www.stupidorange.com
📘 Get the Creative Daily: creativedaily.stupidorange.com

Follow Us:
• YouTube: @stupidestbrokeguy
• TikTok: @stupidestbrokeguy

#affirmation #dailyaffirmation #creativedaily #stupidestbrokeguy #UAE #Dubai #morningaffirmation #positivevibes
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

            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                else:
                    if not os.path.exists(CLIENT_SECRETS_FILE):
                        return {'status': 'failed', 'error': 'No credentials'}
                    
                    free_port = find_free_port()
                    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
                    credentials = flow.run_local_server(port=free_port, open_browser=True)
                
                with open(TOKEN_FILE, 'wb') as f:
                    pickle.dump(credentials, f)

            youtube = build('youtube', 'v3', credentials=credentials)

            if self.playlist_id is None:
                self.playlist_id = self.create_or_get_playlist(youtube)

            # Extract thumbnail
            thumbnail_path = extract_thumbnail_from_video(video_path, time_seconds=0.0)
            
            body = {
                'snippet': {
                    'title': full_title[:100],
                    'description': video_description[:5000],
                    'tags': ['affirmation', 'dailyaffirmation', 'creativedaily', 'stupidestbrokeguy', 'UAE', 'Dubai'],
                    'categoryId': '22'
                },
                'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
            }

            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
            response = request.execute()
            video_url = f"https://youtu.be/{response['id']}"

            # Upload thumbnail
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    youtube.thumbnails().set(
                        videoId=response['id'],
                        media_body=MediaFileUpload(thumbnail_path)
                    ).execute()
                    os.remove(thumbnail_path)
                except Exception as e:
                    print(f"   ⚠️ Thumbnail upload failed: {e}")

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

            return {'status': 'success', 'video_url': video_url}

        except Exception as e:
            return {'status': 'failed', 'error': str(e)}

    def process_date(self, target_date: str, post_to_youtube: bool = True,
                     audio_file: str = None) -> dict:
        print("="*60)
        print("✨ CREATIVE DAILY - AFFIRMATION EXTRACTOR (30 sec)")
        print("="*60)
        print(f"📅 Target Date: {target_date}")
        print("="*60)

        # Get image
        result = self.ensure_image_for_date(target_date)
        if result['status'] == 'not_found':
            return {'status': 'not_found', 'date': target_date}

        # Extract affirmation
        affirmation = self.get_affirmation_from_page(result['image_path'])
        if not affirmation:
            return {'status': 'no_affirmation', 'date': target_date}

        print(f"\n✅ Affirmation found: {affirmation[:100]}...")

        # Create 30-second video
        video_path = create_affirmation_video(
            image_path=result['image_path'],
            affirmation_text=affirmation,
            slide_duration=30,
            audio_file=audio_file
        )

        if video_path is None:
            return {'status': 'conversion_failed', 'date': target_date}

        youtube_result = None
        if post_to_youtube:
            youtube_result = self.upload_to_youtube(video_path, target_date, affirmation)

        return {
            'status': 'success',
            'date': target_date,
            'affirmation': affirmation,
            'video_path': video_path,
            'youtube': youtube_result
        }


if __name__ == "__main__":
    print("="*60)
    print("✨ AFFIRMATION EXTRACTOR - 30 SECOND CLIPS")
    print("="*60)

    PDF_PATH = "your_document.pdf"
    OUTPUT_DIR = "affirmation_pages"

    target_date = None
    post_to_youtube = True
    audio_file = None

    # Parse arguments
    for arg in sys.argv[1:]:
        if arg == "--no-youtube":
            post_to_youtube = False
        elif arg.startswith("--audio="):
            audio_file = arg.split("=")[1]
        elif re.match(r'\d{4}-\d{2}-\d{2}', arg):
            target_date = arg

    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    print(f"📅 Target Date: {target_date}")
    print(f"📹 YouTube Upload: {'ON' if post_to_youtube else 'OFF'}")

    if not os.path.exists(PDF_PATH):
        print(f"❌ PDF not found: {PDF_PATH}")
        sys.exit(1)

    processor = AffirmationExtractor(PDF_PATH, OUTPUT_DIR)
    result = processor.process_date(target_date, post_to_youtube, audio_file)

    print("\n" + "="*60)
    print("📋 FINAL RESULT")
    print("="*60)

    if result['status'] == 'success':
        print(f"✅ SUCCESS!")
        print(f"   📅 Date: {result['date']}")
        print(f"   💬 Affirmation: {result['affirmation'][:150]}...")
        print(f"   🎬 Video: {result.get('video_path', 'N/A')}")
        
        if result.get('youtube') and result['youtube']['status'] == 'success':
            print(f"\n📹 POSTED TO YOUTUBE!")
            print(f"   🔗 URL: {result['youtube']['video_url']}")
        
        sys.exit(0)
    else:
        print(f"❌ FAILED: {result.get('status')}")
        sys.exit(1)
