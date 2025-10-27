# Changelog

All notable changes to ModelHub (Modelling Mate) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2025-01-27

### 🎉 First Major Release

This is the first production-ready release of ModelHub, featuring a complete analytics and modeling platform.

### ✨ Features

#### Core Features
- **Data Import**: CSV and Excel (.xlsx, .xls) file support
- **Data View**: Interactive data table with pagination and summary statistics
- **Period Comparison**: Compare metrics across two time periods with percentage changes
- **Date Range Filtering**: Filter data by date range across all features

#### Analytics & Visualization
- **Advanced Charting**: Multiple chart types (Line, Bar, Area, Scatter, Combo)
  - Dual Y-axis support
  - Customizable colors and styling
  - Interactive tooltips
  - Export to PNG
- **Correlation Analysis**: Ranked correlation matrix with visual heatmap
- **Variable Transformations**: Log, square root, and polynomial transformations

#### Forecasting
- **Prophet Integration**: Time-series forecasting with Meta's Prophet
  - Weekly forecasting with confidence intervals
  - Trend decomposition
  - Yearly seasonality analysis
  - Forecast plot visualization
  - CSV export of seasonality data

#### Feature Engineering
- **Adstock Transformations**: Media decay modeling
- **Lag Variables**: Create time-lagged features
- **Outlier Detection**: Identify and handle statistical outliers
- **Batch Transformations**: Apply multiple transformations at once

#### User Interface
- **Dark Mode**: Professional dark theme with proper contrast
- **Responsive Design**: Adapts to different window sizes
- **Clean Interface**: Minimalist, focused design
- **Date Format**: DD/MM/YYYY format throughout
- **Theme Toggle**: Easy switching between light and dark modes

### 🔧 Technical Features
- **Electron Desktop App**: Native Windows application
- **Auto-Updates**: Automatic update checking and installation
- **Python Backend**: FastAPI backend for advanced analytics
- **OneDrive Integration**: Automatic OneDrive path detection for updates

### 🎨 Design
- **IM Sciences Branding**: Professional dark navy color scheme
- **Consistent Styling**: Unified design language throughout
- **Accessibility**: Proper contrast ratios and readable text
- **Professional Charts**: Publication-ready visualizations

### 📦 Installation
- **NSIS Installer**: Professional Windows installer
- **Desktop Shortcut**: Easy access after installation
- **Dependency Management**: Includes all required Node.js dependencies
- **Python Support**: Optional Python backend for Prophet features

### 🔒 Security
- **No Code Signing**: Currently unsigned (to be added in future)
- **Safe Defaults**: Secure Electron configuration
- **No External Data**: All data processing happens locally

### 📝 Documentation
- Complete release guide
- Build instructions
- User installation guide
- Troubleshooting documentation

---

## [0.1.3] - 2025-01-XX (Pre-release)

### Changed
- Date selector improvements
- Dark mode refinements
- Period comparison enhancements

### Fixed
- Date input visibility in dark mode
- Date format consistency
- Chart rendering issues

---

## [0.1.2] - 2025-01-XX (Pre-release)

### Added
- Period comparison in Data View
- Export functionality for summary statistics
- Improved date range selector

### Changed
- Enhanced dark mode styling
- Better date column auto-detection

---

## [0.1.1] - 2025-01-XX (Pre-release)

### Added
- Basic auto-update infrastructure
- OneDrive path detection
- Prophet forecasting integration

### Fixed
- Backend connectivity issues
- Date filtering bugs

---

## [0.1.0] - 2025-01-XX (Initial Development)

### Added
- Initial project setup
- Basic data loading (CSV, Excel)
- Simple charting
- Correlation analysis
- Variable transformations

---

## Upcoming Features (Roadmap)

### v1.1.0 (Planned)
- [ ] Multiple regression modeling
- [ ] Model diagnostics and validation
- [ ] Enhanced export options (PDF reports)
- [ ] Data preprocessing improvements
- [ ] User preferences and saved sessions

### v1.2.0 (Planned)
- [ ] Marketing Mix Modeling (MMM) module
- [ ] Attribution modeling
- [ ] ROI calculations
- [ ] Advanced statistical tests
- [ ] Multi-file data management

### v2.0.0 (Future)
- [ ] Cloud sync capabilities
- [ ] Collaborative features
- [ ] API integrations
- [ ] Custom plugin system
- [ ] Advanced ML models

---

## Version History

- **1.0.0** - First production release (2025-01-27)
- **0.1.x** - Pre-release development versions
- **0.0.x** - Initial prototypes

---

## Support

For issues, questions, or feature requests:
- **Email**: info@im-sciences.com
- **Website**: https://im-sciences.com

---

## License

Copyright © 2025 Independent Marketing Sciences. All rights reserved.

---

**Note**: This changelog will be updated with each release. Users will be notified of updates through the automatic update system.
