# ---- Build stage (optional: future npm build) ----
FROM nginx:1.25-alpine

LABEL maintainer="Lee <leehungitc@gmail.com>"
LABEL description="So Thu Chi - Expense Tracker"

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy nginx config
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# Copy app source
COPY src/ /usr/share/nginx/html/

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
