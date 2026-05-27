def create_sliding_animation_video(image_path: str, text_content: str,
                                    output_path: str = None,
                                    bg_color: tuple = (255, 215, 0),
                                    text_color: str = "white",
                                    slide_duration: int = 18) -> str:
    """
    Create video with image sliding up and text scrolling
    Image fits within screen (no stretching) - black bars on sides
    """
    
    if output_path is None:
        output_path = image_path.replace('.png', '_video.mp4')
    
    print(f"\n🎬 Creating sliding animation video...")
    print(f"   Image: {os.path.basename(image_path)}")
    print(f"   Duration: {slide_duration} seconds")
    
    # Import moviepy
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
    
    # WIDER SCREEN - 16:9 Landscape
    screen_width, screen_height = 1920, 1080
    
    try:
        from PIL import Image
        
        pil_img = Image.open(image_path)
        img_width, img_height = pil_img.size
        
        # Calculate zoom to fill screen width while maintaining aspect ratio
        # We want the image to fit within the screen with black bars on sides if needed
        # Or slightly zoomed but not stretched
        
        # Option 1: Fit to screen height (image fills height, may have black bars on sides)
        scale = screen_height / img_height
        new_width = int(img_width * scale)
        new_height = screen_height
        
        # If width is less than screen, we'll have black bars on sides (GOOD - no stretching)
        # If width is greater, we need to scale down to fit
        if new_width > screen_width:
            # Image is too wide - scale to fit width instead
            scale = screen_width / img_width
            new_width = screen_width
            new_height = int(img_height * scale)
        
        print(f"   Original image: {img_width}x{img_height}")
        print(f"   Resized to: {new_width}x{new_height}")
        print(f"   Screen: {screen_width}x{screen_height}")
        
        # Resize image with high quality
        try:
            pil_img_resized = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        except AttributeError:
            try:
                pil_img_resized = pil_img.resize((new_width, new_height), Image.LANCZOS)
            except:
                pil_img_resized = pil_img.resize((new_width, new_height))
        
        temp_img_path = image_path.replace('.png', '_temp_resized.png')
        pil_img_resized.save(temp_img_path)
        
        # Image clip with slide animation
        image_clip = ImageClip(temp_img_path, duration=slide_duration)
        
        # Start position: image centered, starting below screen
        start_y = screen_height
        # End position: image centered, scrolled up
        end_y = -new_height + screen_height * 0.15
        
        def image_slide_position(t):
            progress = min(1.0, t / slide_duration)
            # Ease in-out for smoother motion
            eased = progress * progress * (3 - 2 * progress)
            y = start_y + (end_y - start_y) * eased
            return ('center', y)
        
        image_clip = image_clip.with_position(image_slide_position)
        
        # Dark background (black bars on sides) - more professional look
        # Using dark gray/black so the image pops
        background = ColorClip(size=(screen_width, screen_height),
                                color=(0, 0, 0),  # Black background
                                duration=slide_duration)
        
        # Add a subtle yellow glow behind the image (optional)
        # Creates a nice framing effect
        glow_size = 20
        glow_color = (255, 215, 0)  # Yellow
        glow_clip = ColorClip(size=(new_width + glow_size*2, new_height + glow_size*2),
                               color=glow_color,
                               duration=slide_duration)
        glow_clip = glow_clip.with_position(('center', 'center'))
        
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
                print(f"   Using font: {font if font else 'default'} with stroke")
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
        
        # Slower, smoother scroll
        text_height = text_clip.size[1]
        text_start_y = screen_height
        text_end_y = -text_height - 50
        
        def text_scroll_position(t):
            progress = min(1.0, t / slide_duration)
            # Smooth easing
            eased = progress * progress * (3 - 2 * progress)
            y = text_start_y + (text_end_y - text_start_y) * eased
            return ('center', y)
        
        text_clip = text_clip.with_position(text_scroll_position)
        
        # Composite all layers (background, glow, image, text)
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
