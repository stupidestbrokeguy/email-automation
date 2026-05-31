#!/usr/bin/env python3
"""
Creative Daily - Affirmation Focused
Extracts ONLY the affirmation (stops at Related Saying)
Creates custom affirmation image with logo and 30-second video
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
    """
    Extract ONLY the affirmation text from a page.
    Stops at 'Related Saying', 'creativelydaily', or any other section.
    Does NOT include anything after the affirmation.
    """
    print(f"   🔍 Looking for affirmation in {len(page_text)} chars...")
    
    # Method 1: Look for pattern with clear end markers
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
    
    # Method 2: Line-by-line extraction with clear stop at "Related Saying"
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
    
    # Method 3: Look for text between "Affirmation:" and the next period that ends a sentence
    affirmation_match = re.search(r'Affirmation:?\s*([^.!?]+[.!?])', page_text, re.IGNORECASE)
    if affirmation_match:
        affirmation = affirmation_match.group(1).strip()
        print(f"   ✅ Found affirmation via sentence boundary ({len(affirmation)} chars)")
        return affirmation
    
    print(f"   ⚠️ No affirmation found in text")
    return None

def create_affirmation_image(affirmation_text: str, target_date: str, output_path: str = None, logo_path: str = "stupidorange_logo.png") -> str:
    """Create a custom PNG image with title, affirmation text, and logo - Creative Design"""
    
    if output_path is None:
        output_path = f"affirmation_{target_date}.png"
    
    print(f"\n🎨 Creating creative affirmation image with logo...")
    print(f"   📅 Date: {target_date}")
    print(f"   💬 Text: {affirmation_text[:80]}...")
    print(f"   🖼️ Logo path: {logo_path}")
    print(f"   📁 Current directory: {os.getcwd()}")
    
    # Check if logo exists
    logo_exists = os.path.exists(logo_path)
    print(f"   📁 Logo file exists: {logo_exists}")
    
    if logo_exists:
        logo_size = os.path.getsize(logo_path)
        print(f"   📏 Logo file size: {logo_size} bytes")
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        import textwrap
        
        # Image dimensions (16:9 ratio for YouTube)
        width, height = 1920, 1080
        print(f"   📐 Image dimensions: {width}x{height}")
        
        # Create gradient background (yellow to orange)
        img = Image.new('RGB', (width, height), color=(255, 215, 0))
        draw = ImageDraw.Draw(img)
        
        # Add gradient effect (vertical gradient from light yellow to warm orange)
        print(f"   🎨 Creating gradient background...")
        for y in range(height):
            factor = y / height
            r = int(255 - factor * 0)
            g = int(245 - factor * 105)
            b = int(200 - factor * 200)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        # Load fonts with fallbacks
        try:
            font_title_bold = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 85)
            font_title_light = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 55)
            font_affirmation = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 50)
            font_affirmation_bold = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 52)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 35)
            print(f"   ✅ Loaded Liberation fonts")
        except:
            try:
                font_title_bold = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 85)
                font_title_light = ImageFont.truetype("/System/Library/Fonts/Helvetica-Light.ttf", 55)
                font_affirmation = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 50)
                font_affirmation_bold = ImageFont.truetype("/System/Library/Fonts/Helvetica-Bold.ttf", 52)
                font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 35)
                print(f"   ✅ Loaded Helvetica fonts")
            except:
                font_title_bold = ImageFont.load_default()
                font_title_light = ImageFont.load_default()
                font_affirmation = ImageFont.load_default()
                font_affirmation_bold = ImageFont.load_default()
                font_small = ImageFont.load_default()
                print(f"   ⚠️ Using default fonts")
        
        # Format date
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%B %d, %Y")
        print(f"   📅 Formatted date: {formatted_date}")
        
        # Load and place logo in top-right corner with detailed debugging
        logo_placed = False
        
        if logo_path and os.path.exists(logo_path):
            try:
                print(f"   🖼️ Attempting to load logo: {logo_path}")
                logo = Image.open(logo_path)
                print(f"   📐 Original logo size: {logo.width}x{logo.height}")
                print(f"   🎨 Logo mode: {logo.mode}")
                
                # Resize logo to fit nicely (max 120px height)
                logo_max_height = 120
                logo_ratio = logo.width / logo.height
                print(f"   📐 Logo aspect ratio: {logo_ratio:.2f}")
                
                if logo.height > logo_max_height:
                    new_height = logo_max_height
                    new_width = int(logo_ratio * new_height)
                    print(f"   🔄 Resizing logo from {logo.width}x{logo.height} to {new_width}x{new_height}")
                    logo = logo.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    print(f"   ✅ Logo resized successfully")
                else:
                    print(f"   ✅ Logo already fits (height {logo.height} <= {logo_max_height})")
                
                # Position: top-right with margin
                logo_margin = 40
                logo_x = width - logo.width - logo_margin
                logo_y = logo_margin
                print(f"   📍 Logo position: x={logo_x}, y={logo_y}")
                print(f"   📍 Logo will occupy area: ({logo_x}, {logo_y}) to ({logo_x + logo.width}, {logo_y + logo.height})")
                
                # Paste logo (handle transparency)
                if logo.mode == 'RGBA':
                    print(f"   🎨 Logo has transparency (RGBA), pasting with alpha mask")
                    img.paste(logo, (logo_x, logo_y), logo)
                else:
                    print(f"   🎨 Logo has no transparency (RGB), pasting directly")
                    img.paste(logo, (logo_x, logo_y))
                
                logo_placed = True
                print(f"   ✅ LOGO PLACED SUCCESSFULLY at top-right corner!")
                
                # Draw a subtle glow behind logo
                glow_size = 20
                draw.ellipse(
                    [(logo_x - glow_size, logo_y - glow_size),
                     (logo_x + logo.width + glow_size, logo_y + logo.height + glow_size)],
                    fill=(255, 200, 100),
                    outline=None
                )
                print(f"   ✨ Added glow effect behind logo")
                
            except Exception as e:
                print(f"   ❌ Could not place logo: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"   ⚠️ Logo file not found at: {logo_path}")
            print(f"   📁 Looking for logo in: {os.path.abspath(logo_path)}")
            print(f"   📁 Files in current directory: {os.listdir('.')}")
        
        if not logo_placed:
            print(f"   🎨 Creating fallback logo (orange circle with 'SO')")
            # Draw decorative orange circle as fallback logo
            circle_x = width - 100
            circle_y = 80
            circle_radius = 50
            draw.ellipse(
                [(circle_x - circle_radius, circle_y - circle_radius),
                 (circle_x + circle_radius, circle_y + circle_radius)],
                fill=(255, 100, 0)
            )
            draw.text((circle_x - 25, circle_y - 20), "SO", fill=(255, 255, 255), font=font_title_bold)
            print(f"   ✅ Fallback logo placed at ({circle_x}, {circle_y})")
        
        # Draw decorative top bar (thin orange line)
        draw.line([(0, 0), (width, 0)], fill=(255, 100, 0), width=8)
        
        # Draw title with glow effect
        title = "✨ CREATIVE DAILY AFFIRMATION ✨"
        title_bbox = draw.textbbox((0, 0), title, font=font_title_bold)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2
        title_y = 100
        
        # Title shadow/glow
        for offset in range(3):
            draw.text((title_x + offset, title_y + offset), title, fill=(255, 180, 50), font=font_title_bold)
        draw.text((title_x, title_y), title, fill=(255, 255, 255), font=font_title_bold)
        
        # Draw decorative stars around title
        star_positions = [(-60, 20), (title_width + 60, 20), (-80, 60), (title_width + 80, 60)]
        for star_x, star_y in star_positions:
            draw.text((title_x + star_x, title_y + star_y), "⭐", fill=(255, 200, 0), font=font_title_light)
        
        # Draw date with creative styling
        subtitle = formatted_date
        sub_bbox = draw.textbbox((0, 0), subtitle, font=font_title_light)
        sub_width = sub_bbox[2] - sub_bbox[0]
        sub_x = (width - sub_width) // 2
        sub_y = title_y + 110
        
        # Date background pill
        pill_padding = 30
        pill_height = 70
        draw.rounded_rectangle(
            [(sub_x - pill_padding, sub_y - 15),
             (sub_x + sub_width + pill_padding, sub_y + pill_height - 20)],
            radius=35,
            fill=(255, 140, 0),
            outline=(255, 200, 100),
            width=2
        )
        draw.text((sub_x, sub_y), subtitle, fill=(255, 255, 255), font=font_title_light)
        
        # Draw decorative divider with diamond
        divider_y = sub_y + 80
        draw.line([(300, divider_y), (width//2 - 60, divider_y)], fill=(255, 140, 0), width=3)
        draw.line([(width//2 + 60, divider_y), (width - 300, divider_y)], fill=(255, 140, 0), width=3)
        diamond_points = [
            (width//2, divider_y - 12),
            (width//2 + 12, divider_y),
            (width//2, divider_y + 12),
            (width//2 - 12, divider_y)
        ]
        draw.polygon(diamond_points, fill=(255, 100, 0))
        
        # Wrap and draw affirmation text (ONLY the affirmation, no extra content)
        wrapped_text = textwrap.wrap(affirmation_text, width=45)
        print(f"   📝 Wrapped affirmation into {len(wrapped_text)} lines")
        
        # Calculate text position (centered vertically)
        line_height = 70
        total_text_height = len(wrapped_text) * line_height
        text_start_y = (height - total_text_height) // 2 + 50
        
        # Draw each line with background for readability
        for i, line in enumerate(wrapped_text):
            line_bbox = draw.textbbox((0, 0), line, font=font_affirmation_bold)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (width - line_width) // 2
            line_y = text_start_y + (i * line_height)
            
            # Semi-transparent background for text readability
            bg_padding = 40
            bg_height = 65
            draw.rounded_rectangle(
                [(line_x - bg_padding, line_y - 15),
                 (line_x + line_width + bg_padding, line_y + bg_height - 20)],
                radius=20,
                fill=(0, 0, 0),
                outline=(255, 200, 100),
                width=1
            )
            draw.text((line_x, line_y), line, fill=(255, 255, 255), font=font_affirmation_bold)
        
        # Draw decorative bottom section with website link
        bottom_y = height - 100
        
        # Decorative wave pattern
        for x in range(0, width, 40):
            wave_y = bottom_y - 20 + (x % 80) / 80 * 4
            draw.point([(x, wave_y)], fill=(255, 140, 0))
        
        # Draw website URL (always included after every affirmation)
        website = "creativelydaily.stupidorange.com"
        web_bbox = draw.textbbox((0, 0), website, font=font_small)
        web_width = web_bbox[2] - web_bbox[0]
        
        # Website background pill
        web_bg_padding = 25
        draw.rounded_rectangle(
            [((width - web_width) // 2 - web_bg_padding, bottom_y - 15),
             ((width - web_width) // 2 + web_width + web_bg_padding, bottom_y + 35)],
            radius=25,
            fill=(255, 140, 0),
            outline=(255, 200, 100),
            width=1
        )
        draw.text(((width - web_width) // 2, bottom_y), website, fill=(255, 255, 255), font=font_small)
        
        # Draw small decorative sparkles
        sparkle_positions = [
            (100, 200), (width - 100, 200),
            (150, height - 150), (width - 150, height - 150),
            (width - 200, 300), (200, height - 250)
        ]
        for sx, sy in sparkle_positions:
            draw.text((sx, sy), "✦", fill=(255, 200, 0), font=font_small)
        
        # Save image with high quality
        img.save(output_path, quality=95, dpi=(300, 300))
        print(f"   ✅ Creative affirmation image saved: {output_path}")
        print(f"   📏 File size: {os.path.getsize(output_path)} bytes")
        
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
        
        if img_width != screen_width or img_height != screen_height:
            pil_img = pil_img.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
            temp_img_path = image_path.replace('.png', '_resized.png')
            pil_img.save(temp_img_path)
        else:
            temp_img_path = image_path
        
        image_clip = ImageClip(temp_img_path, duration=slide_duration)
        background = ColorClip(size=(screen_width, screen_height), color=bg_color, duration=slide_duration)
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
        print(f"🔧 AffirmationExtractor initialized")
        print(f"   📁 PDF path: {pdf_path}")
        print(f"   📁 Output dir: {output_dir}")

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
            print(f"   ❌ PDF not found: {self.pdf_path}")
            return None

        doc = fitz.open(self.pdf_path)
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        
        date_formats = [
            f"{date_obj.day} {date_obj.strftime('%B')} {date_obj.year}",
            f"{date_obj.strftime('%B')} {date_obj.day}, {date_obj.year}",
            f"{date_obj.day}-{date_obj.strftime('%B')}-{date_obj.year}",
        ]
        
        print(f"   🔍 Looking for date formats: {date_formats}")
        
        for page_num in range(len(doc)):
            text = doc[page_num].get_text()
            for date_format in date_formats:
                if date_format in text:
                    print(f"   ✅ Found on page {page_num + 1}")
                    doc.close()
                    return {
                        'page_num': page_num,
                        'display_num': page_num + 1,
                        'date': target_date,
                        'text': text
                    }
        
        doc.close()
        print(f"   ❌ Date {target_date} not found in PDF")
        return None

    def get_affirmation_from_page(self, page_info: dict) -> str:
        """Extract ONLY affirmation from page text"""
        return extract_affirmation_from_text(page_info['text'])

    def create_or_get_playlist(self, youtube) -> str:
        playlists = youtube.playlists().list(part='snippet', mine=True, maxResults=50).execute()
        
        for playlist in playlists.get('items', []):
            if playlist['snippet']['title'] == PLAYLIST_TITLE:
                print(f"   ✅ Found existing playlist: {playlist['id']}")
                return playlist['id']

        response = youtube.playlists().insert(
            part='snippet,status',
            body={
                'snippet': {'title': PLAYLIST_TITLE, 'description': PLAYLIST_DESCRIPTION},
                'status': {'privacyStatus': 'public'}
            }
        ).execute()
        print(f"   ✅ Created new playlist: {response['id']}")
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
                print(f"   ✅ Loaded credentials from {TOKEN_FILE}")

            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    print(f"   🔄 Refreshing expired token...")
                    credentials.refresh(Request())
                else:
                    if not os.path.exists(CLIENT_SECRETS_FILE):
                        return {'status': 'failed', 'error': 'No credentials'}
                    
                    free_port = find_free_port()
                    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
                    credentials = flow.run_local_server(port=free_port, open_browser=True)
                    print(f"   ✅ Authentication successful")
                
                with open(TOKEN_FILE, 'wb') as f:
                    pickle.dump(credentials, f)
                print(f"   💾 Saved credentials to {TOKEN_FILE}")

            youtube = build('youtube', 'v3', credentials=credentials)
            print(f"   ✅ YouTube service built")

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
            print(f"   ✅ Video uploaded! ID: {response['id']}")

            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    youtube.thumbnails().set(
                        videoId=response['id'],
                        media_body=MediaFileUpload(thumbnail_path)
                    ).execute()
                    os.remove(thumbnail_path)
                    print(f"   ✅ Thumbnail uploaded!")
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
            print(f"   ✅ Added to playlist: {PLAYLIST_TITLE}")

            return {'status': 'success', 'video_url': video_url}

        except Exception as e:
            print(f"   ❌ Upload failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    def process_date(self, target_date: str, post_to_youtube: bool = True,
                     audio_file: str = None) -> dict:
        print("="*60)
        print("✨ CREATIVE DAILY - AFFIRMATION EXTRACTOR (30 sec)")
        print("="*60)
        print(f"📅 Target Date: {target_date}")
        print(f"📹 YouTube Upload: {'ON' if post_to_youtube else 'OFF'}")
        print(f"🎵 Audio File: {audio_file if audio_file else 'Auto-detect'}")
        print("="*60)

        page_info = self.find_page_for_date(target_date)
        if not page_info:
            return {'status': 'not_found', 'date': target_date}

        print(f"✅ Found on page {page_info['display_num']}")

        affirmation = self.get_affirmation_from_page(page_info)
        if not affirmation:
            return {'status': 'no_affirmation', 'date': target_date}

        print(f"\n📝 Affirmation extracted (no quotes, no extra content):")
        print(f"   {affirmation[:200]}...")
        print(f"   Total length: {len(affirmation)} characters")

        # Create custom affirmation image with logo
        image_path = create_affirmation_image(
            affirmation, 
            target_date, 
            os.path.join(self.output_dir, f"affirmation_{target_date}.png"),
            logo_path="stupidorange_logo.png"
        )

        if not image_path:
            return {'status': 'image_failed', 'date': target_date}

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
    print("✨ AFFIRMATION EXTRACTOR - CUSTOM IMAGE WITH LOGO DEBUGGING")
    print("="*60)
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Current working directory: {os.getcwd()}")
    print(f"📁 Files in directory: {os.listdir('.')}")
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
        print(f"💡 Make sure '{PDF_PATH}' exists in the current directory")
        sys.exit(1)
    else:
        pdf_size = os.path.getsize(PDF_PATH) / (1024 * 1024)
        print(f"✅ PDF found: {PDF_PATH} ({pdf_size:.1f} MB)")

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
        
        if os.path.exists(result.get('image_path', '')):
            img_size = os.path.getsize(result['image_path']) / 1024
            print(f"   📏 Image size: {img_size:.1f} KB")
        
        print(f"   🎬 Video: {result.get('video_path', 'N/A')}")
        
        if result.get('video_path') and os.path.exists(result['video_path']):
            video_size = os.path.getsize(result['video_path']) / (1024 * 1024)
            print(f"   📏 Video size: {video_size:.1f} MB")
        
        if result.get('youtube') and result['youtube']['status'] == 'success':
            print(f"\n📹 POSTED TO YOUTUBE!")
            print(f"   🔗 URL: {result['youtube']['video_url']}")
        elif result.get('youtube') and result['youtube']['status'] == 'failed':
            print(f"\n❌ YouTube upload failed: {result['youtube'].get('error', 'Unknown')}")
        
        sys.exit(0)
    else:
        print(f"❌ FAILED: {result.get('status')}")
        sys.exit(1)
