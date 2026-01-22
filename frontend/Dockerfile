# Frontend Dockerfile (Bun + Next.js standalone) - production-ready for Coolify
FROM oven/bun:1.2-alpine AS base
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Install dependencies (cached)
FROM base AS deps
WORKDIR /app
COPY package.json bun.lock ./
RUN bun install --ci

# Build
FROM base AS builder
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Build-time public vars (set these in Coolify build envs)
ARG NEXT_PUBLIC_CLOUDFRONT_URL
ARG NEXT_PUBLIC_API_BASE
ARG NEXT_PUBLIC_SITE_URL
ENV NEXT_PUBLIC_CLOUDFRONT_URL=$NEXT_PUBLIC_CLOUDFRONT_URL \
    NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE \
    NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL

COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN bun run build

# Runtime image
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000

# Create non-root user
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

# Copy public assets
COPY --from=builder /app/public ./public

# Set correct ownership and prepare .next directory
RUN mkdir -p ./.next && chown -R nextjs:nodejs ./.next

# Copy standalone server and static assets
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000

CMD ["bun", "server.js"]
