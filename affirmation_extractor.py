#!/usr/bin/env python3
"""
Creative Daily - Affirmation Focused
Creates custom affirmation PNG and 30-second video
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
    """Extract the affirmation text from a page - NO QUOTES"""
    print(f"   🔍 Looking for affirmation in {len(page_text)} chars...")
    
    patterns = [
        r'(?:Affirmation:?\s*)([^A-Z]+?)(?=(?:creativelydaily|Related Saying|$))',
        r'(?:Affirmation:?\s*)(.+?)(?=(?:creativelydaily|Related Saying|$))',
        r'(?:Affirmation:?\s*\n)((?:.+\n)+?)(?=\n*(?:creativelydaily|Related Saying|\n\n|$))',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
        if match:
            affirmation = match.group(1).strip()
            affirmation = re.sub(r'\s+', ' ', affirmation)
            # Remove any quotes that might be in the text
            affirmation = affirmation.strip('"\'')
            affirmation = affirmation.replace('creativelydaily.stupidorange.com', '')
            affirmation = affirmation.strip()
            if len(affirmation) > 20:
                print(f"   ✅ Found affirmation ({len(affirmation)} chars)")
                return affirmation
    
    # Fallback line-by-line search
    lines = page_text.split('\n')
    affirmation_lines = []
    capture = False
    
    for line in lines:
        line_stripped = line.strip()
        if 'affirmation' in line_stripped.lower():
            capture = True
            parts = re.split(r'Affirmation:?\s*', line_stripped, flags=re.IGNORECASE)
            if len(parts) > 1 and parts[1]:
                affirmation_lines.append(parts[1].strip('"\''))
            continue
        
        if capture:
            if line_stripped and not line_stripped.startswith('http') and 'creativelydaily' not in line_stripped.lower():
                if 'Related Saying' in line_stripped or 'creativelydaily' in line_stripped.lower():
                    break
                affirmation_lines.append(line_stripped)
    
    if affirmation_lines:
        result = ' '.join(affirmation_lines).strip()
        result = result.strip('"\'')
        print(f"   ✅ Found affirmation via fallback ({len(result)} chars)")
        return result
    
    print(f"   ⚠️ No affirmation found")
    return None

def create_affirmation_image(affirmation_text: str, target_date: str, output_path: str = None) -> str:
    """Create a custom PNG image with title and affirmation text (no quotes)"""
    
    if output_path is None:
        output_path = f"affirmation_{target_date}.png"
    
    print(f"\n🎨 Creating custom affirmation image...")
    print(f"   📅 Date: {target_date}")
    print(f"   💬 Text: {affirmation_text[:80]}...")
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        import textwrap
        
        # Image dimensions (1080x1080 for square, or 1920x1080 for wide)
        width, height = 1920, 1080
        
        # Create yellow background (same as video)
        img = Image.new('RGB', (width, height), color=(255, 215, 0))
        draw = ImageDraw.Draw(img)
        
        # Try to load fonts, fall back to default
        try:
            # Try to find a bold font
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 72)
            font_affirmation = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 48)
        except:
            try:
                font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
                font_affirmation = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
            except:
                # Default font
                font_title = ImageFont.load_default()
                font_affirmation = ImageFont.load_default()
        
        # Format date
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%B %d, %Y")
        
        # Draw title
        title = f"✨ CREATIVE DAILY AFFIRMATION ✨"
        subtitle = formatted_date
        
        # Get title size and position
        title_bbox = draw.textbbox((0, 0), title, font=font_title)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2
        title_y = 80
        
        # Draw title with outline for better visibility
        draw.text((title_x, title_y), title, fill=(0, 0, 0), font=font_title)
        
        # Draw subtitle
        sub_bbox = draw.textbbox((0, 0), subtitle, font=font_affirmation)
        sub_width = sub_bbox[2] - sub_bbox[0]
        sub_x = (width - sub_width) // 2
        sub_y = title_y + 80
        draw.text((sub_x, sub_y), subtitle, fill=(100, 80, 0), font=font_affirmation)
        
        # Draw divider line
        line_y = sub_y + 50
        draw.line([(200, line_y), (width - 200, line_y)], fill=(0, 0, 0), width=3)
        
        # Wrap and draw affirmation text (NO QUOTES)
        wrapped_text = textwrap.wrap(affirmation_text, width=50)
        
        # Calculate text position (centered vertically)
        line_height = 60
        total_text_height = len(wrapped_text) * line_height
        text_start_y = (height - total_text_height) // 2 + 50
        
        for i, line in enumerate(wrapped_text):
            line_bbox = draw.textbbox((0, 0), line, font=font_affirmation)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (width - line_width) // 2
            line_y = text_start_y + (i * line_height)
            draw.text((line_x, line_y), line, fill=(0, 0, 0), font=font_affirmation)
        
        # Draw decorative elements
        # Small orange circle logo (Stupid Orange)
        circle_center_x = width - 80
        circle_center_y = height - 80
        circle_radius = 40
        draw.ellipse(
            [(circle_center_x - circle_radius, circle_center_y - circle_radius),
             (circle_center_x + circle_radius, circle_center_y + circle_radius)],
            fill=(255, 140, 0)
        )
        draw.text((circle_center_x - 15, circle_center_y - 15), "SO", fill=(255, 255, 255), font=font_affirmation)
        
        # Draw website at bottom
        website = "creativelydaily.stupidorange.com"
        web_bbox = draw.textbbox((0, 0), website, font=font_affirmation)
        web_width = web_bbox[2] - web_bbox[0]
        draw.text(((width - web_width) // 2, height - 50), website, fill=(100, 80, 0), font=font_affirmation)
        
        # Save image
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
        
        # Resize to thumbnail dimensions
        img = img.resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)
        img.save(output_path, quality=90)
        
        print(f"   ✅ Thumbnail saved: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"   ❌ Thumbnail extraction failed: {e}")
        return None

def create_affirmation_video(image_path: str, affirmation_text: str, target_date: str,
                              output_path: str = None,
                              bg_color: tuple = (255, 215, 0),
                              slide_duration: int = 30,
                              audio_file: str = None) -> str:
    """Create 30-second video with custom affirmation image"""
    
    if output_path is None:
        output_path = image_path.replace('.png', '_video.mp4')
    
    print(f"\n🎬 Creating 30-second affirmation video...")
    print(f"   📷 Image: {image_path}")
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
        
        # If image is not already 1920x1080, resize to fit
        if img_width != screen_width or img_height != screen_height:
            pil_img = pil_img.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
            temp_img_path = image_path.replace('.png', '_resized.png')
            pil_img.save(temp_img_path)
        else:
            temp_img_path = image_path
        
        # Create image clip (no sliding animation since image fills screen)
        image_clip = ImageClip(temp_img_path, duration=slide_duration)
        
        # Create yellow background (just in case)
        background = ColorClip(size=(screen_width, screen_height), color=bg_color, duration=slide_duration)
        
        # Composite (image on top of background)
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
        if temp_img_path != image_path and os.path.exists(temp_img_path):
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

    def find_page_for_date(self, target_date: str) -> dict:
        """Find the page containing the target date"""
        print(f"📄 Searching PDF for {target_date}...")
        
        if not os.path.exists(self.pdf_path):
            return None

        doc = fitz.open(self.pdf_path)
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        
        # Try different date formats
        date_formats = [
            f"{date_obj.day} {date_obj.strftime('%B')} {date_obj.year}",
            f"{date_obj.strftime('%B')} {date_obj.day}, {date_obj.year}",
            f"{date_obj.day}-{date_obj.strftime('%B')}-{date_obj.year}",
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
        """Extract affirmation from page text"""
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

            # Extract thumbnail
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

    def process_date(self, target_date: str, post_to_youtube: bool = True,
                     audio_file: str = None) -> dict:
        print("="*60)
        print("✨ CREATIVE DAILY - AFFIRMATION EXTRACTOR (30 sec)")
        print("="*60)
        print(f"📅 Target Date: {target_date}")

        # Find page with the date
        page_info = self.find_page_for_date(target_date)
        if not page_info:
            return {'status': 'not_found', 'date': target_date}

        print(f"✅ Found on page {page_info['display_num']}")

        # Extract affirmation
        affirmation = self.get_affirmation_from_page(page_info)
        if not affirmation:
            return {'status': 'no_affirmation', 'date': target_date}

        print(f"\n📝 Affirmation extracted (no quotes):")
        print(f"   {affirmation[:150]}...")

        # Create custom affirmation image (NOT the PDF page)
        image_path = create_affirmation_image(affirmation, target_date, 
                                               os.path.join(self.output_dir, f"affirmation_{target_date}.png"))

        if not image_path:
            return {'status': 'image_failed', 'date': target_date}

        # Create 30-second video
        video_path = create_affirmation_video(
            image_path=image_path,
            affirmation_text=affirmation,
            target_date=target_date,
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
    print("✨ AFFIRMATION EXTRACTOR - CUSTOM IMAGE (NO QUOTES)")
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
        target_date = "2026-06-07"  # Default to June 7

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
        print(f"   🖼️ Image: {result.get('image_path', 'N/A')}")
        print(f"   🎬 Video: {result.get('video_path', 'N/A')}")
        
        if result.get('youtube') and result['youtube']['status'] == 'success':
            print(f"\n📹 POSTED TO YOUTUBE!")
            print(f"   🔗 URL: {result['youtube']['video_url']}")
        
        sys.exit(0)
    else:
        print(f"❌ FAILED: {result.get('status')}")
        sys.exit(1)
