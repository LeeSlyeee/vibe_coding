import os
import json

base_dir = "/Users/slyeee/Desktop/vibe_coding/ios_app/Assets.xcassets"
appicon_dir = os.path.join(base_dir, "AppIcon.appiconset")

# 1. Create AppIcon.appiconset directory
if not os.path.exists(appicon_dir):
    os.makedirs(appicon_dir)

# 2. Create Contents.json for AppIcon
# Standard empty AppIcon template to satisfy Xcode
contents = {
  "images" : [
    {
      "idiom" : "iphone",
      "scale" : "2x",
      "size" : "20x20"
    },
    {
      "idiom" : "iphone",
      "scale" : "3x",
      "size" : "20x20"
    },
    {
      "idiom" : "iphone",
      "scale" : "2x",
      "size" : "29x29"
    },
    {
      "idiom" : "iphone",
      "scale" : "3x",
      "size" : "29x29"
    },
    {
      "idiom" : "iphone",
      "scale" : "2x",
      "size" : "38x38"
    },
    {
      "idiom" : "iphone",
      "scale" : "3x",
      "size" : "38x38"
    },
    {
      "idiom" : "iphone",
      "scale" : "2x",
      "size" : "40x40"
    },
    {
      "idiom" : "iphone",
      "scale" : "3x",
      "size" : "40x40"
    },
    {
      "idiom" : "iphone",
      "scale" : "2x",
      "size" : "60x60"
    },
    {
      "idiom" : "iphone",
      "scale" : "3x",
      "size" : "60x60"
    },
    {
      "idiom" : "iphone",
      "scale" : "2x",
      "size" : "64x64"
    },
    {
      "idiom" : "iphone",
      "scale" : "3x",
      "size" : "64x64"
    },
    {
      "idiom" : "iphone",
      "scale" : "2x",
      "size" : "68x68"
    },
    {
      "idiom" : "iphone",
      "scale" : "2x",
      "size" : "76x76"
    },
    {
      "idiom" : "iphone",
      "scale" : "2x",
      "size" : "83.5x83.5"
    },
    {
      "idiom" : "iphone",
      "scale" : "2x",
      "size" : "1024x1024"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  }
}

with open(os.path.join(appicon_dir, "Contents.json"), "w") as f:
    json.dump(contents, f, indent=2)

print("AppIcon placeholder created.")
