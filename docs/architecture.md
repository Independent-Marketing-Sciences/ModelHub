# ModelHub Architecture Documentation

## Project Overview

**ModelHub** (also known as **Modelling Mate**) is a sophisticated full-stack media analytics and marketing mix modeling (MMM) desktop application built with Electron, Next.js, TypeScript, and Python FastAPI. It provides advanced statistical analysis, time-series forecasting, and data visualization capabilities for marketing analytics professionals.

- **Application Type**: Hybrid Desktop/Web Application
- **Platform Support**: Windows, macOS, Linux
- **Version**: 0.1.0
- **Primary Use Case**: Media analytics, marketing mix modeling, time-series forecasting, regression analysis

---

## Tech Stack Overview

### Frontend Stack
- **Framework**: Next.js 15.5.6 (App Router)
- **Runtime**: React 18.3.1 with TypeScript 5.7.3
- **Styling**: Tailwind CSS 3.4.17 + Tailwind Merge
- **UI Components**: Custom shadcn/ui components + Radix UI primitives
- **Component Libraries**:
  - Material-UI (MUI) 7.3.4 with emotion styling
  - Recharts 2.14.1 (data visualization)
  - Lucide React 0.468.0 (icons)
- **State Management**: Zustand 5.0.2
- **Date Handling**: dayjs 1.11.18, date-fns 4.1.0
- **Data Parsing**: Papa Parse 5.4.1 (CSV), XLSX 0.18.5 (Excel)
- **Theme Management**: next-themes 0.4.6

### Desktop Layer
- **Framework**: Electron 38.3.0
- **Build Tool**: electron-builder 25.1.8
- **Auto-Updates**: electron-updater 6.6.2
- **IPC Communication**: Built-in Electron IPC with context isolation

### Backend Stack
- **Framework**: FastAPI 0.115.6 (Python 3.x)
- **Server**: Uvicorn 0.34.0 with standard extras
- **Core Libraries**:
  - pandas 2.2.3 (data manipulation)
  - numpy 2.2.2 (numerical computing)
  - scipy 1.15.2 (scientific computing)
  - scikit-learn 1.6.1 (machine learning)
  - XGBoost 2.1.3 (gradient boosting)
  - Prophet 1.1.6 (time-series forecasting)
- **Utilities**: python-multipart 0.0.20 (multipart form handling)
- **Packaging**: PyInstaller 6.11.1 (executable creation)

### Build & Development Tools
- **Concurrent Execution**: concurrently 9.1.2
- **Server Readiness**: wait-on 8.0.1
- **Code Quality**: ESLint 8.57.1, next/eslint-config
- **Styling**: PostCSS 8.4.49, autoprefixer 10.4.20
- **Task Running**: npm scripts

---

## Directory Structure

```
ModelHub/
├── src/                           # Next.js frontend source code
│   ├── app/                       # Next.js App Router pages & layout
│   │   ├── layout.tsx            # Root layout with theme provider
│   │   ├── page.tsx              # Home page (LandingPage/MainDashboard)
│   │   └── globals.css           # Global styles
│   │
│   ├── components/               # Reusable React components
│   │   ├── layout/               # Page layout components
│   │   │   ├── LandingPage.tsx   # Data import landing screen
│   │   │   └── MainDashboard.tsx # Tab-based analysis dashboard
│   │   ├── data/                 # Data handling components
│   │   │   ├── DatasetLoader.tsx # File upload handler
│   │   │   └── DateRangeSelector.tsx # Date filtering UI
│   │   ├── ui/                   # Shadcn/ui components
│   │   │   ├── button.tsx, card.tsx, input.tsx, etc.
│   │   ├── theme-provider.tsx    # Next-themes wrapper
│   │   ├── theme-toggle.tsx      # Dark/light mode toggle
│   │   └── ThemeLogo.tsx         # Application branding
│   │
│   ├── features/                 # Feature-specific modules (vertical slice)
│   │   ├── data-view/            # Raw data exploration
│   │   ├── transformations/      # Variable transformations
│   │   ├── correlation/          # Correlation analysis
│   │   ├── prophet/              # Time-series forecasting
│   │   ├── regression/           # Stepwise regression
│   │   ├── feature-extraction/   # ML feature selection
│   │   ├── outlier-detection/    # Anomaly detection
│   │   └── naming-convention/    # Standards lookup
│   │
│   ├── lib/                      # Utility & core logic
│   │   ├── api/                  # Backend communication
│   │   │   └── python-client.ts  # FastAPI REST client (singleton)
│   │   ├── store/                # Zustand state management
│   │   │   └── index.ts          # Global data store
│   │   └── utils/                # Helper functions
│   │
│   └── types/                    # TypeScript definitions
│       └── electron.d.ts         # Electron API interface definitions
│
├── backend/                      # Python FastAPI backend
│   ├── requirements.txt          # Python dependencies
│   └── src/
│       ├── main.py              # FastAPI app initialization & routing
│       └── modules/             # Feature modules (service layer pattern)
│           ├── prophet/         # Time-series forecasting
│           ├── correlation/     # Correlation analysis
│           ├── regression/      # Stepwise regression
│           ├── transformations/ # Data transformations
│           └── feature_extraction/ # ML feature selection
│
├── electron/                    # Electron main process
│   ├── main.js                 # Application entry point, window management
│   └── preload.js              # Context-isolated API bridge
│
├── R-ModellingTool/            # R package integration (legacy/future)
│   └── Package/lanzR/          # R Shiny modeling package
│
├── public/                     # Static assets
├── dist/                       # Built Electron app output
├── out/                        # Next.js static export output
├── docs/                       # Documentation
│
└── Configuration Files
    ├── package.json            # NPM dependencies & scripts
    ├── tsconfig.json           # TypeScript configuration
    ├── next.config.ts          # Next.js static export config
    ├── tailwind.config.ts      # Tailwind CSS customization
    ├── postcss.config.mjs      # PostCSS with Tailwind & autoprefixer
    ├── electron-builder.yml    # Electron build configuration
    └── .eslintrc.json          # ESLint rules
```

---

## Frontend Architecture

### Application Flow

1. **Entry Point**: [src/app/page.tsx](src/app/page.tsx)
   - Single page component with state controlling view switching
   - Toggle between LandingPage and MainDashboard

2. **Landing Page**: [LandingPage.tsx](src/components/layout/LandingPage.tsx)
   - File upload interface for CSV/Excel
   - Uses Papa Parse for CSV and XLSX for Excel parsing
   - Stores parsed data in global Zustand store
   - Transitions to MainDashboard on successful load

3. **Main Dashboard**: [MainDashboard.tsx](src/components/layout/MainDashboard.tsx)
   - Tab-based interface for different analyses
   - Collapsible sidebar navigation
   - Integrated date range selector for global filtering
   - Communicates with Python backend via REST API

### State Management (Zustand)

**Global Data Store** ([lib/store/index.ts](src/lib/store/index.ts)):

```typescript
interface DataStore {
  data: DataRow[]                    // Main dataset rows
  columns: string[]                  // Available column names
  dateColumn: string                 // Designated date field
  dateRangeStart/End: string | null  // Global date filter
  namingConvention: DataRow[]        // Standards lookup table
  isLoading: boolean                 // Loading state
  error: string | null               // Error messages

  // Computed selector
  getFilteredData()                  // Returns filtered by date range
}
```

**Key Patterns**:
- Immutable updates
- Computed selectors for derived state
- No middleware (pure Zustand)
- Shared across all tab components

### Component Organization (Feature-Based Slicing)

Each feature follows this structure:
```
features/[feature-name]/
├── components/
│   └── [Feature]Tab.tsx      # Tab component
├── lib/                       # Optional: feature-specific utilities
└── types/                     # Optional: TypeScript interfaces
```

**Tab Components** (all follow similar pattern):
- Import store with `useDataStore()`
- Get filtered data via `getFilteredData()`
- Use `pythonClient` singleton for API calls
- Handle loading/error states locally
- Render results with Recharts or tables

### API Client Pattern

**Singleton Pattern** ([lib/api/python-client.ts](src/lib/api/python-client.ts)):

```typescript
class PythonBackendClient {
  async isAvailable()              // Health check
  async checkAvailability()        // Detailed diagnostics
  async prophetForecast()          // /api/prophet/forecast
  async stepwiseRegression()       // /api/regression/stepwise
  async correlationMatrix()        // /api/correlation/matrix
  async correlationRanked()        // /api/correlation/ranked
  async transformVariable()        // /api/transform/variable
  async post()                     // Generic endpoint handler
}
```

Base URL: `http://localhost:8000` (configurable)

**Error Handling**:
- Network errors caught and logged
- Backend 4xx/5xx errors parsed and rethrown
- Timeouts handled with AbortSignal

---

## Backend Architecture

### API Structure

**FastAPI Application** ([backend/src/main.py](backend/src/main.py)):

```python
FastAPI(title="Modelling Mate Backend", version="1.0.0")

# CORS enabled for all origins
# 5 module routers registered:
- /api/prophet/      → Time-series forecasting
- /api/correlation/  → Correlation analysis
- /api/regression/   → Stepwise regression
- /api/transform/    → Variable transformations
- /api/feature-extraction/ → ML feature selection
```

**Health Check Endpoints**:
- `GET /` - Status, version, Prophet availability
- `GET /health` - Dependency status (prophet, pandas, sklearn, etc.)

### Module Architecture (Service Layer Pattern)

Each module follows 3-file structure:

1. **models.py** - Pydantic request/response schemas
2. **routes.py** - FastAPI endpoint definitions
3. **service.py** - Core business logic

### Implemented Features

#### 1. Prophet Module (`/api/prophet/forecast`)
- **Input**: Time-series dates, values, seasonality flags, forecast periods
- **Output**:
  - Future forecast with yhat, yhat_lower, yhat_upper (confidence intervals)
  - Trend component
  - Yearly/weekly seasonality (if available)
  - Model parameters
- **Process**: Prophet model fitting, future dataframe generation, component decomposition

#### 2. Correlation Module (`/api/correlation/`)
- **Endpoints**:
  - `/matrix` - Full correlation matrix (Pearson + Spearman + p-values)
  - `/ranked` - Correlations ranked by absolute value for target variable
- **Process**:
  - Drop NaN values
  - Calculate Pearson & Spearman correlations
  - Compute t-statistics and p-values
  - Format as ranked dictionary

#### 3. Regression Module (`/api/regression/stepwise`)
- **Methods**: forward, backward, both
- **Output**:
  - Selected variables list
  - Coefficients (intercept + per-variable)
  - R² and adjusted R²
  - P-values for each variable
  - Step-by-step selection process
- **Algorithm**: Stepwise variable selection using significance levels

#### 4. Transformations Module (`/api/transform/variable`)
- **Supported Transformations** (applied sequentially):
  1. **log**: `log(x + amount)` with log base handling
  2. **lag_lead**: Shift data forward (lag) or backward (lead)
  3. **adstock**: Exponential decay: `x[i] = x[i] + decay * x[i-1]`
  4. **diminishing_returns_absolute**: `x / (x + saturation_point)`
  5. **diminishing_returns_exponential**: Hill curve: `1 - exp(-slope * x)`
  6. **moving_average**: Simple moving average (SMA)
- **Frontend Equivalent**: Mirrored in [src/features/transformations/lib/transformations.ts](src/features/transformations/lib/transformations.ts)

#### 5. Feature Extraction Module (`/api/feature-extraction/extract`)
- Uses scikit-learn for ML-based feature selection
- Splits data into train/test
- Selects top N features by importance
- Returns rankings and importance scores

---

## Electron Integration

### Architecture Pattern: Main + Preload Bridge

**[electron/main.js](electron/main.js)** (Main Process):

1. **Window Management**
   - Create BrowserWindow (1400x900, min 1200x700)
   - Load app://./index.html (production) or http://localhost:3000 (dev)
   - Register custom protocol for static files
   - Display on ready, prevent flashing

2. **Python Backend Lifecycle**
   - Spawn Python process: `python backend/src/main.py`
   - Monitor stdout/stderr
   - Health check polling (every 1 second, timeout 30s)
   - Kill on app quit

3. **Application Menu**
   - File: Open Dataset, Export, Exit
   - View: Reload, DevTools, Zoom, Fullscreen
   - Help: Check Updates, About, Documentation

4. **IPC Handlers**
   - `dialog:openFile` - File dialog with CSV/Excel filters
   - `file:read` - Synchronous file read (Base64 encoded)
   - `app:getVersion` - Application version

5. **Auto-Update System**
   - electron-updater configuration
   - Check on startup + every 4 hours
   - Download/install flow with dialogs
   - Disabled in development mode

**[electron/preload.js](electron/preload.js)** (Context Isolation):

Exposes secure APIs via contextBridge:

```javascript
window.electron = {
  openFile(),        // Dialog → file path
  readFile(path),    // File path → base64 content
  saveFile(data),    // Data → dialog → save path
  getAppVersion()    // → version string
}
```

### Development vs Production Mode

**Development**:
```bash
npm run dev:frontend  # Next.js dev server on :3000
npm run electron:dev  # Wait for :3000, launch Electron, start Python
```

**Production**:
```bash
npm run electron:build:win  # Build Next.js → out/, package with electron-builder
```

At Runtime:
- Load app://./index.html via custom protocol
- Serve from out/ folder
- Unpack backend via asarUnpack
- Spawn Python process

---

## Data Flow Architecture

### Complete Request-Response Cycle

```
1. USER INTERACTION (Frontend)
   ├── Uploads CSV/Excel file (LandingPage)
   │   ├── Papa Parse / XLSX library
   │   └── Stores in Zustand store
   │
   └── Selects analysis tab (MainDashboard)
       └── Chooses variables + parameters

2. STORE UPDATE
   ├── Data stored in global state
   ├── Date range filter applied
   └── Filtered data computed on demand

3. API REQUEST (Frontend → Backend)
   ├── pythonClient picks appropriate endpoint
   ├── Constructs Pydantic request object
   ├── Sends JSON via POST to http://localhost:8000
   └── Sets loading state, clears errors

4. BACKEND PROCESSING
   ├── Route handler parses request
   ├── Service layer validates data
   ├── Applies statistical algorithm
   │   ├── Prophet: ARIMA + seasonality
   │   ├── Correlation: Pearson/Spearman
   │   ├── Regression: Stepwise OLS
   │   ├── Transformations: Sequential ops
   │   └── Features: Mutual information
   └── Returns Pydantic response object

5. RESPONSE HANDLING (Frontend)
   ├── pythonClient deserializes JSON
   ├── Sets results in component state
   ├── Catches errors, displays in UI
   └── Loading state cleared

6. VISUALIZATION
   ├── Recharts renders data
   ├── Tables display statistics
   ├── Charts show trends/relationships
   └── User can export or reanalyze

7. PERSISTENCE
   ├── Store keeps data in memory
   ├── No automatic saves (in-memory only)
   ├── Export via Electron file dialog (future feature)
   └── On refresh: data lost (no persistence layer)
```

---

## Build Configuration

### NPM Scripts

```json
{
  "dev": "concurrently \"next dev\" \"npm run python:dev\"",
  "dev:frontend": "next dev",
  "python:dev": "cd backend/src && python main.py",
  "build": "next build",
  "electron:dev": "concurrently \"npm run dev:frontend\" \"wait-on http://localhost:3000 && electron .\"",
  "electron:build:win": "set CSC_IDENTITY_AUTO_DISCOVERY=false && next build && electron-builder --win --config electron-builder.yml",
  "electron:build:mac": "next build && electron-builder --mac",
  "electron:build:linux": "next build && electron-builder --linux"
}
```

### Next.js Configuration ([next.config.ts](next.config.ts))

```typescript
{
  output: 'export',              // Static export (no Node.js server)
  images: { unoptimized: true }  // Disable image optimization
}
```

**Why**: Electron doesn't run Node.js backend; static files served via custom protocol

### Build Output Structure

```
dist/
├── Modelling Mate Setup 0.1.0.exe    # NSIS installer
└── [other platform installers]

out/                                   # Next.js static export
├── index.html
├── _next/
│   ├── static/
│   │   ├── chunks/
│   │   ├── css/
│   │   └── media/
```

---

## Architectural Patterns

### 1. Monolithic Vertical Slices
Each analysis feature (prophet, correlation, etc.) is self-contained:
- Frontend: Single tab component
- Backend: Dedicated module with routes + service
- Benefits: Easy to test, modify, extend

### 2. Singleton Pattern
- `pythonClient` - Single instance for all API calls
- Eliminates multiple connections
- Provides consistent error handling

### 3. Service Layer Pattern
Backend modules separate routing from business logic:
- Routes: Handle HTTP requests/responses
- Services: Core computation logic
- Models: Data validation (Pydantic)

### 4. Observer Pattern (Zustand)
Global store notifies all consumers of state changes:
- Components subscribe via hooks
- Updates trigger re-renders
- Decoupled components

### 5. Bridge Pattern (Electron)
Preload script bridges secure IPC to renderer:
- Exposes controlled API surface
- Prevents direct Node.js access
- Maintains security boundaries

### 6. Feature-Based Folder Organization
Frontend components grouped by feature, not type:
- Cohesive features
- Easy feature removal
- Clear responsibility

---

## Key Technologies Summary

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| UI Framework | React | 18.3.1 | Component library |
| Server Framework | Next.js | 15.5.6 | SSR/SSG, routing (static export) |
| State Management | Zustand | 5.0.2 | Global state |
| Styling | Tailwind CSS | 3.4.17 | Utility CSS |
| Visualization | Recharts | 2.14.1 | React charts |
| Desktop | Electron | 38.3.0 | Desktop app framework |
| Backend | FastAPI | 0.115.6 | Web framework |
| Data Processing | pandas | 2.2.3 | Data manipulation |
| ML/Stats | scikit-learn | 1.6.1 | Machine learning |
| Forecasting | Prophet | 1.1.6 | Time-series analysis |

---

## Security Considerations

1. **CORS**: Currently `["*"]` - should be restricted in production
2. **File Access**: Electron file APIs exposed via preload bridge
3. **Code Signing**: Disabled in build config (development note)
4. **Context Isolation**: Enabled for renderer process security

---

## Future Enhancements

1. **Data Persistence**: Add database layer for saving projects
2. **Export Functionality**: Implement menu items for data export
3. **R Integration**: Complete integration of R-ModellingTool component
4. **Caching**: Add result caching for repeated analyses
5. **Testing**: Implement unit and integration tests
6. **Logging**: Add structured logging and error tracking

---

*Last Updated: 2025-10-26*
