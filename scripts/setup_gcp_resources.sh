#!/usr/bin/env bash
# ================================================================
# setup_gcp_resources.sh
# One-time setup script for Strategy Engine → vdo-content integration
#
# Usage:
#   gcloud auth login
#   gcloud config set project ecol-b0859
#   bash scripts/setup_gcp_resources.sh
# ================================================================
set -euo pipefail

PROJECT_ID="ecol-b0859"
REGION="asia-southeast1"
QUEUE_NAME="blueprint-processing"
AR_REPO="strategy-engine"
SA_NAME="strategy-engine-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
SECRET_NAME="strategy-engine-secrets"

echo "🚀 Setting up GCP resources for Strategy Engine on project: ${PROJECT_ID}"
echo ""

# ── 1. Enable required APIs ─────────────────────────────────────────────
echo "1️⃣  Enabling required APIs..."
gcloud services enable \
  cloudtasks.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  run.googleapis.com \
  --project="${PROJECT_ID}"
echo "   ✅ APIs enabled"
echo ""

# ── 2. Cloud Tasks queue ────────────────────────────────────────────────
echo "2️⃣  Creating Cloud Tasks queue: ${QUEUE_NAME}..."
if gcloud tasks queues describe "${QUEUE_NAME}" \
    --location="${REGION}" --project="${PROJECT_ID}" &>/dev/null; then
  echo "   ℹ️  Queue already exists — skipping"
else
  gcloud tasks queues create "${QUEUE_NAME}" \
    --location="${REGION}" \
    --project="${PROJECT_ID}" \
    --max-attempts=5 \
    --max-retry-duration=3600s \
    --min-backoff=10s \
    --max-backoff=300s \
    --max-doublings=4
  echo "   ✅ Queue created: ${QUEUE_NAME}"
fi
echo ""

# ── 3. Artifact Registry repo ────────────────────────────────────────────
echo "3️⃣  Creating Artifact Registry repo: ${AR_REPO}..."
if gcloud artifacts repositories describe "${AR_REPO}" \
    --location="${REGION}" --project="${PROJECT_ID}" &>/dev/null; then
  echo "   ℹ️  Repo already exists — skipping"
else
  gcloud artifacts repositories create "${AR_REPO}" \
    --repository-format=docker \
    --location="${REGION}" \
    --project="${PROJECT_ID}" \
    --description="Strategy Engine Docker images"
  echo "   ✅ Artifact Registry repo created: ${AR_REPO}"
fi
echo ""

# ── 4. Service Account ───────────────────────────────────────────────────
echo "4️⃣  Creating service account: ${SA_NAME}..."
if gcloud iam service-accounts describe "${SA_EMAIL}" \
    --project="${PROJECT_ID}" &>/dev/null; then
  echo "   ℹ️  Service account already exists — skipping creation"
else
  gcloud iam service-accounts create "${SA_NAME}" \
    --display-name="Strategy Engine Cloud Run SA" \
    --project="${PROJECT_ID}"
  echo "   ✅ Service account created: ${SA_EMAIL}"
fi

echo "   → Granting roles to ${SA_EMAIL}..."
for ROLE in \
  roles/run.invoker \
  roles/cloudtasks.enqueuer \
  roles/secretmanager.secretAccessor \
  roles/datastore.user; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${ROLE}" \
    --quiet
  echo "     ✅ ${ROLE}"
done
echo ""

# ── 5. Secret Manager ────────────────────────────────────────────────────
echo "5️⃣  Creating Secret Manager secret: ${SECRET_NAME}..."
if gcloud secrets describe "${SECRET_NAME}" \
    --project="${PROJECT_ID}" &>/dev/null; then
  echo "   ℹ️  Secret already exists — skipping creation"
else
  gcloud secrets create "${SECRET_NAME}" \
    --project="${PROJECT_ID}" \
    --replication-policy="automatic"
  echo "   ✅ Secret created: ${SECRET_NAME}"
fi

echo ""
echo "   ⚠️  ACTION REQUIRED — Add secret versions manually:"
echo "   Run the following for each key (replace <VALUE> with actual value):"
echo ""

KEYS=(
  "openai_api_key:<your-openai-api-key>"
  "deepseek_api_key:<your-deepseek-api-key>"
  "database_url:postgresql+asyncpg://strategy:strategy@<CLOUD_SQL_HOST>:5432/strategy_engine"
  "dataforseo_login:<your-dataforseo-login-or-empty>"
  "dataforseo_password:<your-dataforseo-password-or-empty>"
  "production_webhook_url:https://vdo-content-1040928076984.asia-southeast1.run.app/api/strategy/ingest"
  "production_webhook_token:<same-value-as-STRATEGY_ENGINE_TOKEN-github-secret>"
  "qdrant_url:https://<your-qdrant-host>:6333"
)

for KV in "${KEYS[@]}"; do
  KEY="${KV%%:*}"
  EXAMPLE_VAL="${KV#*:}"
  echo "   echo -n '${EXAMPLE_VAL}' | gcloud secrets versions add ${SECRET_NAME} --data-file=- --project=${PROJECT_ID}"
  echo "   # (key: ${KEY})"
  echo ""
done

# ── 6. Allow vdo-content to enqueue Cloud Tasks ──────────────────────────
VDO_SA="1040928076984-compute@developer.gserviceaccount.com"
echo "6️⃣  Granting Cloud Tasks enqueuer to vdo-content service account (${VDO_SA})..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${VDO_SA}" \
  --role="roles/cloudtasks.enqueuer" \
  --quiet
echo "   ✅ Granted roles/cloudtasks.enqueuer to vdo-content SA"
echo ""

# ── 7. Summary ───────────────────────────────────────────────────────────
echo "════════════════════════════════════════════════════════════════"
echo "✅ GCP resource setup complete!"
echo ""
echo "Next steps:"
echo "  1. Add secret versions to ${SECRET_NAME} (see commands above)"
echo "  2. Set STRATEGY_ENGINE_TOKEN in GitHub → Settings → Secrets"
echo "     (same value as production_webhook_token secret above)"
echo "  3. Trigger strategy-engine deploy:"
echo "     git push origin main  (or manually trigger deploy-strategy-engine.yml)"
echo "════════════════════════════════════════════════════════════════"
