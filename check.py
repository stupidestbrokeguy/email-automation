def extract_thumbnail_from_video(video_path: str, output_path: str = None, time_seconds: float = 0.0) -> str:
    """
    Extract thumbnail from video - capturing the TOP 25% of the image visible at T=0
    and making it fill the entire thumbnail canvas (no yellow background)
    
    At T=0, the PNG is positioned at the bottom of the screen. The visible part
    is the top portion of the PNG. This function extracts just that visible part
    and resizes it to fill the thumbnail completely.
    
    Args:
        video_path: Path to video file
        output_path: Where to save thumbnail (auto-generated if None)
        time_seconds: Time in seconds to capture frame (default 0.0)
    
    Returns:
        Path to saved thumbnail image
    """
    print(f"\n🎬 DEBUG: extract_thumbnail_from_video START (Top 25% cropping mode)")
    print(f"   📹 Video: {video_path}")
    print(f"   ⏱️  Time: {time_seconds} seconds")
    
    if output_path is None:
        output_path = video_path.replace('.mp4', '_thumbnail.png')
    
    # Target thumbnail dimensions (YouTube standard)
    THUMBNAIL_WIDTH = 1280
    THUMBNAIL_HEIGHT = 720
    
    try:
        # Try using moviepy first
        from moviepy import VideoFileClip
        print(f"   ✅ Using moviepy for thumbnail extraction")
        
        clip = VideoFileClip(video_path)
        frame = clip.get_frame(time_seconds)
        clip.close()
        
        from PIL import Image
        import numpy as np
        
        # Convert frame to PIL Image
        img = Image.fromarray(frame.astype('uint8'), 'RGB')
        
        print(f"   📸 Original frame size: {img.size}")
        
        # At T=0, the PNG is positioned starting from bottom
        # The visible part is the top portion of the PNG
        # We need to find where the PNG content starts and ends
        
        # Convert to numpy array for analysis
        img_array = np.array(img)
        
        # Define yellow background color range (with some tolerance)
        yellow_lower = np.array([240, 200, 0])   # Lower bound for yellow
        yellow_upper = np.array([255, 230, 50])  # Upper bound for yellow
        
        # Find non-yellow pixels (these are the PNG image content)
        is_not_yellow = np.any((img_array < yellow_lower) | (img_array > yellow_upper), axis=2)
        
        # Find bounding box of non-yellow pixels (the PNG area)
        non_yellow_coords = np.argwhere(is_not_yellow)
        
        if len(non_yellow_coords) > 0:
            y_min = non_yellow_coords[:, 0].min()
            y_max = non_yellow_coords[:, 0].max()
            x_min = non_yellow_coords[:, 1].min()
            x_max = non_yellow_coords[:, 1].max()
            
            png_height = y_max - y_min
            png_width = x_max - x_min
            
            print(f"   📐 PNG bounding box: y={y_min}-{y_max}, x={x_min}-{x_max}")
            print(f"   📏 PNG dimensions: {png_width}x{png_height}")
            
            # The visible part at T=0 is the TOP 25% of the PNG
            # Since the PNG is positioned starting at bottom, 
            # the visible top portion = from y_min to y_min + (png_height * 0.25)
            top_visible_height = int(png_height * 0.25)
            crop_y_min = y_min
            crop_y_max = y_min + top_visible_height
            
            print(f"   ✂️ Cropping top 25% of PNG: y={crop_y_min} to {crop_y_max}")
            
            # Crop to just the top 25% of the PNG
            cropped_img = img.crop((x_min, crop_y_min, x_max, crop_y_max))
            print(f"   📐 Cropped size: {cropped_img.size}")
            
            # Now resize to fill the entire thumbnail canvas (1280x720)
            # This maintains aspect ratio and fills the whole area
            target_ratio = THUMBNAIL_WIDTH / THUMBNAIL_HEIGHT
            cropped_ratio = cropped_img.width / cropped_img.height
            
            if cropped_ratio > target_ratio:
                # Crop is wider than target - resize to match height, then crop width
                new_height = THUMBNAIL_HEIGHT
                new_width = int(cropped_img.width * (THUMBNAIL_HEIGHT / cropped_img.height))
                resized_img = cropped_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                # Crop to target width
                left = (new_width - THUMBNAIL_WIDTH) // 2
                right = left + THUMBNAIL_WIDTH
                final_img = resized_img.crop((left, 0, right, THUMBNAIL_HEIGHT))
            else:
                # Crop is taller than target - resize to match width, then crop height
                new_width = THUMBNAIL_WIDTH
                new_height = int(cropped_img.height * (THUMBNAIL_WIDTH / cropped_img.width))
                resized_img = cropped_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                # Crop to target height
                top = (new_height - THUMBNAIL_HEIGHT) // 2
                bottom = top + THUMBNAIL_HEIGHT
                final_img = resized_img.crop((0, top, THUMBNAIL_WIDTH, bottom))
            
            print(f"   🖼️ Final thumbnail size: {final_img.size}")
            final_img.save(output_path, quality=90)
            
        else:
            # Fallback: If no PNG detected, take top 25% of entire frame
            print(f"   ⚠️ Could not detect PNG area, cropping top 25% of full frame")
            height = img.height
            crop_height = int(height * 0.25)
            cropped_img = img.crop((0, 0, img.width, crop_height))
            
            # Resize to fill thumbnail
            final_img = cropped_img.resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)
            final_img.save(output_path, quality=90)
        
        print(f"   ✅ Thumbnail saved: {output_path} ({os.path.getsize(output_path)} bytes)")
        
    except ImportError:
        try:
            # Fallback to OpenCV
            import cv2
            print(f"   ✅ Using OpenCV for thumbnail extraction")
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception("Cannot open video")
            
            # Set frame position
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_num = int(time_seconds * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            
            ret, frame = cap.read()
            if ret:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                
                # Same cropping logic as above
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
                    
                    # Resize to fill thumbnail
                    final_img = cropped_img.resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)
                    final_img.save(output_path, quality=90)
                else:
                    # Fallback: crop top 25% of full frame
                    height = img.height
                    crop_height = int(height * 0.25)
                    cropped_img = img.crop((0, 0, img.width, crop_height))
                    final_img = cropped_img.resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)
                    final_img.save(output_path, quality=90)
                
                print(f"   ✅ Thumbnail saved: {output_path}")
            else:
                raise Exception("Cannot read frame")
            
            cap.release()
            
        except ImportError:
            # Fallback to ffmpeg
            print(f"   ✅ Using ffmpeg for thumbnail extraction")
            import subprocess
            
            temp_frame = output_path.replace('.png', '_temp_frame.png')
            cmd_extract = [
                'ffmpeg', '-y',
                '-ss', str(time_seconds),
                '-i', video_path,
                '-vframes', '1',
                '-q:v', '2',
                temp_frame
            ]
            
            result = subprocess.run(cmd_extract, capture_output=True, text=True)
            if result.returncode == 0:
                from PIL import Image
                import numpy as np
                
                img = Image.open(temp_frame)
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
                    
                    # Resize to fill thumbnail
                    final_img = cropped_img.resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)
                    final_img.save(output_path, quality=90)
                else:
                    height = img.height
                    crop_height = int(height * 0.25)
                    cropped_img = img.crop((0, 0, img.width, crop_height))
                    final_img = cropped_img.resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)
                    final_img.save(output_path, quality=90)
                
                if os.path.exists(temp_frame):
                    os.remove(temp_frame)
                
                print(f"   ✅ Thumbnail saved: {output_path}")
            else:
                raise Exception(f"ffmpeg error: {result.stderr}")
    
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path) / 1024
        print(f"   📁 Thumbnail size: {file_size:.1f} KB")
        print(f"🎬 DEBUG: extract_thumbnail_from_video COMPLETE")
        return output_path
    else:
        print(f"   ❌ Failed to extract thumbnail")
        return None
