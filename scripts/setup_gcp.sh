#!/bin/bash
# ====================================================================
# VDO Content — GCP Production Setup Script
#
# Run this ONCE to set up all GCP resources for production.
# Prerequisites: gcloud CLI installed and authenticated.
#
# Usage:
#   chmod +x scripts/setup_gcp.sh
#   ./scripts/setup_gcp.sh
# ====================================================================

set -e

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT_ID="ecol-b0859"
REGION="asia-southeast1"
VDO_SERVICE="vdo-content"
SE_API_SERVICE="strategy-engine-api"
SE_UI_SERVICE="strategy-engine-ui"
AR_REPO_VDO="vdo-content"
AR_REPO_SE="strategy-engine"
CLOUD_TASKS_QUEUE="blueprint-processing"
COMPUTE_SA="${PROJECT_ID}@appspot.gserviceaccount.com"

echo "🌏 Project: $PROJECT_ID | Region: $REGION"
echo "────────────────────────────────────────────────────────────"

# ── Set project ───────────────────────────────────────────────────────────────
gcloud config set project $PROJECT_ID

# ── Enable required APIs ──────────────────────────────────────────────────────
echo "📡 Enabling GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  cloudtasks.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  firestore.googleapis.com \
  cloudbuild.googleapis.com \
  --quiet

echo "✅ APIs enabled"

# ── Artifact Registry: Strategy Engine repo ──────────────────────────────────
echo "📦 Creating Artifact Registry repository: $AR_REPO_SE..."
gcloud artifacts repositories create $AR_REPO_SE \
  --repository-format=docker \
  --location=$REGION \
  --description="Strategy Engine container images" \
  --quiet 2>/dev/null || echo "  (already exists, skipping)"

echo "✅ Artifact Registry ready"

# ── Cloud Tasks Queue ─────────────────────────────────────────────────────────
echo "📬 Creating Cloud Tasks queue: $CLOUD_TASKS_QUEUE..."
gcloud tasks queues create $CLOUD_TASKS_QUEUE \
  --location=$REGION \
  --max-attempts=5 \
  --min-backoff=10s \
  --max-backoff=300s \
  --max-doublings=4 \
  2>/dev/null || echo "  (queue already exists, updating config...)"

# Update queue config (safe to run again)
gcloud tasks queues update $CLOUD_TASKS_QUEUE \
  --location=$REGION \
  --max-attempts=5 \
  --min-backoff=10s \
  --max-backoff=300s \
  --max-doublings=4 \
  --quiet

echo "✅ Cloud Tasks queue ready: $CLOUD_TASKS_QUEUE"

# ── IAM: Grant Cloud Tasks invoker to compute SA ─────────────────────────────
echo "🔐 Granting IAM roles..."

# Allow Cloud Run to invoke the task-worker endpoint
gcloud run services add-iam-policy-binding $VDO_SERVICE \
  --region=$REGION \
  --member="serviceAccount:${COMPUTE_SA}" \
  --role="roles/run.invoker" \
  --quiet 2>/dev/null || true

# Allow SA to create Cloud Tasks
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${COMPUTE_SA}" \
  --role="roles/cloudtasks.enqueuer" \
  --quiet

# Allow SA to read Secret Manager secrets
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${COMPUTE_SA}" \
  --role="roles/secretmanager.secretAccessor" \
  --quiet

# Allow SA to write to Firestore
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${COMPUTE_SA}" \
  --role="roles/datastore.user" \
  --quiet

echo "✅ IAM roles granted"

# ── Secret Manager: STRATEGY_ENGINE_TOKEN ────────────────────────────────────
echo "🔑 Setting up Secret Manager secrets..."

# Generate token if not exists
EXISTING=$(gcloud secrets list --filter="name:STRATEGY_ENGINE_TOKEN" --format="value(name)" 2>/dev/null || echo "")
if [ -z "$EXISTING" ]; then
  TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
  echo -n "$TOKEN" | gcloud secrets create STRATEGY_ENGINE_TOKEN --data-file=- --quiet
  echo "  ✅ Created STRATEGY_ENGINE_TOKEN — value saved to Secret Manager"
  echo "  ⚠️  Copy this token to GitHub Secrets as STRATEGY_ENGINE_TOKEN:"
  gcloud secrets versions access latest --secret="STRATEGY_ENGINE_TOKEN"
  echo ""
else
  echo "  (STRATEGY_ENGINE_TOKEN already exists)"
fi

echo "✅ Secrets configured"

# ── Firestore: Create idempotency collection indexes ─────────────────────────
# Note: Firestore creates collections automatically; indexes are optional
# If you need composite indexes, add them here with gcloud firestore indexes

# ── Cloud SQL (PostgreSQL for Strategy Engine) ────────────────────────────────
echo ""
echo "⚠️  MANUAL STEP REQUIRED: Cloud SQL for Strategy Engine PostgreSQL"
echo "   Option A (Managed): Create Cloud SQL instance via Cloud Console"
echo "     → Choose: PostgreSQL 16, region=$REGION, db=strategy_engine"
echo "   Option B (Serverless): Use Neon/Supabase PostgreSQL (cheaper for low traffic)"
echo "   → After creating, add DATABASE_URL to Secret Manager as:"
echo "     gcloud secrets create SE_DATABASE_URL --data-file=-"
echo ""

# ── Qdrant (Vector DB for Strategy Engine) ────────────────────────────────────
echo "⚠️  MANUAL STEP REQUIRED: Qdrant"
echo "   Option A (Managed): https://cloud.qdrant.io (free tier available)"
echo "   Option B (Self-hosted): Deploy qdrant/qdrant on a GCE VM"
echo "   → After getting URL, add to Secret Manager as:"
echo "     gcloud secrets create SE_QDRANT_URL --data-file=-"
echo ""

# ── Summary ───────────────────────────────────────────────────────────────────
echo "════════════════════════════════════════════════════════════"
echo "✅ GCP Setup Complete!"
echo ""
echo "Next steps:"
echo "  1. Complete manual steps above (Cloud SQL + Qdrant)"
echo "  2. Add GitHub Secrets:"
echo "     - WIF_PROVIDER (already set)"
echo "     - WIF_SERVICE_ACCOUNT (already set)"
echo "     - STRATEGY_ENGINE_TOKEN (from Secret Manager above)"
echo "     - DEEPSEEK_API_KEY, OPENAI_API_KEY, etc."
echo "  3. Push to main → CI/CD deploys automatically"
echo "════════════════════════════════════════════════════════════"
