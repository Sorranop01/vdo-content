# =====================================================
# Strategy Engine Frontend — Production Dockerfile
# Optimised for Cloud Run (Next.js standalone output)
# =====================================================

# Stage 1: Install dependencies
FROM node:20-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --frozen-lockfile


# Stage 2: Build Next.js
FROM node:20-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Standalone output mode (self-contained bundle, no node_modules needed at runtime)
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Build args for public env vars (injected at build time)
ARG NEXT_PUBLIC_API_URL=https://strategy-api-xxxx.run.app

RUN npm run build


# Stage 3: Runtime image
FROM node:20-alpine AS runtime

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Next.js standalone output includes all needed files
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Non-root user
RUN addgroup -g 1001 nodejs && adduser -S -u 1001 nextjs
USER nextjs

ENV PORT=3000
EXPOSE 3000

CMD ["node", "server.js"]
