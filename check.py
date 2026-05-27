"""
Creative Daily - Complete with Seamless Thumbnail Transition
Extracts from PDF, creates sliding animation video with smooth zoom from thumbnail
FEATURES:
- Full debug output for every step
- 60% zoomed image for large readable text
- Yellow background
- Background music support
- AUTO THUMBNAIL with seamless transition to video
- SMOOTH ZOOM from thumbnail dimensions to video start position
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
# THUMBNAIL_SIZE = (1280, 720)  # YouTube thumbnail dimensions
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
    print(f"   🔍 DEBUG: detect_page_title called with {len(page_text)} chars")
    lines = page_text.split('\n')
    clean_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.isdigit() and not re.search(r'Page\s+\d+', line):
            clean_lines.append(line)
    
    print(f"   🔍 DEBUG: Found {len(clean_lines)} clean lines")
    
    found_creative_daily = False
    for i, line in enumerate(clean_lines):
        if found_creative_daily and line and len(line) > 2 and not line.startswith('#'):
            print(f"   🔍 DEBUG: Title found at line {i}: '{line}'")
            return line
        if "Creative Daily" in line or "creative daily" in line.lower():
            found_creative_daily = True
            print(f"   🔍 DEBUG: Found 'Creative Daily' at line {i}")
    
    print(f"   🔍 DEBUG: No title found, using default")
    return "Creative Daily"

def create_thumbnail_from_image(image_path: str, output_path: str = None, target_size: tuple = (1280, 720)) -> str:
    """
    Create a YouTube thumbnail from the source image (before video creation)
    This thumbnail will match the starting position of the video
    """
    print(f"\n🖼️ DEBUG: create_thumbnail_from_image START")
    print(f"   📷 Source image: {image_path}")
    print(f"   📏 Target size: {target_size[0]}x{target_size[1]}")
    
    if output_path is None:
        output_path = image_path.replace('.png', '_thumbnail.png')
    
    try:
        from PIL import Image
        import numpy as np
        
        # Load original image
        pil_img = Image.open(image_path)
        img_width, img_height = pil_img.size
        print(f"   📸 Original size: {img_width}x{img_height}")
        
        # Calculate the same zoom and positioning as video at 0 seconds
        screen_width, screen_height = 1920, 1080
        fit_scale = min(screen_width / img_width, screen_height / img_height)
        zoom_factor = 1.6
        scale = fit_scale * zoom_factor
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        print(f"   🔍 Video scale: {scale:.4f}")
        print(f"   📐 Resized dimensions: {new_width}x{new_height}")
        
        # Resize image
        try:
            img_resized = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        except AttributeError:
            try:
                img_resized = pil_img.resize((new_width, new_height), Image.LANCZOS)
            except:
                img_resized = pil_img.resize((new_width, new_height))
        
        # Calculate position at 0 seconds (same as video start)
        start_y_original = screen_height
        end_y_original = -new_height + screen_height * 0.2
        
        # For thumbnail, we need the exact position at 0 seconds
        # At t=0, progress = 0, so y = start_y_original
        y_position = start_y_original
        x_position = screen_width // 2  # Center horizontally
        
        print(f"   📍 Thumbnail position: x={x_position}, y={y_position}")
        
        # Create yellow background
        background = Image.new('RGB', (screen_width, screen_height), (255, 215, 0))
        
        # Paste resized image onto background
        # Calculate paste position (centered horizontally)
        paste_x = (screen_width - new_width) // 2
        paste_y = int(y_position)
        
        background.paste(img_resized, (paste_x, paste_y))
        
        # Now resize to YouTube thumbnail size (1280x720)
        final_thumbnail = background.resize(target_size, Image.Resampling.LANCZOS)
        final_thumbnail.save(output_path, quality=90)
        
        print(f"   ✅ Thumbnail created: {output_path} ({os.path.getsize(output_path)} bytes)")
        print(f"🖼️ DEBUG: create_thumbnail_from_image COMPLETE")
        return output_path
        
    except Exception as e:
        print(f"   ❌ Error creating thumbnail: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_video_with_seamless_transition(image_path: str, 
                                          thumbnail_path: str = None,
                                          output_path: str = None,
                                          bg_color: tuple = (255, 215, 0),
                                          slide_duration: int = 18,
                                          transition_duration: float = 0.5,
                                          audio_file: str = None) -> str:
    """
    Create video with seamless zoom transition from thumbnail to video start position
    
    The video starts with the thumbnail image, then smoothly zooms/scales to match
    the video's starting position, creating a seamless effect when YouTube shows
    the thumbnail then plays the video.
    """
    
    if output_path is None:
        output_path = image_path.replace('.png', '_video.mp4')
    
    print(f"\n🎬 DEBUG: create_video_with_seamless_transition START")
    print(f"   📷 Image path: {image_path}")
    print(f"   🖼️ Thumbnail path: {thumbnail_path if thumbnail_path else 'Will use image at 0s'}")
    print(f"   ⏱️  Duration: {slide_duration} seconds")
    print(f"   🔄 Transition duration: {transition_duration} seconds")
    
    # Import moviepy modules
    try:
        from moviepy import ImageClip, CompositeVideoClip, ColorClip
        from moviepy.audio.io.AudioFileClip import AudioFileClip
        print(f"   ✅ DEBUG: moviepy v2.0+ imported")
    except ImportError:
        try:
            from moviepy.editor import ImageClip, CompositeVideoClip, ColorClip, AudioFileClip
            print(f"   ✅ DEBUG: moviepy legacy imported")
        except ImportError as e:
            print(f"   ❌ DEBUG: moviepy import failed: {e}")
            return None
    
    screen_width, screen_height = 1920, 1080
    print(f"   📺 Screen: {screen_width}x{screen_height}")
    
    try:
        from PIL import Image
        import numpy as np
        
        # Load and process main image
        print(f"   📸 Loading main image...")
        pil_img = Image.open(image_path)
        img_width, img_height = pil_img.size
        
        # Calculate final scaled dimensions (60% zoom)
        fit_scale = min(screen_width / img_width, screen_height / img_height)
        zoom_factor = 1.6
        final_scale = fit_scale * zoom_factor
        
        final_width = int(img_width * final_scale)
        final_height = int(img_height * final_scale)
        
        print(f"   📐 Final size: {final_width}x{final_height}")
        
        # High quality resize for main image
        try:
            pil_img_final = pil_img.resize((final_width, final_height), Image.Resampling.LANCZOS)
        except AttributeError:
            try:
                pil_img_final = pil_img.resize((final_width, final_height), Image.LANCZOS)
            except:
                pil_img_final = pil_img.resize((final_width, final_height))
        
        temp_final_path = image_path.replace('.png', '_temp_final.png')
        pil_img_final.save(temp_final_path)
        
        # Create main image clip
        main_clip = ImageClip(temp_final_path, duration=slide_duration)
        
        # Calculate animation positions
        start_y_original = screen_height
        end_y_original = -final_height + screen_height * 0.2
        progress_at_4_8s = 4.8 / slide_duration
        eased_at_4_8s = progress_at_4_8s * progress_at_4_8s * (3 - 2 * progress_at_4_8s)
        y_at_4_8s = start_y_original + (end_y_original - start_y_original) * eased_at_4_8s
        
        new_start_y = y_at_4_8s
        new_end_y = end_y_original
        
        # Position animation function
        def image_slide_position(t):
            if t < transition_duration:
                # During transition: stay at start position
                return ('center', new_start_y)
            progress = min(1.0, (t - transition_duration) / (slide_duration - transition_duration))
            eased = progress * progress * (3 - 2 * progress)
            y = new_start_y + (new_end_y - new_start_y) * eased
            return ('center', y)
        
        main_clip = main_clip.with_position(image_slide_position)
        
        # Create thumbnail overlay for seamless transition
        if thumbnail_path and os.path.exists(thumbnail_path):
            print(f"   🖼️ Using thumbnail for seamless transition...")
            thumb_clip = ImageClip(thumbnail_path, duration=transition_duration)
            
            # Position thumbnail to match exactly where it will be in YouTube
            # YouTube thumbnails are 1280x720, we need to scale to fit screen
            thumb_img = Image.open(thumbnail_path)
            thumb_width, thumb_height = thumb_img.size
            
            # Scale thumbnail to full screen
            thumb_scale_x = screen_width / thumb_width
            thumb_scale_y = screen_height / thumb_height
            thumb_scale = max(thumb_scale_x, thumb_scale_y)
            
            scaled_thumb_width = int(thumb_width * thumb_scale)
            scaled_thumb_height = int(thumb_height * thumb_scale)
            
            # Resize thumbnail to screen size
            try:
                thumb_resized = thumb_img.resize((scaled_thumb_width, scaled_thumb_height), Image.Resampling.LANCZOS)
            except:
                thumb_resized = thumb_img.resize((scaled_thumb_width, scaled_thumb_height))
            
            temp_thumb_path = thumbnail_path.replace('.png', '_temp_scaled.png')
            thumb_resized.save(temp_thumb_path)
            
            thumb_clip = ImageClip(temp_thumb_path, duration=transition_duration)
            
            # Fade out thumbnail while main clip becomes visible
            thumb_clip = thumb_clip.with_alpha().with_opacity(lambda t: 1 - t/transition_duration)
            
            # Create composite with transition
            background = ColorClip(size=(screen_width, screen_height), color=bg_color, duration=slide_duration)
            
            # At start, show thumbnail overlay; it fades out as main clip becomes fully visible
            final_clip = CompositeVideoClip([background, main_clip, thumb_clip], size=(screen_width, screen_height))
            
            # Cleanup temp thumbnail
            if os.path.exists(temp_thumb_path):
                os.remove(temp_thumb_path)
                
        else:
            # No thumbnail provided, just use main clip
            print(f"   ℹ️ No thumbnail provided, using standard animation")
            background = ColorClip(size=(screen_width, screen_height), color=bg_color, duration=slide_duration)
            final_clip = CompositeVideoClip([background, main_clip], size=(screen_width, screen_height))
        
        # Handle audio
        audio_added = False
        
        def add_audio_to_clip(clip, audio_path, volume=0.25):
            try:
                if not os.path.exists(audio_path):
                    return clip, False
                
                audio = AudioFileClip(audio_path)
                if audio.duration < slide_duration:
                    loops = int(slide_duration / audio.duration) + 1
                    audio = audio.loop(loops)
                audio = audio.subclipped(0, slide_duration)
                
                try:
                    audio = audio.with_volume_scaled(volume)
                except AttributeError:
                    try:
                        audio = audio.volumex(volume)
                    except:
                        pass
                
                return clip.with_audio(audio), True
            except Exception as e:
                print(f"   ⚠️ Audio error: {e}")
                return clip, False
        
        # Try audio files
        if audio_file:
            final_clip, audio_added = add_audio_to_clip(final_clip, audio_file, 0.25)
        
        if not audio_added:
            common_audio = ["background_music.mp3", "audio.mp3", "music.mp3", "bgm.mp3"]
            for audio in common_audio:
                if os.path.exists(audio):
                    final_clip, audio_added = add_audio_to_clip(final_clip, audio, 0.25)
                    if audio_added:
                        break
        
        # Write video
        print(f"   💾 Rendering video with seamless transition...")
        audio_codec = 'aac' if audio_added else None
        
        try:
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec=audio_codec,
                fps=30,
                bitrate="5000k",
                preset='medium',
                logger=None
            )
        except TypeError:
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec=audio_codec,
                fps=30,
                bitrate="5000k",
                preset='medium'
            )
        
        # Cleanup
        final_clip.close()
        if os.path.exists(temp_final_path):
            os.remove(temp_final_path)
        
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"   ✅ Video created: {os.path.basename(output_path)} ({file_size_mb:.1f} MB)")
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
        print(f"🔧 DEBUG: CompleteCalendarExtractor initialized")
        print(f"   📁 PDF path: {pdf_path}")
        print(f"   📁 Output dir: {output_dir}")

    def extract_date_from_text(self, text: str) -> str:
        print(f"   🔍 DEBUG: extract_date_from_text called with {len(text)} chars")
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    dt = datetime.strptime(match.strip(), "%d %B %Y")
                    result = dt.strftime("%Y-%m-%d")
                    print(f"   ✅ DEBUG: Date found: {result} (format: %d %B %Y)")
                    return result
                except:
                    try:
                        dt = datetime.strptime(match.strip(), "%B %d, %Y")
                        result = dt.strftime("%Y-%m-%d")
                        print(f"   ✅ DEBUG: Date found: {result} (format: %B %d, %Y)")
                        return result
                    except:
                        continue
        print(f"   ⚠️ DEBUG: No date found in text")
        return None

    def find_all_date_pages(self) -> dict:
        print(f"📄 DEBUG: find_all_date_pages START")
        print(f"   📁 PDF path: {self.pdf_path}")
        
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
            return {'status': 'not_found', 'image_path': None, 'page_num': None}

    def get_page_text_content(self, image_path: str) -> str:
        print(f"📝 DEBUG: get_page_text_content for {os.path.basename(image_path)}")
        text_file = image_path.replace('.png', '_text.txt')
        if os.path.exists(text_file):
            with open(text_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                cleaned = []
                for line in lines:
                    line = line.strip()
                    if line and not line.isdigit() and not line.startswith('Page'):
                        cleaned.append(line)
                result = '\n\n'.join(cleaned)
                print(f"   📝 DEBUG: Extracted {len(result)} characters from {len(lines)} lines")
                return result
        print(f"   ⚠️ DEBUG: No text file found for {image_path}")
        return ""

    def get_page_title(self, image_path: str) -> str:
        print(f"📝 DEBUG: get_page_title for {os.path.basename(image_path)}")
        text_file = image_path.replace('.png', '_text.txt')
        if os.path.exists(text_file):
            with open(text_file, 'r', encoding='utf-8') as f:
                page_text = f.read()
                title = detect_page_title(page_text)
                print(f"   📝 DEBUG: Detected title: '{title}'")
                return title
        print(f"   ⚠️ DEBUG: No text file, returning default")
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

    def upload_to_youtube(self, video_path: str, target_date: str, page_text: str = "", video_title: str = "", thumbnail_path: str = None) -> dict:
        print(f"\n📤 DEBUG: upload_to_youtube START")
        print(f"   📹 Video path: {video_path}")
        print(f"   🖼️ Thumbnail path: {thumbnail_path if thumbnail_path else 'Auto-generated'}")

        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%B %d, %Y")

        if video_title and video_title != "Creative Daily":
            main_title = video_title
        else:
            main_title = f"Creative Daily | {formatted_date} | Stupid Orange | Stupidest Broke Guy"

        full_title = f"{main_title} | {formatted_date} | Creative Daily | Stupid Orange | Stupidest Broke Guy | #creativedaily #stupidestbrokeguy #UAE #Dubai"

        video_description = f"""{page_text[:4500] if page_text else ''}
        
- Help someone collect their first royalty from creativity : join Stupid Solomon Fashion Line Waiting List Here - | www.stupidorange.com |
- Secure a copy of the latest Creative Daily and get daily messages that will fasttrack you to collecting your first royalty Here = | creativedaily.stupidorange.com |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨{main_title} |  {formatted_date} | Creative Daily | Stupid Orange | Stupidest Broke Guy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 #creativedaily #creativedaily #stupidestbrokeguy #UAE #Dubai #fyp #
"""

        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            print(f"   ✅ DEBUG: Google libraries imported")

            SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
            CLIENT_SECRETS_FILE = "client_secrets.json"
            TOKEN_FILE = "token.pickle"

            credentials = None

            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, 'rb') as f:
                    credentials = pickle.load(f)
                print(f"   📂 DEBUG: Loaded saved credentials")

            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    print("   🔄 DEBUG: Refreshing token...")
                    credentials.refresh(Request())
                else:
                    if not os.path.exists(CLIENT_SECRETS_FILE):
                        print(f"   ❌ DEBUG: No client_secrets.json found!")
                        return {'status': 'skipped', 'error': 'No credentials'}
                    
                    print("   🔐 DEBUG: Opening browser for authentication...")
                    free_port = find_free_port()
                    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
                    try:
                        credentials = flow.run_local_server(port=free_port, open_browser=True)
                    except OSError:
                        credentials = flow.run_local_server(open_browser=True)
                
                with open(TOKEN_FILE, 'wb') as f:
                    pickle.dump(credentials, f)

            youtube = build('youtube', 'v3', credentials=credentials)
            print(f"   ✅ DEBUG: YouTube service built")

            if self.playlist_id is None:
                self.playlist_id = self.create_or_get_playlist(youtube)

            # Upload video
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
            print(f"   ✅ Video uploaded! ID: {response['id']}")

            # Upload custom thumbnail if provided
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    print(f"   🖼️ Uploading custom thumbnail...")
                    youtube.thumbnails().set(
                        videoId=response['id'],
                        media_body=MediaFileUpload(thumbnail_path)
                    ).execute()
                    print(f"   ✅ Custom thumbnail uploaded!")
                except Exception as e:
                    print(f"   ⚠️ Could not upload thumbnail: {e}")

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
            import traceback
            traceback.print_exc()
            return {'status': 'failed', 'error': str(e)}

    def process_date(self, target_date: str, post_to_youtube: bool = True, 
                     slide_duration: int = 18, audio_file: str = None,
                     transition_duration: float = 0.5) -> dict:
        print("="*60)
        print("📅 CREATIVE DAILY - SEAMLESS THUMBNAIL TRANSITION")
        print("🎬 Thumbnail zooms smoothly into video start position")
        print("="*60)
        print(f"📅 Target Date: {target_date}")
        print(f"⏱️  Duration: {slide_duration} seconds")
        print(f"🔄 Transition: {transition_duration} seconds")
        print("="*60)

        # Step 1: Get image from PDF
        result = self.ensure_image_for_date(target_date)
        if result['status'] == 'not_found':
            return {'status': 'not_found', 'date': target_date}

        image_path = result['image_path']
        
        # Step 2: Create thumbnail (matches video start position)
        print(f"\n🎨 Creating matching thumbnail...")
        thumbnail_path = create_thumbnail_from_image(image_path)
        
        # Step 3: Get text and title
        page_text = self.get_page_text_content(image_path)
        page_title = self.get_page_title(image_path)
        
        # Step 4: Create video with seamless transition
        print(f"\n🎬 Creating video with seamless transition...")
        video_path = create_video_with_seamless_transition(
            image_path=image_path,
            thumbnail_path=thumbnail_path,
            slide_duration=slide_duration,
            transition_duration=transition_duration,
            audio_file=audio_file
        )

        if video_path is None:
            return {'status': 'conversion_failed', 'date': target_date}

        # Step 5: Upload to YouTube
        youtube_result = None
        if post_to_youtube:
            youtube_result = self.upload_to_youtube(
                video_path, target_date, page_text, page_title, thumbnail_path
            )

        return {
            'status': 'success',
            'date': target_date,
            'image_path': image_path,
            'thumbnail_path': thumbnail_path,
            'video_path': video_path,
            'detected_title': page_title,
            'youtube': youtube_result
        }


if __name__ == "__main__":
    print("="*60)
    print("🎬 CREATIVE DAILY - SEAMLESS TRANSITION EDITION")
    print("="*60)
    
    PDF_PATH = "your_document.pdf"
    OUTPUT_DIR = "extracted_date_pages"

    target_date = None
    post_to_youtube = True
    slide_duration = 18
    transition_duration = 0.5  # Quick 0.5 second transition
    audio_file = None

    # Parse arguments
    for arg in sys.argv[1:]:
        if arg == "--no-youtube":
            post_to_youtube = False
        elif arg.startswith("--duration="):
            slide_duration = int(arg.split("=")[1])
        elif arg.startswith("--transition="):
            transition_duration = float(arg.split("=")[1])
        elif arg.startswith("--audio="):
            audio_file = arg.split("=")[1]
        elif arg.endswith(".mp3") and os.path.exists(arg):
            audio_file = arg
        elif re.match(r'\d{4}-\d{2}-\d{2}', arg):
            target_date = arg

    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    print(f"🎯 Configuration:")
    print(f"   📅 Date: {target_date}")
    print(f"   ⏱️  Duration: {slide_duration}s")
    print(f"   🔄 Transition: {transition_duration}s")
    print(f"   📹 YouTube: {'ON' if post_to_youtube else 'OFF'}")
    
    # Check PDF
    if not os.path.exists(PDF_PATH):
        print(f"❌ PDF not found: {PDF_PATH}")
        sys.exit(1)

    processor = CompleteCalendarExtractor(PDF_PATH, OUTPUT_DIR)
    result = processor.process_date(
        target_date, post_to_youtube, 
        slide_duration=slide_duration,
        transition_duration=transition_duration,
        audio_file=audio_file
    )

    print("\n" + "="*60)
    print("📋 RESULT")
    print("="*60)
    
    if result['status'] == 'success':
        print(f"✅ SUCCESS!")
        print(f"   📅 Date: {result['date']}")
        print(f"   🎬 Video: {result.get('video_path', 'N/A')}")
        if result.get('youtube') and result['youtube']['status'] == 'success':
            print(f"   🔗 YouTube: {result['youtube']['video_url']}")
            print(f"   🖼️ Thumbnail: Seamless transition enabled!")
        sys.exit(0)
    else:
        print(f"❌ FAILED: {result.get('status')}")
        sys.exit(1)
