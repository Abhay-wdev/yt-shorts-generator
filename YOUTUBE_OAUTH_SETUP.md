# Official Google OAuth 2.0 & YouTube API Setup Guide

This application integrates directly with the official Google YouTube Data API v3 and YouTube Analytics API.

---

## 1. Google Cloud Console Configuration

To connect your YouTube channel and upload Shorts:

1. **Create or Select a Google Cloud Project**:
   - Navigate to [Google Cloud Console](https://console.cloud.google.com/).
   - Click **Select a Project** -> **New Project**, name it (e.g., `YT-Shorts-Automation`), and click **Create**.

2. **Enable Required APIs**:
   - Go to **APIs & Services** > **Library**.
   - Search for and enable:
     - **YouTube Data API v3**
     - **YouTube Analytics API**
     - **YouTube Reporting API** (optional, for batch historical reports)

3. **Configure OAuth Consent Screen**:
   - Navigate to **APIs & Services** > **OAuth consent screen**.
   - Choose **External** (or **Internal** if using Google Workspace).
   - Enter your App name (e.g. `AI Shorts Studio`), User support email, and Developer contact information.
   - Add Scopes:
     - `https://www.googleapis.com/auth/youtube.readonly` (Video discovery & channel details)
     - `https://www.googleapis.com/auth/youtube.upload` (Official video upload)
     - `https://www.googleapis.com/auth/youtube` (Video metadata update)
     - `https://www.googleapis.com/auth/yt-analytics.readonly` (Audience retention & analytics)
   - Add Test Users: Add the Google account email associated with your YouTube channel while your app is in "Testing" status.

4. **Create OAuth 2.0 Client Credentials**:
   - Go to **APIs & Services** > **Credentials**.
   - Click **Create Credentials** -> **OAuth client ID**.
   - Select Application type: **Web application**.
   - Set Name: `AI Shorts Generator Web Client`.
   - Authorized JavaScript origins:
     - `http://localhost:3000`
     - `http://127.0.0.1:3000`
   - Authorized redirect URIs:
     - `http://localhost:8000/api/v1/channels/oauth/callback`
     - `http://127.0.0.1:8000/api/v1/channels/oauth/callback`
   - Click **Create**.
   - Copy the **Client ID** and **Client Secret**.

5. **Environment Configuration**:
   - In `backend/.env`, set:
     ```env
     YOUTUBE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
     YOUTUBE_CLIENT_SECRET="your-client-secret"
     YOUTUBE_REDIRECT_URI="http://localhost:8000/api/v1/channels/oauth/callback"
     ```

---

## 2. API Quotas & Limitations

- **Daily Quota**: Google provides a free default quota of 10,000 units per project per day.
- **Cost per Operation**:
  - `videos.insert` (Upload): **1,600 units** (~6 uploads/day on the free tier).
  - `channels.list`: **1 unit**.
  - `videos.list`: **1 unit**.
  - `search.list`: **100 units**.
  - `thumbnails.set`: **50 units**.
- **Quota Conservation Strategy**:
  - Cache channel details and recent videos in SQLite.
  - Upload only quality-controlled clips in Safe or Auto mode.
  - Track estimated units consumed per day in the System Health dashboard.
