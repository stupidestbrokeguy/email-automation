"""
Complete Calendar Date Extractor & YouTube Poster
Full page text formatted nicely, each line on its own
"""

import os
import re
import sys
from datetime import datetime
import fitz  # PyMuPDF
import pickle
import socket

def find_free_port(start_port=8080, end_port=8090):
    """Find a free port to use for OAuth callback"""
    for port in range(start_port, end_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except socket.error:
                continue
    return 8080

def convert_png_to_mp4(png_path: str, duration: int = 5) -> str:
    """
    Convert a PNG image to MP4 video using moviepy
    """
    mp4_path = png_path.replace('.png', '.mp4')
    
    if os.path.exists(mp4_path):
        print(f"   ✅ MP4 already exists: {os.path.basename(mp4_path)}")
        return mp4_path
    
    print(f"   🎬 Converting PNG to MP4...")
    
    try:
        from moviepy import ImageClip
        print(f"   Using moviepy for conversion...")
        
        clip = ImageClip(png_path, duration=duration)
        clip = clip.resized(height=1080)
        clip = clip.with_fps(30)
        clip.write_videofile(mp4_path, codec='libx264', logger=None)
        clip.close()
        
        print(f"   ✅ Converted to MP4: {os.path.basename(mp4_path)}")
        return mp4_path
        
    except ImportError:
        try:
            from moviepy.editor import ImageClip
            print(f"   Using moviepy (legacy) for conversion...")
            
            clip = ImageClip(png_path, duration=duration)
            clip = clip.resize(height=1080)
            clip = clip.set_fps(30)
            clip.write_videofile(mp4_path, codec='libx264', verbose=False, logger=None)
            clip.close()
            
            print(f"   ✅ Converted to MP4: {os.path.basename(mp4_path)}")
            return mp4_path
            
        except ImportError:
            print(f"   ❌ moviepy import failed")
            return None
            
    except Exception as e:
        print(f"   ❌ Conversion failed: {e}")
        return None

class CompleteCalendarExtractor:
    """
    Complete solution: Extract dates from PDF, convert to images, convert to video, post to YouTube
    """
    
    def __init__(self, pdf_path: str, output_dir: str = "extracted_date_pages"):
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        
        self.date_patterns = [
            r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b',
            r'\b\d{2}/\d{2}/\d{4}\b',
            r'\b\d{4}-\d{2}-\d{2}\b',
            r'\b\d{2}\.\d{2}\.\d{4}\b',
        ]
        
        os.makedirs(output_dir, exist_ok=True)
        
    def extract_date_from_text(self, text: str) -> str:
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                parsed = self.parse_date(match)
                if parsed:
                    return parsed
        return None
    
    def parse_date(self, date_str: str) -> str:
        formats = [
            ("%d %B %Y", None),
            ("%B %d, %Y", None),
            ("%d/%m/%Y", None),
            ("%m/%d/%Y", None),
            ("%Y-%m-%d", None),
            ("%d.%m.%Y", None),
        ]
        
        date_str_clean = date_str.strip()
        
        for fmt, _ in formats:
            try:
                dt = datetime.strptime(date_str_clean, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None
    
    def format_date_for_title(self, date_str: str) -> str:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%B %d, %Y")
        except:
            return date_str
    
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
                    'text': text  # Store full text now
                })
                print(f"   ✓ Page {page_num + 1} -> {date_str}")
        
        doc.close()
        print(f"\n📊 Found {len(date_page_map)} unique dates in the PDF")
        return date_page_map
    
    def convert_page_to_image(self, page_info: dict, dpi: int = 150) -> str:
        doc = fitz.open(self.pdf_path)
        page = doc[page_info['page_num']]
        
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        date_obj = datetime.strptime(page_info['date'], "%Y-%m-%d")
        day = date_obj.day
        month = date_obj.strftime("%B")
        year = date_obj.year
        filename = f"{day}_{month}_{year}_page_{page_info['display_num']}.png"
        image_path = os.path.join(self.output_dir, filename)
        
        pix.save(image_path)
        
        # Save the full text for later use
        text_file = image_path.replace('.png', '_text.txt')
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(page_info['text'])
        
        doc.close()
        print(f"   🖼️ Saved: {filename}")
        
        return image_path
    
    def ensure_image_for_date(self, target_date: str, dpi: int = 150) -> dict:
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        day = date_obj.day
        month = date_obj.strftime("%B")
        year = date_obj.year
        expected_pattern = f"{day}_{month}_{year}_page_"
        
        existing_images = []
        if os.path.exists(self.output_dir):
            for file in os.listdir(self.output_dir):
                if file.startswith(expected_pattern) and file.endswith('.png'):
                    existing_images.append(os.path.join(self.output_dir, file))
        
        if existing_images:
            print(f"✅ Image already exists: {os.path.basename(existing_images[0])}")
            page_match = re.search(r'page_(\d+)', existing_images[0])
            return {
                'status': 'exists',
                'image_path': existing_images[0],
                'page_num': page_match.group(1) if page_match else None
            }
        
        print(f"\n🔍 Searching for date {target_date} in PDF...")
        date_map = self.find_all_date_pages()
        
        if target_date in date_map:
            page_info = date_map[target_date][0]
            print(f"\n📄 Found on page {page_info['display_num']}")
            image_path = self.convert_page_to_image(page_info, dpi)
            
            return {
                'status': 'extracted',
                'image_path': image_path,
                'page_num': page_info['display_num']
            }
        else:
            print(f"❌ Date {target_date} not found in the PDF!")
            return {
                'status': 'not_found',
                'image_path': None,
                'page_num': None
            }
    
    def get_page_text_content(self, image_path: str) -> str:
        """Get the full page text, each line on its own (no page numbers or headers)"""
        text_file = image_path.replace('.png', '_text.txt')
        if os.path.exists(text_file):
            with open(text_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Clean up the text - remove extra spaces, keep line breaks
                lines = content.split('\n')
                
                # Filter out empty lines and clean each line
                cleaned_lines = []
                for line in lines:
                    line = line.strip()
                    if line:  # Only keep non-empty lines
                        # Remove any page number patterns if they exist
                        line = re.sub(r'Page \d+', '', line)
                        line = re.sub(r'^\d+\s*$', '', line)  # Remove standalone page numbers
                        line = line.strip()
                        if line:
                            cleaned_lines.append(line)
                
                # Join with double newline for better readability
                formatted_text = '\n\n'.join(cleaned_lines)
                
                return formatted_text
        return ""
    
    def upload_to_youtube(self, video_path: str, target_date: str, page_text: str = "") -> dict:
        """Upload video to YouTube with custom title and formatted description"""
        print(f"\n📤 Uploading to YouTube...")
        
        # Format date for display
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%B %d, %Y")
        
        # ===== CUSTOM TITLE =====
        video_title = f"Creative Daily | {formatted_date} | Stupid Orange | Stupidest Broke Guy | #Dubai #stupidestbrokeguy #DubaiCreatives #creativedaily #stupidorange"
        
        # ===== CUSTOM DESCRIPTION =====
        if page_text:
            description_text = page_text
        else:
            description_text = f"Daily calendar page for {formatted_date}"
        
        video_description = f"""{description_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ Creative Daily | {formatted_date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#creativedaily #trending #viral #viralvideo #trendingnow #explore #fyp
"""
        
        print(f"   📝 Title: {video_title[:80]}...")
        print(f"   📝 Description length: {len(description_text)} characters")
        print(f"   📝 Hashtags: #creativedaily #trending #viral #fyp")
        
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            
            SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
            CLIENT_SECRETS_FILE = "client_secrets.json"
            TOKEN_FILE = "token.pickle"
            
            credentials = None
            
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, 'rb') as f:
                    credentials = pickle.load(f)
                print("   📂 Loaded saved credentials")
            
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    print("   🔄 Refreshing expired token...")
                    credentials.refresh(Request())
                else:
                    if not os.path.exists(CLIENT_SECRETS_FILE):
                        print(f"   ⚠️ client_secrets.json not found")
                        return {'status': 'skipped', 'error': 'No credentials'}
                    
                    print("   🔐 Opening browser for authentication...")
                    free_port = find_free_port()
                    print(f"   Using port: {free_port}")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        CLIENT_SECRETS_FILE, SCOPES)
                    
                    try:
                        credentials = flow.run_local_server(port=free_port, open_browser=True)
                    except OSError:
                        print("   Retrying with automatic port selection...")
                        credentials = flow.run_local_server(open_browser=True)
                
                with open(TOKEN_FILE, 'wb') as f:
                    pickle.dump(credentials, f)
                print("   💾 Saved credentials for future use")
            
            youtube = build('youtube', 'v3', credentials=credentials)
            
            body = {
                'snippet': {
                    'title': video_title,
                    'description': video_description,
                    'tags': ['Dubai','creativedaily', 'trending', 'viral', 'fyp', 'explore', 'calendar','UAE','DubaiCreatives', target_date],
                    'categoryId': '22'
                },
                'status': {
                    'privacyStatus': 'public',
                    'selfDeclaredMadeForKids': False
                }
            }
            
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            
            print(f"   ⬆️ Uploading video to YouTube...")
            request = youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = request.execute()
            video_url = f"https://youtu.be/{response.get('id')}"
            
            print(f"   ✅ Uploaded successfully!")
            print(f"   📹 {video_url}")
            
            return {'status': 'success', 'video_url': video_url}
            
        except ImportError as e:
            print(f"   ⚠️ Missing library: {e}")
            return {'status': 'skipped', 'error': 'Missing libraries'}
        except Exception as e:
            error_msg = str(e)
            print(f"   ⚠️ Upload error: {error_msg[:200]}")
            return {'status': 'failed', 'error': error_msg}
    
    def process_date(self, target_date: str, post_to_youtube: bool = True, dpi: int = 150, video_duration: int = 5) -> dict:
        """Main method: Process a single date"""
        print("="*60)
        print("📅 CREATIVE DAILY - CALENDAR POSTER")
        print("="*60)
        print(f"Target Date: {target_date}")
        print(f"Output Dir: {self.output_dir}")
        print("="*60)
        
        # Step 1: Ensure image exists
        result = self.ensure_image_for_date(target_date, dpi)
        
        if result['status'] == 'not_found':
            print(f"\n❌ Date {target_date} not found in PDF")
            return {'status': 'not_found', 'date': target_date}
        
        print(f"\n✅ Image ready: {os.path.basename(result['image_path'])}")
        
        # Step 2: Get full page text (each line on its own)
        page_text = self.get_page_text_content(result['image_path'])
        print(f"   📝 Extracted {len(page_text)} characters of text")
        
        # Step 3: Convert PNG to MP4
        video_path = convert_png_to_mp4(result['image_path'], video_duration)
        
        if video_path is None:
            print(f"\n❌ Video conversion failed - cannot upload to YouTube")
            return {'status': 'conversion_failed', 'date': target_date}
        
        # Step 4: Upload to YouTube
        youtube_result = None
        if post_to_youtube:
            youtube_result = self.upload_to_youtube(video_path, target_date, page_text)
        
        return {
            'status': 'success',
            'date': target_date,
            'image_path': result['image_path'],
            'video_path': video_path,
            'page_num': result['page_num'],
            'youtube': youtube_result
        }


# ============= MAIN =============

if __name__ == "__main__":
    import sys
    
    PDF_PATH = "your_document.pdf"
    OUTPUT_DIR = "extracted_date_pages"
    
    target_date = None
    post_to_youtube = True
    
    for arg in sys.argv[1:]:
        if arg == "--no-youtube":
            post_to_youtube = False
        elif re.match(r'\d{4}-\d{2}-\d{2}', arg):
            target_date = arg
    
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"\n🎯 Processing: {target_date}")
    print(f"📹 YouTube posting: {'ON' if post_to_youtube else 'OFF'}")
    print(f"📝 Title: Creative Daily | {{date}} | Stupid Orange | Stupidest Broke Guy")
    print(f"🏷️ Hashtags: #creativedaily #trending #viral #viralvideo #trendingnow #explore #fyp\n")
    
    processor = CompleteCalendarExtractor(PDF_PATH, OUTPUT_DIR)
    result = processor.process_date(target_date, post_to_youtube)
    
    print("\n" + "="*60)
    print("📋 FINAL RESULT")
    print("="*60)
    
    if result['status'] == 'success':
        print(f"✅ SUCCESS!")
        print(f"   Date: {result['date']}")
        print(f"   Image: {result['image_path']}")
        print(f"   Video: {result.get('video_path', 'N/A')}")
        print(f"   Page: {result['page_num']}")
        
        if result.get('youtube'):
            if result['youtube']['status'] == 'success':
                print(f"\n📹 POSTED TO YOUTUBE!")
                print(f"   URL: {result['youtube']['video_url']}")
            elif result['youtube']['status'] == 'failed':
                print(f"\n❌ YouTube upload failed: {result['youtube'].get('error', 'Unknown')}")
            else:
                print(f"\n⚠️ YouTube skipped: {result['youtube'].get('error', 'Unknown')}")
        
        sys.exit(0)
    else:
        print(f"❌ FAILED: {result.get('error', 'Date not found')}")
        sys.exit(1)
