# Sổ Thu Chi — Hướng dẫn Deploy VPS

## Yêu cầu
- VPS chạy Ubuntu 20.04+ / Debian 11+
- Docker & Docker Compose đã cài
- Port 80 (và 443 nếu dùng HTTPS) được mở

---

## Cách 1 — Deploy nhanh (1 lệnh)

```bash
# SSH vào VPS
ssh user@your-server-ip

# Chạy deploy script
curl -fsSL https://raw.githubusercontent.com/huyentay-ai/oc_personal/master/so-thu-chi/deploy.sh | bash
```

---

## Cách 2 — Deploy thủ công

```bash
# 1. Clone repo
git clone https://github.com/huyentay-ai/oc_personal.git
cd oc_personal/so-thu-chi

# 2. Build & chạy
docker-compose up -d --build

# 3. Kiểm tra
docker ps
curl http://localhost/health
```

---

## Cập nhật khi có thay đổi

```bash
cd ~/oc_personal
git pull origin master
cd so-thu-chi
docker-compose up -d --build
```

---

## Cài Docker (nếu chưa có)

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Đăng xuất rồi đăng nhập lại để có hiệu lực
```

---

## HTTPS với Let's Encrypt (tùy chọn)

```bash
# Cài certbot
sudo apt install certbot python3-certbot-nginx -y

# Thay domain thật vào nginx/default.conf:
#   server_name your-domain.com;

# Dừng container, chạy certbot, rồi restart
docker-compose down
sudo certbot --nginx -d your-domain.com
docker-compose up -d
```

---

## Lệnh thường dùng

| Lệnh | Mô tả |
|------|-------|
| `docker logs -f so-thu-chi` | Xem log realtime |
| `docker stop so-thu-chi` | Dừng app |
| `docker start so-thu-chi` | Khởi động lại |
| `docker stats so-thu-chi` | Xem CPU/RAM |
| `docker exec -it so-thu-chi sh` | Vào trong container |
