#!/bin/bash
# Deploy Hotel Booking System to Koyeb
# Since your PostgreSQL is already on Koyeb, this is the best option

echo "🚀 DEPLOYING TO KOYEB"
echo "===================="

# Check if koyeb CLI is available
if ! command -v koyeb &> /dev/null; then
    echo "❌ Koyeb CLI not found"
    echo "💡 Use the web interface instead: https://app.koyeb.com"
    exit 1
fi

# Set your API token
export KOYEB_TOKEN="chb2c9vob23r1p213246wb7a7z39knvo6xwkzqbgcyc6jxu4k8hr4s5qt19p867f"

echo "🔧 Creating Koyeb service..."

# Deploy the app
koyeb --token $KOYEB_TOKEN services create hotel-booking-app \
  --git-url https://github.com/locle27/Koyeb-Booking \
  --git-branch clean-main \
  --instance-type small \
  --region fra \
  --env DATABASE_URL="postgres://koyeb-adm:npg_T4hEuUQeDl7A@ep-little-haze-a2133rvc.eu-central-1.pg.koyeb.app:5432/koyebdb" \
  --env DEFAULT_SHEET_ID="13kQETOUGCVUwUqZrxeLy-WAj3b17SugI4L8Oq09SX2w" \
  --env GOOGLE_API_KEY="AIzaSyA-0V4VgrJbnzQWueDVI9pSOoH_V2EMUg4" \
  --env GCP_CREDS_FILE_PATH="credentials.json" \
  --env USE_POSTGRESQL="false" \
  --env USE_HYBRID_MODE="true" \
  --env FALLBACK_TO_SHEETS="true" \
  --env FLASK_ENV="production" \
  --env PORT="8080"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment initiated!"
    echo "🔗 Check status: https://app.koyeb.com"
    echo "⏳ App will be available in 2-3 minutes"
    
    # Get service details
    echo ""
    echo "📊 Getting service details..."
    koyeb --token $KOYEB_TOKEN services get hotel-booking-app
else
    echo "❌ Deployment failed!"
    echo "💡 Use manual deployment via web interface"
fi