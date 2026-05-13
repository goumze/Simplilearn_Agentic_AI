#!/bin/bash

###############################################################################
# CrewAI Setup Script
# This script sets up CrewAI framework with all dependencies
# Usage: bash setup_crewai.sh
###############################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}==================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}==================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Verify Python installation
check_python() {
    print_header "Checking Python Installation"
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python version: $python_version"
}

# Upgrade pip
upgrade_pip() {
    print_header "Upgrading pip"
    python3 -m pip install --upgrade pip setuptools wheel
    print_success "pip upgraded successfully"
}

# Ensure ~/.local/bin is on PATH (pip user installs land here)
fix_path() {
    print_header "Configuring PATH"

    LOCAL_BIN="$HOME/.local/bin"

    # Add to current session
    export PATH="$LOCAL_BIN:$PATH"

    # Persist across future shells
    for rc_file in "$HOME/.bashrc" "$HOME/.profile"; do
        if [ -f "$rc_file" ] && ! grep -q "$LOCAL_BIN" "$rc_file"; then
            echo "" >> "$rc_file"
            echo "# Added by setup_crewai.sh" >> "$rc_file"
            echo "export PATH=\"$LOCAL_BIN:\$PATH\"" >> "$rc_file"
            print_success "Added $LOCAL_BIN to PATH in $rc_file"
        fi
    done

    print_success "PATH configured: $LOCAL_BIN is on PATH"
}

# Install CrewAI
install_crewai() {
    print_header "Installing CrewAI Framework"
    
    print_warning "Installing CrewAI and dependencies..."
    python3 -m pip install --user crewai crewai-tools
    
    print_success "CrewAI installed successfully"
}

# Install additional dependencies
install_dependencies() {
    print_header "Installing Additional Dependencies"
    
    print_warning "Installing requirements..."
    
    # Core dependencies
    python3 -m pip install \
        python-dotenv \
        pydantic \
        langchain \
        langchain-community \
        openai \
        anthropic \
        google-generativeai \
        ipython \
        jupyter \
        ipykernel
    
    print_success "All dependencies installed successfully"
}

# Verify installation
verify_installation() {
    print_header "Verifying Installation"
    
    if python3 -c "import crewai; print(f'CrewAI version: {crewai.__version__}')" 2>/dev/null; then
        print_success "CrewAI Python package is properly installed"
    else
        print_error "CrewAI installation verification failed"
        exit 1
    fi

    # Verify the CLI is reachable
    if command -v crewai &> /dev/null; then
        crewai_cli_version=$(crewai --version 2>&1)
        print_success "CrewAI CLI is available: $crewai_cli_version"
    else
        print_warning "crewai CLI not found on PATH after install."
        print_warning "Run: source ~/.bashrc  (or open a new terminal) to pick up the updated PATH."
    fi
}

# Display environment setup info
display_setup_info() {
    print_header "Setup Information"
    
    cat << EOF
${GREEN}CrewAI has been successfully set up!${NC}

Next steps:
1. Create a .env file with your API keys:
   - OPENAI_API_KEY=your_openai_key
   - ANTHROPIC_API_KEY=your_anthropic_key
   - GOOGLE_API_KEY=your_google_key

2. Use CrewAI in your Python code:
   from crewai import Agent, Task, Crew

3. To run Jupyter notebooks with CrewAI:
   jupyter notebook

4. Documentation: https://docs.crewai.com/

${YELLOW}To run this setup again in the future:${NC}
   bash setup_crewai.sh

EOF
}

# Main execution
main() {
    print_header "CrewAI Setup Script Started"
    
    check_python
    fix_path
    upgrade_pip
    install_crewai
    install_dependencies
    verify_installation
    display_setup_info
    
    print_success "CrewAI setup completed successfully!"
}

# Run main function
main "$@"
