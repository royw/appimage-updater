#!/bin/bash
# Local CI simulation script that matches GitHub Actions exactly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Set GitHub Actions environment variables
export GITHUB_ACTIONS=true
export CI=true
export RUNNER_OS=Linux
export RUNNER_ARCH=X64

echo -e "${PURPLE}🔧 AppImage Updater - Local CI Simulation${NC}"
echo -e "${PURPLE}==========================================${NC}"
echo -e "${BLUE}Simulating GitHub Actions CI environment locally${NC}"
echo -e "${BLUE}Python version: $(python --version)${NC}"
echo -e "${BLUE}UV version: $(uv --version)${NC}"
echo ""

# Function to run CI step with timing and proper error handling
run_ci_step() {
    local step_name="$1"
    local command="$2"
    local start_time=$(date +%s)
    
    echo -e "${YELLOW}▶ Step: $step_name${NC}"
    echo -e "${BLUE}Command: $command${NC}"
    echo "----------------------------------------"
    
    if eval "$command"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo -e "${GREEN}✅ $step_name completed in ${duration}s${NC}"
        echo ""
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo -e "${RED}❌ $step_name failed after ${duration}s${NC}"
        echo ""
        return 1
    fi
}

# Ensure we're in the project root
cd "$(dirname "$0")/.."

echo -e "${BLUE}📦 Installing dependencies...${NC}"
uv sync --extra dev

echo -e "\n${PURPLE}🚀 Running CI Pipeline${NC}"
echo -e "${PURPLE}=====================${NC}"

# Run each CI step exactly as in GitHub Actions
run_ci_step "Formatting Check" "uv run ruff format --check src/" || {
    echo -e "${RED}💡 Fix with: uv run ruff format src/${NC}"
    exit 1
}

run_ci_step "Linting" "uv run ruff check src/" || {
    echo -e "${RED}💡 Fix with: uv run ruff check --fix src/${NC}"
    exit 1
}

run_ci_step "Type Checking" "uv run mypy src/" || {
    echo -e "${RED}💡 Check mypy errors above${NC}"
    exit 1
}

run_ci_step "Complexity Analysis" "uv run radon cc src/ --min C" || {
    echo -e "${RED}💡 Refactor complex functions (C+ rating)${NC}"
    exit 1
}

# Run tests with same coverage settings as CI (sequential execution)
run_ci_step "Tests with Coverage" "uv run pytest --cov=src/appimage_updater --cov-report=xml --cov-report=term-missing --dist=no" || {
    echo -e "${RED}💡 Check test failures above${NC}"
    exit 1
}

run_ci_step "Build Package" "uv build" || {
    echo -e "${RED}💡 Check build errors above${NC}"
    exit 1
}

echo -e "${GREEN}🎉 All CI steps passed! Your code is ready for GitHub Actions.${NC}"
echo -e "${GREEN}📊 Coverage report saved to coverage.xml${NC}"
echo -e "${GREEN}📦 Build artifacts in dist/${NC}"
