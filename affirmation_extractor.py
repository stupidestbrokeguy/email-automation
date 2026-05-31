#!/usr/bin/env python3
"""
Creative Daily - Affirmation with Canva Template
Uses a pre-designed Canva template as background and overlays text
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
PLAYLIST_DESCRIPTION = """Daily affirmations from Creative Daily to help you start collecting royalties from your creativity."""

# Template file name (your Canva design)
TEMPLATE_PATH = "affirmation_template.png"  # Change this to your template filename

def find_free_port(start_port=8080, end_port=8090):
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
    Extract ONLY the affirmation text from a page.
    Stops at 'Related Saying', 'creativelydaily', or any other section.
    """
    print(f"   🔍 Looking for affirmation in {len(page_text)} chars...")
    
    patterns = [
        r'(?:Affirmation:?\s*)([^A-Z]+?)(?=\n\s*(?:Related Saying|creativelydaily|-\s*[A-Z]|$))',
        r'(?:Affirmation:?\s*)(.+?)(?=\n\s*(?:Related Saying|creativelydaily|-\s*[A-Z]|$))',
        r'(?:Affirmation:?\s*\n)((?:[^\n]+\n)+?)(?=\n*(?:Related Saying|creativelydaily|\n\n))',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
        if match:
            affirmation = match.group(1).strip()
            affirmation = re.sub(r'\s+', ' ', affirmation)
            affirmation = affirmation.replace('creativelydaily.stupidorange.com', '')
            affirmation = affirmation.replace('Related Saying', '')
            affirmation = affirmation.strip('"\'')
            affirmation = affirmation.strip()
            
            if len(affirmation) > 20:
                print(f"   ✅ Found affirmation ({len(affirmation)} chars)")
                return affirmation
    
    # Line-by-line extraction
    lines = page_text.split('\n')
    affirmation_lines = []
    capture = False
    
    for line in lines:
        line_stripped = line.strip()
        
        if 'affirmation' in line_stripped.lower():
            capture = True
            parts = re.split(r'Affirmation:?\s*', line_stripped, flags=re.IGNORECASE)
            if len(parts) > 1 and parts[1]:
                clean_part = parts[1].split('Related Saying')[0].split('creativelydaily')[0].strip()
                if clean_part:
                    affirmation_lines.append(clean_part)
            continue
        
        if capture:
            if ('Related Saying' in line_stripped or 
                'creativelydaily' in line_stripped.lower() or
                line_stripped.startswith('-') or
                (line_stripped == '' and len(affirmation_lines) > 0)):
                break
            
            if line_stripped:
                clean_line = line_stripped.split('Related Saying')[0].split('creativelydaily')[0].strip()
                if clean_line:
                    affirmation_lines.append(clean_line)
    
    if affirmation_lines:
        result = ' '.join(affirmation_lines).strip()
        result = result.split('Related Saying')[0].split('creativelydaily')[0].strip()
        result = result.strip('"\'')
        print(f"   ✅ Found affirmation via line-by-line ({len(result)} chars)")
        return result
    
    # Fallback: sentence boundary
    affirmation_match = re.search(r'Affirmation:?\s*([^.!?]+[.!?])', page_text, re.IGNORECASE)
    if affirmation_match:
        affirmation = affirmation_match.group(1).strip()
        print(f"   ✅ Found affirmation via sentence boundary ({len(affirmation)} chars)")
        return affirmation
    
    print(f"   ⚠️ No affirmation found in text")
    return None

def create_affirmation_image_from_template(affirmation_text: str, target_date: str, output_path: str = None, template_path: str = TEMPLATE_PATH) -> str:
    """
    Uses a Canva template as background and overlays the affirmation text and date.
    This way your logo, design, and branding are already in the template.
    """
    
    if output_path is None:
        output_path = f"affirmation_{target_date}.png"
    
    print(f"\n🎨 Creating affirmation image from Canva template...")
    print(f"   📅 Date: {target_date}")
    print(f"   📁 Template path: {template_path}")
    print(f"   💬 Text: {affirmation_text[:80]}...")
    
    # Check if template exists
    if not os.path.exists(template_path):
        print(f"   ❌ Template not found: {template_path}")
        print(f"   📁 Looking for: {os.path.abspath(template_path)}")
        print(f"   📁 Files in directory: {os.listdir('.')}")
        return None
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        import textwrap
        
        # Load the Canva template
        print(f"   🖼️ Loading template...")
        img = Image.open(template_path)
        draw = ImageDraw.Draw(img)
        
        print(f"   📐 Template size: {img.width}x{img.height}")
        
        # Load fonts (adjust these paths to match your template's design)
        try:
            # Try to use a nice font that matches your Canva design
            font_affirmation = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 52)
            font_date = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 40)
            print(f"   ✅ Loaded Liberation fonts")
        except:
            try:
                font_affirmation = ImageFont.truetype("/System/Library/Fonts/Helvetica-Bold.ttf", 52)
                font_date = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
                print(f"   ✅ Loaded Helvetica fonts")
            except:
                font_affirmation = ImageFont.load_default()
                font_date = ImageFont.load_default()
                print(f"   ⚠️ Using default fonts")
        
        # Format date
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%B %d, %Y")
        
        # Define text area on your template (YOU NEED TO ADJUST THESE COORDINATES)
        # These are the pixel coordinates where text should be placed
        # You can find these by opening your template in an image editor
        
        # =====================================================
        # TODO: ADJUST THESE COORDINATES TO MATCH YOUR TEMPLATE
        # =====================================================
        
        # Area for affirmation text (x, y, width, max_height)
        # For 1920x1080 template, typical text area in the center
        text_x = 200           # Left margin for text (pixels)
        text_y = 450           # Top Y position for text (pixels)
        text_width = img.width - 400  # Width available for text (with margins)
        max_text_height = 400  # Maximum height text can take before overflowing
        
        # Date position (adjust based on your template)
        date_x = img.width // 2  # Center horizontally
        date_y = 200             # Y position for date (pixels)
        
        print(f"   📍 Text area: x={text_x}, y={text_y}, width={text_width}")
        print(f"   📍 Date position: x={date_x}, y={date_y}")
        
        # Wrap text to fit within the defined width
        # Calculate how many characters fit per line based on font size
        # For font size 52, ~30-40 characters per line on 1920px width
        chars_per_line = 45
        wrapped_text = textwrap.wrap(affirmation_text, width=chars_per_line)
        print(f"   📝 Wrapped affirmation into {len(wrapped_text)} lines")
        
        # Draw date on template
        # Get date text size for centering
        date_bbox = draw.textbbox((0, 0), formatted_date, font=font_date)
        date_width = date_bbox[2] - date_bbox[0]
        date_x_centered = (img.width - date_width) // 2
        
        # Draw date with shadow for better visibility
        shadow_offset = 2
        draw.text((date_x_centered + shadow_offset, date_y + shadow_offset), formatted_date, fill=(0, 0, 0, 100), font=font_date)
        draw.text((date_x_centered, date_y), formatted_date, fill=(255, 255, 255), font=font_date)
        print(f"   📅 Date drawn: '{formatted_date}' at ({date_x_centered}, {date_y})")
        
        # Draw each line of affirmation text
        line_height = 70
        current_y = text_y
        
        for i, line in enumerate(wrapped_text):
            # Check if we're exceeding the max height
            if current_y + line_height > text_y + max_text_height:
                print(f"   ⚠️ Text overflow! Some lines may be cut off.")
                break
            
            # Draw text shadow for better readability
            draw.text((text_x + 2, current_y + 2), line, fill=(0, 0, 0, 100), font=font_affirmation)
            # Draw main text
            draw.text((text_x, current_y), line, fill=(255, 255, 255), font=font_affirmation)
            current_y += line_height
        
        print(f"   ✅ Drew {i+1} lines of affirmation text")
        
        # Save the final image
        img.save(output_path, quality=95)
        print(f"   ✅ Image saved: {output_path} ({os.path.getsize(output_path)} bytes)")
        
        return output_path
        
    except Exception as e:
        print(f"   ❌ Image creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def extract_thumbnail_from_video(video_path: str, output_path: str = None, time_seconds: float = 0.0) -> str:
    """Extract thumbnail from video - first frame"""
    print(f"\n🎬 Extracting thumbnail...")
    
    if output_path is None:
        output_path = video_path.replace('.mp4', '_thumbnail.png')
    
    THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT = 1280, 720
    
    try:
        from moviepy import VideoFileClip
        from PIL import Image
        
        clip = VideoFileClip(video_path)
        frame = clip.get_frame(time_seconds)
        clip.close()
        
        img = Image.fromarray(frame.astype('uint8'), 'RGB')
        img = img.resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)
        img.save(output_path, quality=90)
        
        print(f"   ✅ Thumbnail saved: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"   ❌ Thumbnail extraction failed: {e}")
        return None

def create_affirmation_video(image_path: str, output_path: str = None, slide_duration: int = 30, audio_file: str = None) -> str:
    """Create 30-second video with the affirmation image"""
    
    if output_path is None:
        output_path = image_path.replace('.png', '_video.mp4')
    
    print(f"\n🎬 Creating 30-second affirmation video...")
    print(f"   📷 Image: {image_path}")
    print(f"   ⏱️  Duration: {slide_duration} seconds")
    
    try:
        from moviepy import ImageClip
        from moviepy.audio.io.AudioFileClip import AudioFileClip
    except ImportError:
        try:
            from moviepy.editor import ImageClip, AudioFileClip
        except ImportError as e:
            print(f"   ❌ moviepy import failed: {e}")
            return None
    
    try:
        # Just use the image directly (no background needed since template has it all)
        clip = ImageClip(image_path, duration=slide_duration)
        
        # Handle audio
        audio_added = False
        
        if audio_file and os.path.exists(audio_file):
            try:
                audio = AudioFileClip(audio_file)
                if audio.duration < slide_duration:
                    loops = int(slide_duration / audio.duration) + 1
                    audio = audio.loop(loops)
                audio = audio.subclipped(0, slide_duration)
                clip = clip.with_audio(audio)
                audio_added = True
                print(f"   🎵 Audio added: {audio_file}")
            except Exception as e:
                print(f"   ⚠️ Audio error: {e}")
        
        if not audio_added:
            for audio in ["background_music.mp3", "audio.mp3", "music.mp3", "bgm.mp3"]:
                if os.path.exists(audio):
                    try:
                        audio_clip = AudioFileClip(audio)
                        if audio_clip.duration < slide_duration:
                            audio_clip = audio_clip.loop(int(slide_duration / audio_clip.duration) + 1)
                        audio_clip = audio_clip.subclipped(0, slide_duration)
                        clip = clip.with_audio(audio_clip)
                        audio_added = True
                        print(f"   🎵 Auto-detected audio: {audio}")
                        break
                    except:
                        continue
        
        # Write video
        clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac' if audio_added else None,
            fps=30,
            bitrate="5000k",
            preset='medium'
        )
        
        clip.close()
        
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
        os.makedirs(output_dir, exist_ok=True)
        self.playlist_id = None

    def find_page_for_date(self, target_date: str) -> dict:
        """Find the page containing the target date"""
        print(f"📄 Searching PDF for {target_date}...")
        
        if not os.path.exists(self.pdf_path):
            return None

        doc = fitz.open(self.pdf_path)
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        
        date_formats = [
            f"{date_obj.day} {date_obj.strftime('%B')} {date_obj.year}",
            f"{date_obj.strftime('%B')} {date_obj.day}, {date_obj.year}",
        ]
        
        for page_num in range(len(doc)):
            text = doc[page_num].get_text()
            for date_format in date_formats:
                if date_format in text:
                    doc.close()
                    return {
                        'page_num': page_num,
                        'display_num': page_num + 1,
                        'date': target_date,
                        'text': text
                    }
        
        doc.close()
        return None

    def get_affirmation_from_page(self, page_info: dict) -> str:
        return extract_affirmation_from_text(page_info['text'])

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

        full_title = f"Creative Daily Affirmation | {formatted_date} | Stupid Orange"
        
        video_description = f"""🌟 DAILY AFFIRMATION - {formatted_date} 🌟

{affirmation_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ Join the Creative Daily community and start collecting royalties from your creativity!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 www.stupidorange.com
📘 creativedaily.stupidorange.com

#affirmation #dailyaffirmation #creativedaily #stupidestbrokeguy #UAE #Dubai
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

            thumbnail_path = extract_thumbnail_from_video(video_path, time_seconds=0.0)
            
            body = {
                'snippet': {
                    'title': full_title[:100],
                    'description': video_description[:5000],
                    'tags': ['affirmation', 'dailyaffirmation', 'creativedaily', 'stupidestbrokeguy'],
                    'categoryId': '22'
                },
                'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
            }

            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
            response = request.execute()
            video_url = f"https://youtu.be/{response['id']}"

            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    youtube.thumbnails().set(
                        videoId=response['id'],
                        media_body=MediaFileUpload(thumbnail_path)
                    ).execute()
                    os.remove(thumbnail_path)
                except Exception as e:
                    print(f"   ⚠️ Thumbnail upload failed: {e}")

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

    def process_date(self, target_date: str, post_to_youtube: bool = True, audio_file: str = None) -> dict:
        print("="*60)
        print("✨ CREATIVE DAILY - AFFIRMATION WITH CANVA TEMPLATE")
        print("="*60)
        print(f"📅 Target Date: {target_date}")
        print(f"📹 YouTube Upload: {'ON' if post_to_youtube else 'OFF'}")
        print("="*60)

        page_info = self.find_page_for_date(target_date)
        if not page_info:
            return {'status': 'not_found', 'date': target_date}

        print(f"✅ Found on page {page_info['display_num']}")

        affirmation = self.get_affirmation_from_page(page_info)
        if not affirmation:
            return {'status': 'no_affirmation', 'date': target_date}

        print(f"\n📝 Affirmation extracted:")
        print(f"   {affirmation[:150]}...")

        # Create image using Canva template
        image_path = create_affirmation_image_from_template(
            affirmation, 
            target_date, 
            os.path.join(self.output_dir, f"affirmation_{target_date}.png")
        )

        if not image_path:
            return {'status': 'image_failed', 'date': target_date}

        # Create video
        video_path = create_affirmation_video(
            image_path=image_path,
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
            'image_path': image_path,
            'video_path': video_path,
            'youtube': youtube_result
        }

if __name__ == "__main__":
    print("="*60)
    print("✨ AFFIRMATION WITH CANVA TEMPLATE")
    print("="*60)
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"📁 Files: {os.listdir('.')}")
    print("="*60)

    PDF_PATH = "your_document.pdf"
    OUTPUT_DIR = "affirmation_pages"

    target_date = None
    post_to_youtube = True
    audio_file = None

    for arg in sys.argv[1:]:
        if arg == "--no-youtube":
            post_to_youtube = False
        elif arg.startswith("--audio="):
            audio_file = arg.split("=")[1]
        elif re.match(r'\d{4}-\d{2}-\d{2}', arg):
            target_date = arg

    if target_date is None:
        target_date = "2026-06-07"

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
        print(f"   🖼️ Image: {result.get('image_path', 'N/A')}")
        print(f"   🎬 Video: {result.get('video_path', 'N/A')}")
        
        if result.get('youtube') and result['youtube']['status'] == 'success':
            print(f"\n📹 POSTED TO YOUTUBE!")
            print(f"   🔗 URL: {result['youtube']['video_url']}")
        
        sys.exit(0)
    else:
        print(f"❌ FAILED: {result.get('status')}")
        sys.exit(1)
