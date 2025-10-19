# Deploy Telegram Bot to Google Cloud Run

## Method 1: Using Google Cloud Console (Web UI) - RECOMMENDED

### Step 1: Create Project and Enable Billing

1. Go to https://console.cloud.google.com
2. Click "Select a project" → "New Project"
3. Enter project name: "Telegram Bot" (note the auto-generated Project ID)
4. Click "Create"
5. Go to "Billing" (hamburger menu) → Link a billing account
6. Enable APIs:

   - Search for "Cloud Run API" → Enable
   - Search for "Artifact Registry API" → Enable
   - Search for "Secret Manager API" → Enable

### Step 2: Store Your Secrets

1. Go to "Secret Manager" in the navigation menu
2. Click "Create Secret"

   - **Name**: `telegram-bot-token`
   - **Secret value**: Your actual Telegram bot token
   - Click "Create Secret"

3. Repeat for:

   - **Name**: `openai-api-key` (with your OpenAI API key)
   - **Name**: `user-chat-id` (with your Telegram chat ID)

### Step 2.5: Grant Secret Access Permissions

**IMPORTANT**: After creating secrets, you must grant Cloud Run permission to access them:

1. Go to "IAM & Admin" → "IAM" in the navigation menu
2. Find the service account: `YOUR-PROJECT-NUMBER-compute@developer.gserviceaccount.com` (or similar)
3. Click the pencil icon to edit
4. Click "ADD ANOTHER ROLE"
5. Add these roles:
   - `Secret Manager Secret Accessor` (roles/secretmanager.secretAccessor)
6. Click "Save"

**Alternative method using gcloud CLI:**
```bash
# Replace YOUR-PROJECT-ID and YOUR-PROJECT-NUMBER with your actual values
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
    --member="serviceAccount:YOUR-PROJECT-NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Step 3: Build and Push Docker Image

**You'll need Docker installed locally and gcloud CLI for this step:**

```bash
# Install gcloud CLI: https://cloud.google.com/sdk/docs/install
gcloud auth login
gcloud config set project YOUR-PROJECT-ID
gcloud auth configure-docker

# Build and push (run from your project directory)
docker build -t gcr.io/YOUR-PROJECT-ID/telegram-bot:latest .
docker push gcr.io/YOUR-PROJECT-ID/telegram-bot:latest
```

### Step 4: Deploy to Cloud Run (Console)

1. Go to "Cloud Run" in the navigation menu
2. Click "Create Service"
3. Select "Deploy one revision from an existing container image"
4. Click "Select" → Choose your image: `gcr.io/YOUR-PROJECT-ID/telegram-bot:latest`
5. **Service name**: `telegram-bot`
6. **Region**: `us-central1` (or any US region for best pricing)
7. **Authentication**: Allow unauthenticated invocations
8. Click "Container, Networking, Security" to expand:

   - **Container tab**:
     - Memory: 256 MiB
     - CPU: 1
     - Minimum instances: 1
     - Maximum instances: 1
   - **Variables & Secrets tab**:
     - Click "Add Variable" for environment variables:
       - `OPENAI_MODEL` = `gpt-4.1-nano`
       - `TIMEZONE` = `Europe/London`
       - `BOT_URL` = `https://your-bot-url-here.run.app` (optional - defaults to "ask creator")
     - Click "Reference a Secret" (repeat 3 times):
       - Secret: `telegram-bot-token` → Expose as: Environment variable → Name: `TELEGRAM_BOT_TOKEN`
       - Secret: `openai-api-key` → Expose as: Environment variable → Name: `OPENAI_API_KEY`
       - Secret: `user-chat-id` → Expose as: Environment variable → Name: `USER_CHAT_ID`

9. Click "Create"
10. Wait for deployment to complete (2-3 minutes)

### Step 5: Verify Deployment

1. Click on your deployed service
2. Go to "Logs" tab to see bot activity
3. Test by sending a message to your Telegram bot
4. Check logs for responses and scheduled messages

---

## Method 2: Using gcloud CLI (Alternative)

### Prerequisites

Install Google Cloud CLI: https://cloud.google.com/sdk/docs/install

```bash
gcloud init  # Authenticate and set up
```

### Quick Deploy Commands

```bash
# 1. Create project
gcloud projects create YOUR-PROJECT-ID --name="Telegram Bot"
gcloud config set project YOUR-PROJECT-ID

# 2. Enable APIs and billing
gcloud services enable run.googleapis.com containerregistry.googleapis.com secretmanager.googleapis.com
# Note: Enable billing at https://console.cloud.google.com/billing

# 3. Create secrets
echo -n "YOUR_TELEGRAM_TOKEN" | gcloud secrets create telegram-bot-token --data-file=-
echo -n "YOUR_OPENAI_KEY" | gcloud secrets create openai-api-key --data-file=-
echo -n "YOUR_CHAT_ID" | gcloud secrets create user-chat-id --data-file=-

# 4. Build and push
gcloud auth configure-docker
docker build -t gcr.io/YOUR-PROJECT-ID/telegram-bot:latest .
docker push gcr.io/YOUR-PROJECT-ID/telegram-bot:latest

# 5. Deploy
gcloud run deploy telegram-bot \
    --image gcr.io/YOUR-PROJECT-ID/telegram-bot:latest \
    --region us-central1 \
    --allow-unauthenticated \
    --min-instances 1 \
    --max-instances 1 \
    --memory 256Mi \
    --cpu 1 \
    --set-secrets TELEGRAM_BOT_TOKEN=telegram-bot-token:latest,OPENAI_API_KEY=openai-api-key:latest,USER_CHAT_ID=user-chat-id:latest \
    --set-env-vars OPENAI_MODEL=gpt-4.1-nano,TIMEZONE=Europe/London,BOT_URL=https://your-bot-url-here.run.app

# 6. View logs
gcloud run services logs read telegram-bot --region us-central1
```

---

## Verify Everything Works

1. **Check logs** (Console: Cloud Run → telegram-bot → Logs)
2. **Test the bot**: Send a message to your Telegram bot
3. **Verify scheduled messages**: Check that daily messages are sent
4. **Monitor costs**: Go to Billing → Reports (should be ~$0-2/month)

## Cost Optimization Tips

- **Free tier eligible**: With min-instances=1 at 256Mi, you'll likely stay within Cloud Run free tier (~$0-2/month)
- **Monitor usage**: Check billing dashboard regularly
- **Alternative regions**: `us-central1`, `us-west1`, or `us-east1` have best pricing

## Troubleshooting

**If bot doesn't respond:**

1. Check logs: Console → Cloud Run → telegram-bot → Logs
2. Verify secrets are accessible in Secret Manager
3. Ensure billing is enabled and APIs are activated

**If deployment fails with "Permission denied on secret":**

This means Cloud Run doesn't have permission to access your secrets. Fix it by:

1. Go to "IAM & Admin" → "IAM"
2. Find your compute service account (e.g., `YOUR-PROJECT-NUMBER-compute@developer.gserviceaccount.com`)
3. Add the role: `Secret Manager Secret Accessor`
4. Or run this command:
   ```bash
   gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
       --member="serviceAccount:YOUR-PROJECT-NUMBER-compute@developer.gserviceaccount.com" \
       --role="roles/secretmanager.secretAccessor"
   ```

**If deployment fails with "container failed to start and listen on port":**

This means your bot isn't listening on the required port 8080. The bot code has been updated to include a web server for Cloud Run compatibility. Make sure you have the latest version with:
- `aiohttp` dependency in requirements.txt
- Updated bot.py with web server endpoints

**Other deployment failures:**

- Verify Docker image built successfully
- Check that project ID matches everywhere (replace YOUR-PROJECT-ID)
- Ensure you have Owner or Editor role on the project

## Updating the Bot

When you make code changes:

```bash
docker build -t gcr.io/YOUR-PROJECT-ID/telegram-bot:latest .
docker push gcr.io/YOUR-PROJECT-ID/telegram-bot:latest
```

Then in Console: Cloud Run → telegram-bot → Edit & Deploy New Revision → Select new image

## Files Used

- `bot.py`: Main bot code with polling and scheduled jobs
- `Dockerfile`: Container configuration (already optimized)
- `requirements.txt`: Python dependencies
