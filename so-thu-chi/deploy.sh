#!/bin/bash
# =============================================================
# deploy.sh — Deploy So Thu Chi lên VPS
# Chạy: bash deploy.sh [options]
# =============================================================
set -e

APP_NAME="so-thu-chi"
IMAGE_NAME="so-thu-chi:latest"
REPO_URL="https://github.com/huyentay-ai/oc_personal.git"
DEPLOY_DIR="$HOME/$APP_NAME"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo "╔══════════════════════════════════════╗"
echo "║     Sổ Thu Chi — Deploy Script      ║"
echo "╚══════════════════════════════════════╝"
echo ""

# --- 1. Check Docker ---
log "Kiểm tra Docker..."
command -v docker >/dev/null 2>&1 || err "Docker chưa cài. Chạy: curl -fsSL https://get.docker.com | sh"
command -v docker-compose >/dev/null 2>&1 || command -v docker >/dev/null 2>&1 || err "docker-compose chưa cài."
log "Docker OK: $(docker --version)"

# --- 2. Lấy source code ---
if [ -d "$DEPLOY_DIR/.git" ]; then
  log "Cập nhật source code..."
  cd "$DEPLOY_DIR"
  git pull origin master
else
  log "Clone source code về $DEPLOY_DIR..."
  git clone --depth=1 "$REPO_URL" "$DEPLOY_DIR"
  cd "$DEPLOY_DIR"
fi

# Nếu file nằm trong subfolder dashboard/
cd "$DEPLOY_DIR"

# --- 3. Build & start ---
log "Build Docker image..."
if [ -f "dashboard/so_thu_chi.html" ]; then
  # Nếu deploy từ repo gốc (không phải subfolder riêng)
  mkdir -p /tmp/stc-build/src /tmp/stc-build/nginx
  cp dashboard/so_thu_chi.html /tmp/stc-build/src/index.html

  # Inline Dockerfile
  cat > /tmp/stc-build/Dockerfile <<'EOF'
FROM nginx:1.25-alpine
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY src/ /usr/share/nginx/html/
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s CMD wget -qO- http://localhost/health || exit 1
CMD ["nginx", "-g", "daemon off;"]
EOF

  cat > /tmp/stc-build/nginx/default.conf <<'EOF'
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    gzip on;
    gzip_types text/html text/css application/javascript;
    location = /index.html { add_header Cache-Control "no-cache"; }
    location / { try_files $uri $uri/ /index.html; }
    location /health { return 200 "OK\n"; add_header Content-Type text/plain; }
}
EOF
  docker build -t "$IMAGE_NAME" /tmp/stc-build
else
  docker build -t "$IMAGE_NAME" .
fi

log "Dừng container cũ (nếu có)..."
docker stop "$APP_NAME" 2>/dev/null || true
docker rm   "$APP_NAME" 2>/dev/null || true

log "Khởi động container mới..."
docker run -d \
  --name "$APP_NAME" \
  --restart unless-stopped \
  -p 80:80 \
  -e TZ=Asia/Ho_Chi_Minh \
  "$IMAGE_NAME"

# --- 4. Verify ---
sleep 2
STATUS=$(docker inspect --format='{{.State.Status}}' "$APP_NAME" 2>/dev/null || echo "unknown")
if [ "$STATUS" = "running" ]; then
  log "Container đang chạy: $STATUS"
else
  err "Container không khởi động được. Xem log: docker logs $APP_NAME"
fi

HEALTH=$(curl -sf http://localhost/health || echo "FAIL")
if [ "$HEALTH" = "OK" ]; then
  log "Health check OK ✓"
else
  warn "Health check chưa trả lời — có thể cần vài giây nữa."
fi

# --- Done ---
SERVER_IP=$(curl -sf https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   ✅  Deploy thành công!                ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  🌐 URL: http://$SERVER_IP"
echo "  📦 Image: $IMAGE_NAME"
echo "  📋 Logs: docker logs -f $APP_NAME"
echo "  🔄 Update: bash deploy.sh"
echo "  🛑 Dừng: docker stop $APP_NAME"
echo ""
