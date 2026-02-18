#!/bin/bash

# Configuration
PROJECT_ID="ecol-b0859"
REPO="Sorranop01/vdo-content"  # Format: username/repo
POOL_NAME="github-pool"
PROVIDER_NAME="github-provider"
SA_NAME="deployer"
location="global"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "🚀 Setting up Workload Identity Federation for $REPO..."

# 1. Enable Services
echo "Step 1: Enabling required services..."
gcloud services enable iamcredentials.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  --project "$PROJECT_ID" || echo -e "${RED}Failed to enable services (might already be enabled)${NC}"

# 2. Create Workload Identity Pool
echo "Step 2: Creating Workload Identity Pool..."
gcloud iam workload-identity-pools create "$POOL_NAME" \
  --project="$PROJECT_ID" \
  --location="$location" \
  --display-name="GitHub Actions Pool" \
  --quiet || echo "Pool might already exist"

# Get Pool ID
POOL_ID=$(gcloud iam workload-identity-pools describe "$POOL_NAME" \
  --project="$PROJECT_ID" \
  --location="$location" \
  --format="value(name)")

echo "✅ Pool ID: $POOL_ID"

# 3. Create Workload Identity Provider
echo "Step 3: Creating Workload Identity Provider..."
gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_NAME" \
  --project="$PROJECT_ID" \
  --location="$location" \
  --workload-identity-pool="$POOL_NAME" \
  --display-name="GitHub Actions Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='$REPO'" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --quiet || echo "Provider might already exist"

# Get Provider Name (WIF_PROVIDER)
WIF_PROVIDER=$(gcloud iam workload-identity-pools providers describe "$PROVIDER_NAME" \
  --project="$PROJECT_ID" \
  --location="$location" \
  --workload-identity-pool="$POOL_NAME" \
  --format="value(name)")

# 4. Create Service Account
echo "Step 4: Creating Service Account..."
gcloud iam service-accounts create "$SA_NAME" \
  --project="$PROJECT_ID" \
  --display-name="GitHub Actions Deployer" \
  --quiet || echo "Service Account might already exist"

SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# 5. Grant Permissions (Roles)
echo "Step 5: Granting permissions..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/run.admin" --quiet > /dev/null

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/storage.admin" --quiet > /dev/null

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/iam.serviceAccountUser" --quiet > /dev/null

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/artifactregistry.admin" --quiet > /dev/null

# 6. Bind Service Account to Workload Identity Pool
echo "Step 6: Binding Service Account to WIF..."
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --project="$PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${POOL_ID}/attribute.repository/${REPO}" \
  --quiet > /dev/null

echo ""
echo "--------------------------------------------------------"
echo "🎉 Setup Complete!"
echo "--------------------------------------------------------"
echo ""
echo "Please set these secrets in GitHub:"
echo ""
echo -e "${GREEN}WIF_PROVIDER${NC}:"
echo "$WIF_PROVIDER"
echo ""
echo -e "${GREEN}WIF_SERVICE_ACCOUNT${NC}:"
echo "$SA_EMAIL"
echo ""
echo "--------------------------------------------------------"
