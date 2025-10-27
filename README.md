# Modelling Mate

**Media Analytics**.

Built with Electron, Next.js, TypeScript, and Python (FastAPI + Prophet).

## Quick Start

### For Developers

```bash
# Install dependencies
npm install
cd backend && pip install -r requirements.txt && cd ..

# Run development mode
npm run dev              # Terminal 1: Next.js
npm run electron:dev     # Terminal 2: Electron window
```

### For Building/Deploying

```bash
# Build Windows installer
npm run electron:build:win

# Output: dist/Modelling Mate Setup 0.1.0.exe
```

## Features

1. **Data View** - Import Excel/CSV, explore data with pagination
2. **Charting Tool** - Visualize with transformations (log, adstock, diminishing returns, etc.)
3. **Correlation Analysis** - Color-coded correlation matrix
4. **Prophet Forecasting** - Time-series forecasting with seasonality decomposition
5. **Stepwise Regression** - Automated variable selection
6. **Naming Convention** - Project standards lookup table

## Tech Stack

**Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui, Recharts
**Desktop**: Electron 38
**Backend**: Python FastAPI, Prophet, pandas, numpy, scipy, scikit-learn
**State**: Zustand

## Documentation

- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Installation, building, auto-updates, and troubleshooting
- **[scripts/README.txt](scripts/README.txt)** - End-user installation help
- **[PROPHET-TROUBLESHOOTING.md](PROPHET-TROUBLESHOOTING.md)** - Prophet feature troubleshooting guide
- **[CRITICAL-PROPHET-FIX.md](CRITICAL-PROPHET-FIX.md)** - Important: Prophet version fix (if you installed before 2025-10-27)

## Project Structure

```
Modelling_Mate/
├── app/              # Next.js pages
├── components/       # React components
├── electron/         # Electron main process
├── lib/              # Utilities & state
├── backend/          # FastAPI backend
├── scripts/          # Build scripts
└── docs/             # Documentation
```

## Quick Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Next.js dev server |
| `npm run electron:dev` | Open Electron window |
| `npm run electron:build:win` | Build Windows installer |

## Distribution
    
Share `distribution/Modelling_Mate_Installation/` folder with users. Contains:
- Installer (`.exe`)
- Python dependency installer
- Installation instructions

## License

Proprietary - Independent Marketing Sciences Ltd © 2025
