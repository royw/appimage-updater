#!/bin/bash
set -e

# GitHub Actions environment simulation
export GITHUB_ACTIONS=true
export CI=true
export RUNNER_OS=Linux
export RUNNER_ARCH=X64

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 GitHub Actions CI Runner (Local)${NC}"
echo -e "${BLUE}=====================================${NC}"

# Function to run CI step with proper formatting
run_step() {
    local step_name="$1"
    local command="$2"
    
    echo -e "\n${YELLOW}▶ $step_name${NC}"
    echo "Command: $command"
    echo "----------------------------------------"
    
    if eval "$command"; then
        echo -e "${GREEN}✅ $step_name - PASSED${NC}"
        return 0
    else
        echo -e "${RED}❌ $step_name - FAILED${NC}"
        return 1
    fi
}

# Default to running all CI steps if no arguments provided
if [ $# -eq 0 ]; then
    echo -e "${BLUE}Running full CI pipeline...${NC}"
    
    # Run all CI steps in order
    run_step "Formatting Check" "uv run ruff format --check src/" || exit 1
    run_step "Linting" "uv run ruff check src/" || exit 1
    run_step "Type Checking" "uv run mypy src/" || exit 1
    run_step "Complexity Analysis" "uv run radon cc src/ --min C" || exit 1
    run_step "Tests" "uv run pytest --cov=src/appimage_updater --cov-report=xml --cov-report=term-missing" || exit 1
    run_step "Build Package" "uv build" || exit 1
    
    echo -e "\n${GREEN}🎉 All CI steps completed successfully!${NC}"
else
    # Run specific command
    echo -e "${BLUE}Running custom command: $*${NC}"
    exec "$@"
fi
