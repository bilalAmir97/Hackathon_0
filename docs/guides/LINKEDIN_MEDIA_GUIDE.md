# LinkedIn Media Support - Complete Guide

**Feature:** Post images and videos to LinkedIn via Official API

---

## Supported Media Types

### Images
- **Formats:** JPG, JPEG, PNG
- **Max Size:** 10 MB per image
- **Max Count:** 1 image per post (LinkedIn API limitation)

### Videos
- **Format:** MP4
- **Max Size:** 200 MB
- **Max Duration:** 10 minutes
- **Max Count:** 1 video per post
- **Processing:** Videos take 1-5 minutes to process on LinkedIn's servers

---

## How to Use

### 1. Create Post with Image

**File:** `AI_Employee_Vault/Pending_LinkedIn/POST_with_image.md`

```markdown
---
type: linkedin_post
status: pending
media: images/my_screenshot.png
---

## Content
🚀 Check out this screenshot!

Your post content here...

#AI #Automation
```

**Steps:**
1. Place your image in `AI_Employee_Vault/images/my_screenshot.png`
2. Create post file with `media: images/my_screenshot.png` in frontmatter
3. Move to `Approved_LinkedIn/` folder
4. Post will be published automatically with image

---

### 2. Create Post with Video

**File:** `AI_Employee_Vault/Pending_LinkedIn/POST_with_video.md`

```markdown
---
type: linkedin_post
status: pending
media: videos/demo.mp4
---

## Content
🎬 Watch this demo!

Your post content here...

#VideoDemo #AI
```

**Steps:**
1. Place your video in `AI_Employee_Vault/videos/demo.mp4`
2. Create post file with `media: videos/demo.mp4` in frontmatter
3. Move to `Approved_LinkedIn/` folder
4. Post will be published automatically with video
5. Wait 1-5 minutes for LinkedIn to process the video

---

## Media Path Options

### Relative Paths (Recommended)
```yaml
media: images/screenshot.png
media: videos/demo.mp4
```
Paths are relative to `AI_Employee_Vault/`

### Absolute Paths
```yaml
media: /full/path/to/image.jpg
media: /mnt/d/Bilal/videos/demo.mp4
```

---

## File Size Limits

### Check File Size
```bash
# Check image size
ls -lh AI_Employee_Vault/images/screenshot.png

# Check video size
ls -lh AI_Employee_Vault/videos/demo.mp4
```

### Compress if Needed

**Images (reduce to under 10MB):**
```bash
# Using ImageMagick
convert input.png -quality 85 -resize 1920x1080 output.png

# Using Python PIL
python -c "from PIL import Image; img=Image.open('input.png'); img.save('output.jpg', quality=85, optimize=True)"
```

**Videos (reduce to under 200MB):**
```bash
# Using ffmpeg
ffmpeg -i input.mp4 -vcodec h264 -acodec aac -b:v 2M output.mp4
```

---

## Validation

The system automatically validates:
- ✅ File exists
- ✅ File type is supported (jpg, png, mp4)
- ✅ File size is within limits
- ✅ File is readable

If validation fails, an alert is created in `Needs_Action/`

---

## Example: Screenshot of PM2 Dashboard

```bash
# 1. Take screenshot
pm2 monit
# (Take screenshot, save as pm2_dashboard.png)

# 2. Move to vault
mv pm2_dashboard.png AI_Employee_Vault/images/

# 3. Create post
cat > AI_Employee_Vault/Pending_LinkedIn/POST_pm2_dashboard.md << 'EOF'
---
type: linkedin_post
status: pending
media: images/pm2_dashboard.png
---

## Content
📊 My AI Employee running 24/7!

This is what autonomous operation looks like:
- 3 services online
- 17+ hours uptime
- 0 crashes
- 80.6 MB memory

All managed by PM2, running continuously without human intervention.

#AI #Automation #PM2 #DevOps
EOF

# 4. Approve and post
mv AI_Employee_Vault/Pending_LinkedIn/POST_pm2_dashboard.md \
   AI_Employee_Vault/Approved_LinkedIn/

# 5. Post immediately (or wait 5 minutes)
uv run python watchers/linkedin_api_poster.py
```

---

## Example: Demo Video

```bash
# 1. Record demo video (30-60 seconds)
# Show: pm2 status, pm2 logs, posting to LinkedIn

# 2. Move to vault
mv demo.mp4 AI_Employee_Vault/videos/

# 3. Create post
cat > AI_Employee_Vault/Pending_LinkedIn/POST_demo_video.md << 'EOF'
---
type: linkedin_post
status: pending
media: videos/demo.mp4
---

## Content
🎬 60-second demo of my AI Employee!

Watch it:
- Monitor Gmail & WhatsApp
- Post to LinkedIn automatically
- Run health checks
- Generate daily briefings

All autonomous. All 24/7. Zero human intervention.

#AI #Automation #Demo #TechInnovation
EOF

# 4. Approve and post
mv AI_Employee_Vault/Pending_LinkedIn/POST_demo_video.md \
   AI_Employee_Vault/Approved_LinkedIn/

# 5. Post immediately
uv run python watchers/linkedin_api_poster.py

# 6. Wait for LinkedIn to process video (1-5 minutes)
```

---

## Troubleshooting

### "File not found"
```bash
# Check file exists
ls -lh AI_Employee_Vault/images/screenshot.png

# Check path in frontmatter matches actual file location
```

### "Image too large"
```bash
# Check size
ls -lh AI_Employee_Vault/images/screenshot.png

# If over 10MB, compress:
convert screenshot.png -quality 85 -resize 1920x1080 screenshot_compressed.png
```

### "Video too large"
```bash
# Check size
ls -lh AI_Employee_Vault/videos/demo.mp4

# If over 200MB, compress:
ffmpeg -i demo.mp4 -vcodec h264 -b:v 2M demo_compressed.mp4
```

### "Unsupported file type"
```bash
# Convert to supported format
# For images: convert to PNG or JPG
convert image.gif image.png

# For videos: convert to MP4
ffmpeg -i video.avi video.mp4
```

### "Media upload failed"
- Check LinkedIn API token is valid
- Re-authenticate: `uv run python watchers/linkedin_api_poster.py --authenticate`
- Check internet connection
- Check LinkedIn API status

### "Video not showing on LinkedIn"
- Videos take 1-5 minutes to process
- Check LinkedIn post - video may still be processing
- If processing fails, LinkedIn will show error
- Try re-uploading with smaller file size

---

## Best Practices

### Images
1. **Resolution:** 1200x627 pixels (optimal for LinkedIn)
2. **Format:** PNG for screenshots, JPG for photos
3. **Size:** Keep under 5MB for faster upload
4. **Content:** Clear, readable text; professional appearance

### Videos
1. **Duration:** 30-90 seconds (optimal engagement)
2. **Resolution:** 1080p (1920x1080)
3. **Format:** MP4 with H.264 codec
4. **Size:** Keep under 50MB for faster upload
5. **Content:** Add captions (LinkedIn auto-generates)

### Post Content
1. **Hook:** First line should grab attention
2. **Context:** Explain what the media shows
3. **Value:** What can viewers learn?
4. **CTA:** Ask a question or invite discussion
5. **Hashtags:** 3-5 relevant hashtags

---

## Limitations

### LinkedIn API Limitations
- ❌ Cannot post multiple images (carousel) via API
- ❌ Cannot post documents (PDF) via API
- ❌ Cannot edit posts after publishing
- ❌ Cannot schedule posts for future time
- ✅ Can post single image
- ✅ Can post single video
- ✅ Can post text-only

### Workarounds
- **Multiple images:** Create collage image
- **Documents:** Convert to image or link to external PDF
- **Scheduling:** Use cron to move files at specific time

---

## Performance

### Upload Times
- **Image (1-5MB):** 2-5 seconds
- **Video (50MB):** 10-30 seconds
- **Video (200MB):** 30-60 seconds

### Processing Times
- **Image:** Instant (ready immediately)
- **Video:** 1-5 minutes (LinkedIn processing)

---

## Security

### Media Privacy
- All media uploaded to LinkedIn is public
- Do not include sensitive information
- Review screenshots for PII, credentials, tokens
- Blur sensitive areas if needed

### File Permissions
```bash
# Ensure media files are readable
chmod 644 AI_Employee_Vault/images/*.png
chmod 644 AI_Employee_Vault/videos/*.mp4
```

---

## Testing

### Test Image Upload
```bash
# Create test image
convert -size 800x600 xc:blue -pointsize 72 -fill white \
  -annotate +100+300 "Test Image" test.png

# Move to vault
mv test.png AI_Employee_Vault/images/

# Create test post
cat > AI_Employee_Vault/Approved_LinkedIn/TEST_image.md << 'EOF'
---
type: linkedin_post
status: pending
media: images/test.png
---

## Content
🧪 Testing image upload feature!

This is a test post to verify image upload works correctly.

#Test
EOF

# Post
uv run python watchers/linkedin_api_poster.py
```

### Test Video Upload
```bash
# Create test video (5 seconds, blue screen)
ffmpeg -f lavfi -i color=blue:s=1280x720:d=5 -vcodec libx264 test.mp4

# Move to vault
mv test.mp4 AI_Employee_Vault/videos/

# Create test post
cat > AI_Employee_Vault/Approved_LinkedIn/TEST_video.md << 'EOF'
---
type: linkedin_post
status: pending
media: videos/test.mp4
---

## Content
🎬 Testing video upload feature!

This is a test post to verify video upload works correctly.

#Test
EOF

# Post
uv run python watchers/linkedin_api_poster.py
```

---

## Next Steps

1. Create `images/` and `videos/` directories
2. Take screenshots of your AI Employee
3. Record demo video
4. Create posts with media
5. Test with small files first
6. Monitor logs for any issues

---

**Created:** 2026-02-27
**Feature:** LinkedIn Media Support
**Status:** Production-ready
**Supported:** Images (JPG, PNG) + Videos (MP4)
