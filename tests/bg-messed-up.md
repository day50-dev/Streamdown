```dockerfile
# Remove this line:
RUN echo "nameserver 8.8.8.8" > /etc/resolv.conf && \
    apt-get update && apt-get install -y \
    python3=3.10.6-1~22.04.1 \
    prometheus
```

