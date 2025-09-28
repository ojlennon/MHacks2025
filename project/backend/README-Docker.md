# Plate OCR - Docker Deployment

This FastAPI application is containerized using Docker for easy deployment and scaling.

## Prerequisites

- Docker
- Docker Compose (optional)
- OpenAI API key

## Quick Start

### 1. Environment Setup

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=your_actual_openai_api_key_here
```

### 2. Build and Run with Docker Compose (Recommended)

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### 3. Build and Run with Docker

```bash
# Make build script executable
chmod +x docker-build.sh

# Build the image
./docker-build.sh

# Run the container
docker run -p 8000:8000 --env-file .env plate-ocr:latest
```

### 4. Manual Docker Commands

```bash
# Build the image
docker build -t plate-ocr:latest .

# Run with environment file
docker run -p 8000:8000 --env-file .env plate-ocr:latest

# Run with inline environment variable
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key_here plate-ocr:latest
```

## API Access

Once running, the API will be available at:

- **API Base URL**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Available Endpoints

- `POST /extract` - Extract license plate from image
- `GET /plates` - Get all license plates
- `GET /plate/{plate_number}` - Get specific plate info with alerts
- `POST /plate` - Add new license plate
- `DELETE /plate/{plate_number}` - Delete license plate
- `GET /plate/{plate_number}/alerts` - Get alerts for specific plate

## Health Check

The container includes a health check that monitors the `/plates` endpoint:

```bash
# Check container health
docker ps

# View health check logs
docker inspect --format='{{.State.Health}}' <container_id>
```

## Production Considerations

### Security
- Never commit `.env` files with real API keys
- Use Docker secrets or external secret management in production
- Consider using a reverse proxy (nginx) in front of the application

### Scaling
- Use Docker Swarm or Kubernetes for multi-instance deployment
- Add load balancing for high availability
- Consider using a persistent database instead of in-memory storage

### Monitoring
- Add logging aggregation (ELK stack, etc.)
- Implement application metrics (Prometheus, etc.)
- Set up alerting for health check failures

## Troubleshooting

### Common Issues

1. **Container won't start**:
   ```bash
   docker logs <container_name>
   ```

2. **Health check failing**:
   ```bash
   docker exec -it <container_name> curl http://localhost:8000/plates
   ```

3. **OpenAI API errors**:
   - Verify your API key is correct in `.env`
   - Check API key permissions and billing status

4. **Permission denied**:
   ```bash
   chmod +x docker-build.sh
   ```

### Development

For development with live reload:

```bash
# Mount source code as volume
docker run -p 8000:8000 \
  --env-file .env \
  -v $(pwd):/app \
  plate-ocr:latest \
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```