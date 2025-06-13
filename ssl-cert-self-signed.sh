#!/bin/bash
# This script creates self signed certificate for local usage

DOMAIN="agentkovac.com"
CERT_DIR="./.local-ssl"
KEY_DIR="./.local-ssl"
NGINX_SNIPPETS_DIR="./.local-ssl/snippets"
CERT_FILE="$CERT_DIR/nginx-selfsigned.crt"
KEY_FILE="$KEY_DIR/nginx-selfsigned.key"
SELF_SIGNED_CONF="$NGINX_SNIPPETS_DIR/self-signed.conf"
SSL_PARAMS_CONF="$NGINX_SNIPPETS_DIR/ssl-params.conf"

# Create directories if they don't exist
mkdir -p $CERT_DIR $KEY_DIR $NGINX_SNIPPETS_DIR

# Generate the self-signed certificate and key
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout $KEY_FILE -out $CERT_FILE -subj "/CN=$DOMAIN"

# Create the self-signed configuration snippet
echo "ssl_certificate $CERT_FILE;" | sudo tee $SELF_SIGNED_CONF
echo "ssl_certificate_key $KEY_FILE;" | sudo tee -a $SELF_SIGNED_CONF

# Create the SSL parameters configuration snippet
cat <<EOL | sudo tee $SSL_PARAMS_CONF
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
ssl_ciphers 'ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384:DHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-SHA384';
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;
EOL

# Instructions for updating the Nginx server block
echo "Please update your Nginx server block to include the following lines:"
echo "include $SELF_SIGNED_CONF;"
echo "include $SSL_PARAMS_CONF;"

ln -sf $CERT_FILE $CERT_DIR/cert.crt
ln -sf $KEY_FILE $KEY_DIR/cert.key
