# Changelog

All notable changes to AppImage Updater will be documented in this file.

## [Unreleased] - 2025-01-04

### 🔒 Security
- **NEW**: Automatic checksum verification for downloaded files
  - Supports SHA256, SHA1, and MD5 algorithms
  - Configurable checksum file patterns (e.g., `{filename}-SHA256.txt`)
  - Intelligent detection of checksum files in GitHub releases
  - Visual indicators for verification status in download results
  - Optional or required verification modes per application

### 🚀 Improvements
- **FIXED**: HTTP redirect handling for GitHub release downloads
  - Downloads now properly follow 302 redirects from GitHub CDN
  - Resolves previous "Redirect response '302 Found'" errors
  
- **ENHANCED**: Download robustness and reliability
  - Automatic retry logic with exponential backoff (up to 3 attempts)
  - Improved timeout configuration (separate connect/read/write timeouts)
  - Better error handling for network interruptions
  - Progress tracking with transfer speed and ETA

### 📝 Configuration
- **NEW**: Checksum configuration block for applications
  ```json
  "checksum": {
    "enabled": true,
    "pattern": "{filename}-SHA256.txt",
    "algorithm": "sha256", 
    "required": false
  }
  ```
- **NEW**: Application filtering with `--app` option
- **IMPROVED**: Debug logging with `--debug` flag for troubleshooting

### 🛠️ Developer Experience  
- Enhanced logging with checksum verification status
- Comprehensive debug information for download failures
- Better error messages and user feedback
- Updated documentation with security recommendations

### 📋 Technical Details
- Checksum files automatically downloaded and verified
- Support for multiple checksum file formats:
  - Hash + filename: `abc123... filename.AppImage`
  - Hash only: `abc123...`
  - Multiple files: One hash per line
- Configurable patterns support various naming conventions:
  - `{filename}-SHA256.txt` (FreeCAD style)
  - `{filename}_SHA256.txt` (underscore variant)  
  - `{filename}.sha256` (extension-based)

### 🧪 Tested With
- ✅ FreeCAD weekly builds (SHA256 verification)
- ✅ Large file downloads (>800MB) with retry logic
- ✅ GitHub release redirect handling
- ✅ Checksum pattern detection and parsing

---

## Contributing

This project follows [Semantic Versioning](https://semver.org/).
