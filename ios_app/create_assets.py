import os
import json
import shutil

base_dir = "/Users/slyeee/Desktop/vibe_coding/ios_app"
assets_dir = os.path.join(base_dir, "Assets")
xcassets_dir = os.path.join(base_dir, "Assets.xcassets")

# images to process
images = ["mood_angry", "mood_sad", "mood_soso", "mood_calm", "mood_happy"]

# 1. Create .xcassets directory
if not os.path.exists(xcassets_dir):
    os.makedirs(xcassets_dir)

# 2. Create root Contents.json
root_contents = {
    "info": {
        "author": "xcode",
        "version": 1
    }
}
with open(os.path.join(xcassets_dir, "Contents.json"), "w") as f:
    json.dump(root_contents, f, indent=2)

# 3. Process each image
for name in images:
    # Source image path
    src_img = os.path.join(assets_dir, f"{name}.png")
    
    if not os.path.exists(src_img):
        print(f"Warning: {src_img} not found")
        continue
        
    # Create imageset directory
    imageset_dir = os.path.join(xcassets_dir, f"{name}.imageset")
    if not os.path.exists(imageset_dir):
        os.makedirs(imageset_dir)
        
    # Copy file to imageset
    dst_img = os.path.join(imageset_dir, f"{name}.png")
    shutil.copy2(src_img, dst_img)
    
    # Create imageset Contents.json
    item_contents = {
        "images": [
            {
                "filename": f"{name}.png",
                "idiom": "universal",
                "scale": "1x"
            },
            {
                "idiom": "universal",
                "scale": "2x"
            },
            {
                "idiom": "universal",
                "scale": "3x"
            }
        ],
        "info": {
            "author": "xcode",
            "version": 1
        }
    }
    
    with open(os.path.join(imageset_dir, "Contents.json"), "w") as f:
        json.dump(item_contents, f, indent=2)

print("Assets.xcassets structure created successfully.")
