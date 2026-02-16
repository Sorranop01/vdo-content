# 🔐 Google Cloud Service Account Setup Guide

## Why Service Account?

To use **Gemini 2.5 TTS** (AI Studio quality voices), you need a Google Cloud service account. This gives you access to:
- `gemini-2.5-flash-tts` - Low latency, natural voices
- `gemini-2.5-pro-tts` - Highest quality for podcasts/audiobooks
- 30+ natural voices (Zephyr, Orbit, Leda, Kore, etc.)

## Prerequisites

- Google account
- ~10-15 minutes

## Step-by-Step Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Enter project name (e.g., `vdo-content-tts`)
4. Click **"Create"**
5. Wait for project creation (~30 seconds)

### 2. Enable Cloud Text-to-Speech API

1. In Cloud Console, go to **"APIs & Services"** → **"Library"**
2. Search for **"Cloud Text-to-Speech API"**
3. Click on it → Click **"Enable"**
4. Wait for API to enable (~1 minute)

### 3. Create Service Account

1. Go to **"IAM & Admin"** → **"Service Accounts"**
2. Click **"Create Service Account"**
3. Enter details:
   - **Name:** `vdo-tts-service`
   - **Description:** `TTS service account for VDO Content`
4. Click **"Create and Continue"**
5. **Grant role:** Select **"Cloud Text-to-Speech User"**
6. Click **"Continue"** → **"Done"**

### 4. Create JSON Key

1. Find your newly created service account in the list
2. Click on it → Go to **"Keys"** tab
3. Click **"Add Key"** → **"Create new key"**
4. Select **"JSON"** format
5. Click **"Create"**
6. A JSON file will download automatically
7. **IMPORTANT:** Keep this file secure! Don't commit to Git!

### 5. Configure VDO Content

1. Move the downloaded JSON file to a secure location:
   ```bash
   mkdir -p ~/credentials
   mv ~/Downloads/vdo-content-tts-*.json ~/credentials/google-tts-service-account.json
   chmod 600 ~/credentials/google-tts-service-account.json
   ```

2. Update `.env` file:
   ```env
   # Gemini TTS Mode (Advanced)
   GOOGLE_APPLICATION_CREDENTIALS=/home/agent/credentials/google-tts-service-account.json
   GCP_PROJECT_ID=vdo-content-tts
   ```

3. Restart the app:
   ```bash
   # Stop current Streamlit
   pkill -f "streamlit run"
   
   # Start again
   .venv/bin/streamlit run app.py --server.port 8503
   ```

4. Verify mode:
   - You should see: **"✅ Mode: Gemini TTS (AI Studio quality)"** in logs
   - UI will show **"🌟 Mode: Gemini TTS"**

## Troubleshooting

### Error: "google-cloud-texttospeech not installed"
```bash
.venv/bin/pip install google-cloud-texttospeech>=2.14.0
```

### Error: "Could not automatically determine credentials"
- Check `GOOGLE_APPLICATION_CREDENTIALS` path is correct
- Ensure JSON file exists and is readable
- Verify file permissions: `chmod 600 <json-file>`

### Error: "Permission denied"
- Ensure service account has "Cloud Text-to-Speech User" role
- Check API is enabled in Cloud Console

### Still using Neural2 mode?
- Check logs for error messages
- Verify all environment variables are set correctly
- Restart Streamlit app

## Cost Information

- **Free tier:** 1 million characters/month
- **After free tier:** ~$4 USD per 1 million characters
- **Typical usage:** A 500-word script ≈ 3,000 characters = $0.012 USD

For most users, the free tier is more than enough!

## Security Best Practices

1. ✅ **Never commit service account JSON to Git**
2. ✅ **Add to `.gitignore`:**
   ```
   *service-account*.json
   credentials/
   ```
3. ✅ **Use restrictive permissions:** `chmod 600`
4. ✅ **Rotate keys periodically** (every 90 days)
5. ✅ **Delete unused service accounts**

## Next Steps

Once configured, you'll have access to:
- 🎤 Natural Gemini voices
- 🌏 24+ languages
- 🎨 Voice customization (style prompts)
- ⚡ Low-latency generation

Test it by generating a voice in the app and comparing quality!
