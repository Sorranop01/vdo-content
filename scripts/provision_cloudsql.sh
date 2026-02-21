#!/usr/bin/env bash
# =============================================================================
# Provision Cloud SQL (PostgreSQL 15) for Strategy Engine
#
# Run ONCE before deploying strategy-engine to Cloud Run.
# Idempotent: safe to re-run.
#
# Prerequisites: gcloud auth login, project = ecol-b0859
# =============================================================================
set -euo pipefail

PROJECT_ID="ecol-b0859"
REGION="asia-southeast1"
INSTANCE_NAME="strategy-engine-db"
DB_NAME="strategy_engine"
DB_USER="strategy"
DB_PASSWORD=""  # Generated below

echo "=================================================="
echo "  Strategy Engine — Cloud SQL Setup"
echo "=================================================="

# ── 1. Generate a strong random password ──────────────────────────────────────
DB_PASSWORD=$(python3 -c "import secrets,string; \
  print(''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32)))")
echo "Generated DB password (will be stored in Secret Manager)"

# ── 2. Enable required APIs ───────────────────────────────────────────────────
echo ""
echo "Step 1: Enabling APIs..."
gcloud services enable sqladmin.googleapis.com \
  --project="${PROJECT_ID}" --quiet
echo "  ✅ Cloud SQL Admin API enabled"

# ── 3. Create Cloud SQL instance (db-f1-micro = cheapest, ~$9/mo) ─────────────
echo ""
echo "Step 2: Creating Cloud SQL instance '${INSTANCE_NAME}'..."
if gcloud sql instances describe "${INSTANCE_NAME}" --project="${PROJECT_ID}" &>/dev/null; then
  echo "  ℹ️  Instance '${INSTANCE_NAME}' already exists — skipping"
else
  gcloud sql instances create "${INSTANCE_NAME}" \
    --project="${PROJECT_ID}" \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region="${REGION}" \
    --storage-type=SSD \
    --storage-size=10GB \
    --backup-start-time=03:00 \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=4 \
    --quiet
  echo "  ✅ Instance created"
fi

# Get the connection name (project:region:instance)
CONNECTION_NAME=$(gcloud sql instances describe "${INSTANCE_NAME}" \
  --project="${PROJECT_ID}" \
  --format="value(connectionName)")
echo "  Connection name: ${CONNECTION_NAME}"

# ── 4. Create database ────────────────────────────────────────────────────────
echo ""
echo "Step 3: Creating database '${DB_NAME}'..."
if gcloud sql databases describe "${DB_NAME}" \
    --instance="${INSTANCE_NAME}" \
    --project="${PROJECT_ID}" &>/dev/null; then
  echo "  ℹ️  Database '${DB_NAME}' already exists — skipping"
else
  gcloud sql databases create "${DB_NAME}" \
    --instance="${INSTANCE_NAME}" \
    --project="${PROJECT_ID}" \
    --quiet
  echo "  ✅ Database '${DB_NAME}' created"
fi

# ── 5. Create database user ───────────────────────────────────────────────────
echo ""
echo "Step 4: Creating database user '${DB_USER}'..."
if gcloud sql users describe "${DB_USER}" \
    --instance="${INSTANCE_NAME}" \
    --project="${PROJECT_ID}" &>/dev/null; then
  echo "  ℹ️  User '${DB_USER}' already exists — updating password"
  gcloud sql users set-password "${DB_USER}" \
    --instance="${INSTANCE_NAME}" \
    --project="${PROJECT_ID}" \
    --password="${DB_PASSWORD}" \
    --quiet
else
  gcloud sql users create "${DB_USER}" \
    --instance="${INSTANCE_NAME}" \
    --project="${PROJECT_ID}" \
    --password="${DB_PASSWORD}" \
    --quiet
  echo "  ✅ User '${DB_USER}' created"
fi

# ── 6. Grant Cloud SQL access to strategy-engine Service Account ──────────────
echo ""
echo "Step 5: Granting Cloud SQL Client role to strategy-engine-sa..."
SA_EMAIL="strategy-engine-sa@${PROJECT_ID}.iam.gserviceaccount.com"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/cloudsql.client" \
  --quiet 2>&1 | grep -E "Updated|already" || true
echo "  ✅ IAM binding applied"

# ── 7. Build DATABASE_URL and store in Secret Manager ─────────────────────────
echo ""
echo "Step 6: Storing DATABASE_URL in Secret Manager..."

# Cloud Run uses Unix socket via Cloud SQL proxy
# Format: postgresql+asyncpg://user:pass@/dbname?host=/cloudsql/conn_name
DATABASE_URL="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${CONNECTION_NAME}"

if gcloud secrets describe "strategy-engine-database-url" \
    --project="${PROJECT_ID}" &>/dev/null; then
  echo -n "${DATABASE_URL}" | gcloud secrets versions add "strategy-engine-database-url" \
    --data-file=- --project="${PROJECT_ID}"
else
  echo -n "${DATABASE_URL}" | gcloud secrets create "strategy-engine-database-url" \
    --data-file=- --project="${PROJECT_ID}" --replication-policy=automatic
fi
echo "  ✅ strategy-engine-database-url secret updated"

# ── 8. Add Cloud SQL instance annotation to cloudrun-api.yaml ─────────────────
echo ""
echo "Step 7: Remember to add Cloud SQL instance to cloudrun-api.yaml"
echo "  Add this annotation under spec.template.metadata.annotations:"
echo "    run.googleapis.com/cloudsql-instances: ${CONNECTION_NAME}"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "=================================================="
echo "  ✅ Cloud SQL Setup Complete!"
echo "=================================================="
echo ""
echo "  Instance:    ${INSTANCE_NAME} (${REGION})"
echo "  Connection:  ${CONNECTION_NAME}"
echo "  Database:    ${DB_NAME}"
echo "  User:        ${DB_USER}"
echo "  SM Secret:   strategy-engine-database-url ✅"
echo ""
echo "  Next steps:"
echo "  1. Update cloudrun-api.yaml to add cloudsql-instances annotation"
echo "  2. Run Alembic migrations on first deploy (entrypoint.sh does this)"
echo "  3. Deploy strategy-engine via CI: git push origin main"
echo ""
