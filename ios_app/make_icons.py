import os
import json
import subprocess

source_img = "/Users/slyeee/.gemini/antigravity/brain/95c778ae-abcf-4f02-9289-b961c0f33d2b/uploaded_image_1768993857551.png"
dest_dir = "/Users/slyeee/Desktop/vibe_coding/ios_app/Assets.xcassets/AppIcon.appiconset"

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

# Define standard iOS icon sizes (filename, size_pt, scale)
icons = [
    # iPhone Notifications (20pt)
    ("Icon-20@2x.png", 40),
    ("Icon-20@3x.png", 60),
    # iPhone Settings (29pt)
    ("Icon-29@2x.png", 58),
    ("Icon-29@3x.png", 87),
    # iPhone Spotlight (40pt)
    ("Icon-40@2x.png", 80),
    ("Icon-40@3x.png", 120),
    # iPhone App (60pt)
    ("Icon-60@2x.png", 120),
    ("Icon-60@3x.png", 180),
    # iPad Notifications (20pt) - usually shares iPhone files but for completeness
    ("Icon-20.png", 20),
    # iPad Settings (29pt)
    ("Icon-29.png", 29),
    # iPad Spotlight (40pt)
    ("Icon-40.png", 40),
    # iPad App (76pt)
    ("Icon-76.png", 76),
    ("Icon-76@2x.png", 152),
    # iPad Pro (83.5pt)
    ("Icon-83.5@2x.png", 167),
    # Marketing
    ("Icon-1024.png", 1024)
]

# Generate images using sips
for filename, size in icons:
    out_path = os.path.join(dest_dir, filename)
    print(f"Generating {filename} ({size}x{size})...")
    subprocess.run(["sips", "-z", str(size), str(size), source_img, "--out", out_path], check=False)

# Create Contents.json
contents = {
  "images" : [
    {"size" : "20x20", "idiom" : "iphone", "filename" : "Icon-20@2x.png", "scale" : "2x"},
    {"size" : "20x20", "idiom" : "iphone", "filename" : "Icon-20@3x.png", "scale" : "3x"},
    {"size" : "29x29", "idiom" : "iphone", "filename" : "Icon-29@2x.png", "scale" : "2x"},
    {"size" : "29x29", "idiom" : "iphone", "filename" : "Icon-29@3x.png", "scale" : "3x"},
    {"size" : "40x40", "idiom" : "iphone", "filename" : "Icon-40@2x.png", "scale" : "2x"},
    {"size" : "40x40", "idiom" : "iphone", "filename" : "Icon-40@3x.png", "scale" : "3x"},
    {"size" : "60x60", "idiom" : "iphone", "filename" : "Icon-60@2x.png", "scale" : "2x"},
    {"size" : "60x60", "idiom" : "iphone", "filename" : "Icon-60@3x.png", "scale" : "3x"},
    {"size" : "20x20", "idiom" : "ipad", "filename" : "Icon-20.png", "scale" : "1x"},
    {"size" : "20x20", "idiom" : "ipad", "filename" : "Icon-20@2x.png", "scale" : "2x"},
    {"size" : "29x29", "idiom" : "ipad", "filename" : "Icon-29.png", "scale" : "1x"},
    {"size" : "29x29", "idiom" : "ipad", "filename" : "Icon-29@2x.png", "scale" : "2x"},
    {"size" : "40x40", "idiom" : "ipad", "filename" : "Icon-40.png", "scale" : "1x"},
    {"size" : "40x40", "idiom" : "ipad", "filename" : "Icon-40@2x.png", "scale" : "2x"},
    {"size" : "76x76", "idiom" : "ipad", "filename" : "Icon-76.png", "scale" : "1x"},
    {"size" : "76x76", "idiom" : "ipad", "filename" : "Icon-76@2x.png", "scale" : "2x"},
    {"size" : "83.5x83.5", "idiom" : "ipad", "filename" : "Icon-83.5@2x.png", "scale" : "2x"},
    {"size" : "1024x1024", "idiom" : "ios-marketing", "filename" : "Icon-1024.png", "scale" : "1x"}
  ],
  "info" : {
    "version" : 1,
    "author" : "xcode"
  }
}

with open(os.path.join(dest_dir, "Contents.json"), "w") as f:
    json.dump(contents, f, indent=2)

print("AppIcon generation complete.")
