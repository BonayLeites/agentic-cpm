#!/usr/bin/env bash
# =============================================================================
# setup-vps.sh — Provisioning script para CPM Agent Accelerator en VPS
#
# Prerequisitos:
#   - Ubuntu 22.04+ / Debian 12+
#   - Acceso root o sudo
#   - Dominio apuntando a la IP del VPS (A record configurado)
#
# Uso:
#   curl -sSL https://raw.githubusercontent.com/<user>/agentic_cpm/main/scripts/setup-vps.sh | bash
#   o bien: chmod +x setup-vps.sh && ./setup-vps.sh
# =============================================================================

set -euo pipefail

# --- Configuración ---
DOMAIN="${CPM_DOMAIN:-cpm.bonay.dev}"
REPO_URL="${CPM_REPO:-https://github.com/EdisaBonay/agentic_cpm.git}"
INSTALL_DIR="/opt/agentic_cpm"
EMAIL="${CERTBOT_EMAIL:-bonay.santiago@gmail.com}"

echo "================================================="
echo " CPM Agent Accelerator — VPS Setup"
echo " Dominio: $DOMAIN"
echo "================================================="

# --- 1. Actualizar sistema ---
echo "[1/7] Actualizando sistema..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

# --- 2. Instalar Docker ---
echo "[2/7] Instalando Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "$USER"
    echo "  Docker instalado. Puede que necesites re-login para usar docker sin sudo."
else
    echo "  Docker ya instalado."
fi

# --- 3. Instalar Docker Compose (plugin) ---
echo "[3/7] Verificando Docker Compose..."
if ! docker compose version &> /dev/null; then
    sudo apt-get install -y -qq docker-compose-plugin
fi
docker compose version

# --- 4. Instalar Certbot ---
echo "[4/7] Instalando Certbot..."
sudo apt-get install -y -qq certbot

# --- 5. Clonar repositorio ---
echo "[5/7] Clonando repositorio..."
if [ -d "$INSTALL_DIR" ]; then
    echo "  Directorio $INSTALL_DIR ya existe. Haciendo pull..."
    cd "$INSTALL_DIR" && git pull
else
    sudo git clone "$REPO_URL" "$INSTALL_DIR"
    sudo chown -R "$USER:$USER" "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"

# --- 6. Configurar .env ---
echo "[6/7] Configurando .env..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "  ⚠️  IMPORTANTE: Edita .env con tus valores reales:"
    echo "     nano $INSTALL_DIR/.env"
    echo ""
    echo "  Variables requeridas:"
    echo "    DEMO_PIN=<tu-pin>"
    echo "    POSTGRES_PASSWORD=<password-seguro>"
    echo "    AZURE_AI_ENDPOINT=<tu-endpoint>"
    echo "    AZURE_AI_API_KEY=<tu-api-key>"
    echo "    CORS_ORIGINS=[\"https://bonay.dev\",\"https://$DOMAIN\"]"
    echo ""
    echo "  ⚠️  Edita .env ANTES de arrancar los contenedores."
else
    echo "  .env ya existe."
fi

# --- 7. Obtener certificado SSL ---
echo "[7/7] Obteniendo certificado SSL..."
# Parar cualquier servicio en puerto 80
sudo systemctl stop nginx 2>/dev/null || true
docker compose -f docker-compose.prod.yml down 2>/dev/null || true

if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    # Crear directorio simbólico para que nginx.ssl.conf funcione con nombre genérico
    sudo certbot certonly --standalone \
        -d "$DOMAIN" \
        --email "$EMAIL" \
        --agree-tos \
        --non-interactive

    # Crear symlink para que nginx lo encuentre como "cpm"
    sudo ln -sf "/etc/letsencrypt/live/$DOMAIN" /etc/letsencrypt/live/cpm
    echo "  Certificado SSL obtenido para $DOMAIN"
else
    echo "  Certificado SSL ya existe."
    # Asegurar symlink
    sudo ln -sf "/etc/letsencrypt/live/$DOMAIN" /etc/letsencrypt/live/cpm
fi

# --- 8. Configurar firewall ---
echo "[8] Configurando firewall..."
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP (redirect)
sudo ufw allow 443/tcp  # HTTPS
sudo ufw --force enable

# --- 9. Renovación automática de certificados SSL ---
echo "[9] Configurando renovación automática de SSL..."
cat <<'CRON' | sudo tee /etc/cron.d/certbot-renew > /dev/null
# Renovar certificado SSL cada domingo a las 3:00 AM
0 3 * * 0 root certbot renew --pre-hook "cd /opt/agentic_cpm && docker compose -f docker-compose.prod.yml -f docker-compose.ssl.yml stop frontend" --post-hook "cd /opt/agentic_cpm && docker compose -f docker-compose.prod.yml -f docker-compose.ssl.yml start frontend" >> /var/log/certbot-renew.log 2>&1
CRON
echo "  Cron job de renovación SSL configurado."

# --- 10. Arrancar servicios ---
echo ""
echo "================================================="
echo " Setup completo. Para arrancar:"
echo ""
echo "   cd $INSTALL_DIR"
echo "   docker compose -f docker-compose.prod.yml -f docker-compose.ssl.yml up -d --build"
echo "   docker compose exec backend python -m app.db.seed.seed_all"
echo ""
echo " Para renovar certificado (automático via cron):"
echo "   sudo certbot renew --pre-hook 'docker compose -f docker-compose.prod.yml -f docker-compose.ssl.yml stop frontend' --post-hook 'docker compose -f docker-compose.prod.yml -f docker-compose.ssl.yml start frontend'"
echo ""
echo " Verificar: curl -I https://$DOMAIN/api/health"
echo "================================================="
