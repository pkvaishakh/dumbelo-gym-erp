# The web app as a container, for a server that runs everything itself (deploy/oracle). Vercel doesn't use this.
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
RUN npm run build

ENV NODE_ENV=production
EXPOSE 3000
# next itself, not npm, so it gets the stop signal and shuts down cleanly.
CMD ["node_modules/.bin/next", "start", "-p", "3000"]
