#!/usr/bin/env bash
# =============================================================================
# Deploy Self-Hosted Qdrant on Cloud Run
#
# Runs the official qdrant/qdrant Docker image as a Cloud Run service.
# - No Cloud SQL, no VPC, no API key needed for local instance.
# - Data is ephemeral (resets on restart) — re-index via /api/content/bulk-ingest.
# - For production persistence, mount a GCS bucket (steps shown at end).
#
# Run ONCE: gcloud auth login && ./scripts/provision_qdrant.sh
# =============================================================================
set -euo pipefail

PROJECT_ID="ecol-b0859"
REGION="asia-southeast1"
QDRANT_SERVICE="qdrant"
# Use the same AR repo as strategy-engine for the image
AR_REPO="strategy-engine"
QDRANT_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/qdrant:latest"

echo "=================================================="
echo "  Strategy Engine — Qdrant on Cloud Run Setup"
echo "=================================================="

# ── 1. Pull + push official Qdrant image to our Artifact Registry ─────────────
echo ""
echo "Step 1: Pulling qdrant/qdrant:latest and pushing to Artifact Registry..."
docker pull qdrant/qdrant:latest 2>/dev/null || {
  echo "  ⚠️  Docker not available locally — using the image directly from Docker Hub in Cloud Run"
  QDRANT_IMAGE="qdrant/qdrant:latest"
}

if [[ "$QDRANT_IMAGE" != "qdrant/qdrant:latest" ]]; then
  docker tag qdrant/qdrant:latest "${QDRANT_IMAGE}"
  docker push "${QDRANT_IMAGE}"
  echo "  ✅ Pushed to Artifact Registry"
fi

# ── 2. Deploy Qdrant to Cloud Run ─────────────────────────────────────────────
echo ""
echo "Step 2: Deploying Qdrant to Cloud Run..."
gcloud run deploy "${QDRANT_SERVICE}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --image="${QDRANT_IMAGE}" \
  --port=6333 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=1 \
  --no-allow-unauthenticated \
  --service-account="strategy-engine-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --quiet

echo "  ✅ Qdrant deployed"

# ── 3. Get the Qdrant URL ─────────────────────────────────────────────────────
QDRANT_URL=$(gcloud run services describe "${QDRANT_SERVICE}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --format="value(status.url)")

echo "  Qdrant URL: ${QDRANT_URL}"

# ── 4. Store Qdrant URL in Secret Manager ─────────────────────────────────────
echo ""
echo "Step 3: Storing QDRANT_URL in Secret Manager..."
if gcloud secrets describe "strategy-engine-qdrant-url" \
    --project="${PROJECT_ID}" &>/dev/null; then
  echo -n "${QDRANT_URL}" | gcloud secrets versions add "strategy-engine-qdrant-url" \
    --data-file=- --project="${PROJECT_ID}"
else
  echo -n "${QDRANT_URL}" | gcloud secrets create "strategy-engine-qdrant-url" \
    --data-file=- --project="${PROJECT_ID}" --replication-policy=automatic
fi
echo "  ✅ strategy-engine-qdrant-url secret updated"

# ── 5. Allow strategy-engine to call Qdrant (Cloud Run → Cloud Run IAM) ───────
echo ""
echo "Step 4: Adding IAM binding for strategy-engine-sa → qdrant service..."
gcloud run services add-iam-policy-binding "${QDRANT_SERVICE}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --member="serviceAccount:strategy-engine-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --quiet 2>&1 | grep -E "Updated|already" || true
echo "  ✅ IAM binding applied"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "=================================================="
echo "  ✅ Qdrant Setup Complete!"
echo "=================================================="
echo ""
echo "  Qdrant URL:  ${QDRANT_URL}"
echo "  SM Secret:   strategy-engine-qdrant-url ✅"
echo ""
echo "  ⚠️  NOTE: Qdrant data is EPHEMERAL (resets on Cloud Run restart)."
echo "  When strategy-engine is deployed, run:"
echo "  POST ${QDRANT_URL}/api/content/bulk-ingest"
echo "  to re-index existing published content."
echo ""
echo "  For production persistence, configure a GCS snapshot bucket (future)."
echo ""
