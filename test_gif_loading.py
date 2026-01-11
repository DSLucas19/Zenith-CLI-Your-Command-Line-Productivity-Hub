"""
Quick test to verify the GIF can be loaded and converted to ASCII
"""
import os
from PIL import Image

def test_gif_loading():
    gif_path = r"F:\App\Anti-gravity\CLI_TDL\ascii-animation.gif"
    
    print("=== Testing GIF Loading ===\n")
    print(f"GIF Path: {gif_path}")
    print(f"File exists: {os.path.exists(gif_path)}")
    
    if os.path.exists(gif_path):
        try:
            img = Image.open(gif_path)
            print(f"✓ GIF loaded successfully")
            print(f"  Format: {img.format}")
            print(f"  Size: {img.size}")
            print(f"  Frames: {getattr(img, 'n_frames', 1)}")
            
            # Test ASCII conversion on first frame
            img_resized = img.resize((30, 15), Image.Resampling.LANCZOS)
            img_rgb = img_resized.convert('RGB')
            
            ascii_chars = [' ', '.', ':', '-', '=', '+', '*', '#', '%', '@']
            
            print("\n=== First Frame ASCII Preview ===\n")
            for y in range(min(10, img_rgb.height)):
                line = ""
                for x in range(img_rgb.width):
                    r, g, b = img_rgb.getpixel((x, y))
                    brightness = int((r + g + b) / 3)
                    char_index = min(brightness // 26, len(ascii_chars) - 1)
                    line += ascii_chars[char_index]
                print(line)
            
            print("\n✅ GIF processing test PASSED!")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
    else:
        print("\n❌ GIF file not found!")

if __name__ == "__main__":
    test_gif_loading()
