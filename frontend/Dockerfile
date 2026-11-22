# syntax=docker/dockerfile:1
# Frontend image (SPEC-11 §2): Node 22 builds the SPA, nginx serves it and proxies the API.
# The API base is the relative /api/v1, so no URL is baked in at build time.

FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

FROM nginx:1.31-alpine
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY nginx/security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY nginx/proxy.conf /etc/nginx/snippets/proxy.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --retries=10 CMD wget -qO- http://127.0.0.1/ > /dev/null || exit 1
