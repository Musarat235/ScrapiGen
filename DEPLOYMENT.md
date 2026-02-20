# ScrapiGen Deployment Guide

This guide will help you deploy the **ScrapiGen** backend to **Railway** and the frontend to **Streamlit Community Cloud**.

## Prerequisites
- A GitHub account.
- A [Railway](https://railway.app/) account (GitHub login recommended).
- A [Streamlit Community Cloud](https://streamlit.io/cloud) account.

## Part 1: Backend Deployment (Railway)
We recommend Railway because it handles the complex system dependencies required by Playwright (browsers) automatically when using the Dockerfile we created.

1. **Push your code to GitHub**
   - Ensure your project is in a GitHub repository.

2. **Create a New Service on Railway**
   - Go to your Railway Dashboard.
   - Click **+ New Project** > **Deploy from GitHub repo**.
   - Select your **ScrapiGen** repository.

3. **Configure the Service**
   - Railway should automatically detect the `Dockerfile`.
   - Go to the **Variables** tab for your service.
   - Add any environment variables from your `.env` file (e.g., `GROQ_API_KEY`, etc.).

4. **Generate a Domain**
   - Go to the **Settings** tab.
   - Under **Networking**, click **Generate Domain** (or add a custom one).
   - **Copy this URL** (e.g., `https://scrapigen-production.up.railway.app`). You will need it for the frontend.

## Part 2: Frontend Deployment (Streamlit)

1. **Deploy app on Streamlit Cloud**
   - Log in to [share.streamlit.io](https://share.streamlit.io/).
   - Click **New app**.
   - Select your repository, branch, and the main file path: `frontend/streamlit_app/app.py`.

2. **Configure Environment Variables**
   - Before clicking "Deploy" (or in the app settings after deploying), go to **Advanced Settings**.
   - Add a new secret/environment variable:
     - Key: `API_URL`
     - Value: The Railway URL you copied in Part 1 (e.g., `https://scrapigen-production.up.railway.app`) **without** a trailing slash.
   - Click **Save**.

3. **Launch**
   - Click **Deploy**.
   - Your frontend should now be live and connected to your backend!

## Troubleshooting
- **Backend Crashes?** Check Railway logs. If Playwright complains about missing browsers, the `Dockerfile` steps usually fix this.
- **Frontend can't connect?** Ensure `API_URL` does NOT handle a trailing slash if the app logic appends paths like `/scrape`.
