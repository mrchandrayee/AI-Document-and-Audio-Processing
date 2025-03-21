Steps to obtain SSL certificate
1. First create an A type record in DNS manager of mylightening.com
> Type = A

> Host: ai-api

> Value: Public ip of server or domain

> TTL: Automatic

2. Configure Nginx by going to nginx.conf director

3. Run followinfg command to obtain SSL certificate: `sudo certbot --nginx -d ai-api.mylightening.com`
