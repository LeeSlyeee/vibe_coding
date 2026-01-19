#!/bin/bash
echo "🔧 Fixing Nginx Configuration..."

# 1. Overwrite default config with our setup
sudo cp ~/project/nginx_setup.conf /etc/nginx/sites-available/default

# 2. Test configuration
echo "🧪 Testing Nginx config..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Configuration Valid! Restarting Nginx..."
    sudo systemctl restart nginx
    echo "🎉 Nginx Updated Successfully!"
else
    echo "❌ Configuration Invalid! Please check errors above."
    exit 1
fi
