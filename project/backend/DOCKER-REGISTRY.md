# Docker Registry Push Guide

This guide shows you how to push your Plate OCR Docker image to various registries.

## Prerequisites

1. **Build your image first:**
   ```bash
   docker build -t plate-ocr:latest .
   ```

2. **Have accounts set up:**
   - Docker Hub account
   - GitHub account (for GHCR)
   - AWS account (for ECR)
   - Google Cloud account (for GCR)

## Quick Commands

### Docker Hub
```bash
# Login
docker login

# Tag your image
docker tag plate-ocr:latest YOUR_USERNAME/plate-ocr:latest

# Push
docker push YOUR_USERNAME/plate-ocr:latest
```

### GitHub Container Registry (GHCR)
```bash
# Login (use GitHub token with 'write:packages' scope)
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Tag your image  
docker tag plate-ocr:latest ghcr.io/YOUR_USERNAME/plate-ocr:latest

# Push
docker push ghcr.io/YOUR_USERNAME/plate-ocr:latest
```

### AWS ECR
```bash
# Login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Create repository (one time)
aws ecr create-repository --repository-name plate-ocr --region us-east-1

# Tag your image
docker tag plate-ocr:latest ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/plate-ocr:latest

# Push
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/plate-ocr:latest
```

### Google Container Registry (GCR)
```bash
# Configure authentication
gcloud auth configure-docker

# Tag your image
docker tag plate-ocr:latest gcr.io/PROJECT_ID/plate-ocr:latest

# Push
docker push gcr.io/PROJECT_ID/plate-ocr:latest
```

## Using the Automated Script

Run the interactive script:
```bash
chmod +x docker-push.sh
./docker-push.sh
```

Or specify a version:
```bash
./docker-push.sh v1.0.0
```

## Deployment Examples

### Docker Compose with Registry Image
```yaml
version: '3.8'
services:
  plate-ocr:
    image: your-username/plate-ocr:latest
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: plate-ocr
spec:
  replicas: 3
  selector:
    matchLabels:
      app: plate-ocr
  template:
    metadata:
      labels:
        app: plate-ocr
    spec:
      containers:
      - name: plate-ocr
        image: your-username/plate-ocr:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: openai-key
```

### Cloud Run (GCP)
```bash
# Deploy from GCR
gcloud run deploy plate-ocr \
    --image gcr.io/PROJECT_ID/plate-ocr:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY
```

### AWS ECS Task Definition
```json
{
  "family": "plate-ocr",
  "containerDefinitions": [
    {
      "name": "plate-ocr",
      "image": "ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/plate-ocr:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "OPENAI_API_KEY",
          "value": "your-api-key"
        }
      ],
      "essential": true,
      "memory": 512,
      "cpu": 256
    }
  ],
  "requiresCompatibilities": ["FARGATE"],
  "networkMode": "awsvpc",
  "memory": "512",
  "cpu": "256"
}
```

## Security Best Practices

1. **Never include secrets in images:**
   - Use environment variables
   - Use secrets management systems
   - Don't commit `.env` files

2. **Use specific version tags:**
   ```bash
   docker tag plate-ocr:latest your-username/plate-ocr:v1.0.0
   ```

3. **Scan images for vulnerabilities:**
   ```bash
   docker scan your-username/plate-ocr:latest
   ```

4. **Use multi-stage builds for smaller images:**
   - Already implemented in your Dockerfile
   - Reduces attack surface

## Registry Comparison

| Registry | Pros | Cons | Best For |
|----------|------|------|----------|
| Docker Hub | Easy, popular, free tier | Rate limits, public by default | Open source projects |
| GHCR | Free, integrated with GitHub | Newer, less tooling | GitHub-based projects |
| AWS ECR | AWS integration, private | AWS-only, more complex | AWS deployments |
| GCR | Google Cloud integration | GCP-only, more complex | GCP deployments |

Choose based on your deployment target and team preferences!