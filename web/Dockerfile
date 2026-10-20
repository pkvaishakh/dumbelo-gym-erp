# The web app as a container, for a server that runs everything itself (deploy/server). Vercel doesn't use this.
FROM node:20-slim
ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /app
RUN chown node:node /app
# Nothing here needs root.
USER node

# Packages first: the layer is cached until package-lock.json changes, so a code-only build skips the install.
COPY --chown=node:node package.json package-lock.json ./
RUN npm ci

COPY --chown=node:node . .
# Baked into the build, like on Vercel: a new API address means building the image again.
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
# The landing page: its own address (canonical links, sitemap, share previews), sales' email and WhatsApp number.
# Also baked in. Empty ones fall back to the defaults in src/lib/site.ts (no WhatsApp number: no WhatsApp buttons).
ARG NEXT_PUBLIC_SITE_URL
ARG NEXT_PUBLIC_CONTACT_EMAIL
ARG NEXT_PUBLIC_SALES_WHATSAPP
ENV NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL \
    NEXT_PUBLIC_CONTACT_EMAIL=$NEXT_PUBLIC_CONTACT_EMAIL \
    NEXT_PUBLIC_SALES_WHATSAPP=$NEXT_PUBLIC_SALES_WHATSAPP
RUN npm run build

ENV NODE_ENV=production
EXPOSE 3000
# next itself, not npm, so it gets the stop signal and shuts down cleanly.
CMD ["node_modules/.bin/next", "start", "-p", "3000"]
