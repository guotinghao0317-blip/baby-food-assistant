#!/bin/sh

# 替换配置文件中的环境变量
envsubst < /etc/nginx/conf.d/default.conf > /etc/nginx/conf.d/default.conf.tmp
mv /etc/nginx/conf.d/default.conf.tmp /etc/nginx/conf.d/default.conf

# 启动 nginx
exec nginx -g 'daemon off;'
