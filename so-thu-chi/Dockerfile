FROM nginx:1.25-alpine

LABEL maintainer="Lee <leehungitc@gmail.com>"
LABEL description="So Thu Chi - Expense Tracker"

# Remove default config
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy nginx template (envsubst runs automatically at container start)
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template

# Copy app
COPY src/ /usr/share/nginx/html/

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost/health || exit 1

# nginx:alpine image auto-runs envsubst on /etc/nginx/