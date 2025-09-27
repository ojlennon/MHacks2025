# License Plate Lookup API

A FastAPI backend for looking up license plate information.

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the development server:
```bash
uvicorn coppa.main:app --reload
```

3. Access the API at `http://localhost:8000`

## Vercel Deployment

This project is configured for deployment on Vercel.

### Files for Vercel:
- `vercel.json` - Vercel configuration
- `api/index.py` - Entry point for Vercel
- `coppa/vercel_main.py` - Vercel-compatible FastAPI app
- `coppa/vercel_model.py` - In-memory database for serverless

### Deploy to Vercel:

1. **Install Vercel CLI** (if not already installed):
```bash
npm i -g vercel
```

2. **Login to Vercel**:
```bash
vercel login
```

3. **Deploy**:
```bash
vercel
```

4. **Follow the prompts**:
   - Set up and deploy? `Y`
   - Which scope? Choose your account
   - Link to existing project? `N`
   - Project name: `license-plate-api` (or your preferred name)
   - Directory: `./` (current directory)
   - Override settings? `N`

### API Endpoints

- `GET /` - API information
- `GET /plates/{plate_number}` - Look up a specific license plate
- `GET /plates` - List all license plates (for testing)

### Sample Data

The API includes sample license plates:
- `ABC123` - John Doe
- `XYZ789` - Jane Smith (has warrant)
- `LMN456` - Alice Johnson (stolen vehicle)
- `DEF321` - Bob Brown (has warrant)

### Production Database

For production use, replace the in-memory database in `vercel_model.py` with:
- Vercel Postgres
- PlanetScale
- Supabase
- Any other cloud database service

The current setup uses an in-memory SQLite database that resets on each request, which is fine for demo purposes but not suitable for production.
