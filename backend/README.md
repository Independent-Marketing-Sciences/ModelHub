# Python Backend for Modelling Mate

FastAPI backend that provides Prophet forecasting and advanced statistical operations.

## Quick Start

### 1. Install Python Dependencies

```bash
cd python-backend
pip install -r requirements.txt
```

### 2. Run the Backend

```bash
python main.py
```

Server runs on: http://localhost:8000

### 3. Test the API

Open browser: http://localhost:8000/docs

This shows the interactive API documentation (Swagger UI).

## API Endpoints

### Health Check
- `GET /` - Basic health check
- `GET /health` - Detailed health check with dependencies

### Prophet Forecasting
- `POST /api/prophet/forecast` - Generate time-series forecast

**Request:**
```json
{
  "dates": ["2024-01-01", "2024-01-02", ...],
  "values": [100, 105, 110, ...],
  "periods": 365,
  "yearly_seasonality": true,
  "weekly_seasonality": true
}
```

**Response:**
```json
{
  "forecast": {
    "dates": [...],
    "yhat": [...],
    "yhat_lower": [...],
    "yhat_upper": [...]
  },
  "components": {
    "dates": [...],
    "trend": [...],
    "yearly": [...],
    "weekly": [...]
  }
}
```

### Stepwise Regression
- `POST /api/regression/stepwise` - Variable selection

**Request:**
```json
{
  "y": [10, 20, 30, ...],
  "X": {
    "var1": [1, 2, 3, ...],
    "var2": [4, 5, 6, ...]
  },
  "method": "forward",
  "significance_level": 0.05
}
```

**Response:**
```json
{
  "selected_variables": ["var1", "var2"],
  "coefficients": {
    "intercept": 5.0,
    "variables": {"var1": 2.5, "var2": 1.3}
  },
  "r_squared": 0.85,
  "adjusted_r_squared": 0.83,
  "p_values": {...},
  "steps": [...]
}
```

### Correlation Analysis
- `POST /api/correlation/matrix` - Advanced correlation

**Request:**
```json
{
  "variables": {
    "var1": [1, 2, 3, ...],
    "var2": [4, 5, 6, ...]
  }
}
```

## Integration with Electron

The Electron app automatically:
1. Starts this Python backend on port 8000
2. Waits for it to be ready
3. Makes HTTP requests from Next.js frontend
4. Shuts down the backend when app closes

## Development

### Test Individual Endpoints

```bash
# Prophet forecast
curl -X POST http://localhost:8000/api/prophet/forecast \
  -H "Content-Type: application/json" \
  -d @test-data/prophet-request.json

# Stepwise regression
curl -X POST http://localhost:8000/api/regression/stepwise \
  -H "Content-Type: application/json" \
  -d @test-data/stepwise-request.json
```

### Run with Auto-Reload

```bash
uvicorn main:app --reload --port 8000
```

## Bundling with Electron

When building the Electron app, Python is bundled using:
- PyInstaller (converts Python to executable)
- Embedded Python distribution
- All dependencies included

Users don't need Python installed!

## Troubleshooting

### Prophet Installation Issues

Prophet requires additional dependencies on Windows:

```bash
# Install Visual C++ Build Tools if needed
pip install prophet
```

If issues persist, use conda:
```bash
conda install -c conda-forge prophet
```

### Port Already in Use

Change port in `main.py`:
```python
uvicorn.run(app, host="127.0.0.1", port=8001)
```

And update Electron `main.js` to match.

### Import Errors

Ensure all dependencies installed:
```bash
pip install -r requirements.txt
```

## Architecture

```
Electron (Frontend)
       ↓
  HTTP Requests
       ↓
FastAPI Backend (Python)
       ↓
 ┌──────────────┐
 │   Prophet    │  Forecasting
 │   Sklearn    │  Regression
 │   Scipy      │  Statistics
 │   Pandas     │  Data processing
 └──────────────┘
```
