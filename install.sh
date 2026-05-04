#!/bin/bash
# Installation script for MR Review Agent

set -e

INSTALL_DIR="$HOME/.mr-review-agent"
TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "MR Review Agent - Installation"
echo "=========================================="
echo ""

# Create installation directory
echo "📦 Creating installation directory..."
mkdir -p "$INSTALL_DIR"

# Copy files
echo "📋 Copying agent files..."
cp -r "$TOOL_DIR"/* "$INSTALL_DIR/"

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
cd "$INSTALL_DIR"
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q tree-sitter tree-sitter-typescript gitpython ollama typer rich pydantic

# Create global command
echo "🔗 Creating global command..."
cat > "$HOME/.local/bin/mr-review" << 'EOF'
#!/bin/bash
# MR Review Agent wrapper

AGENT_DIR="$HOME/.mr-review-agent"
cd "$AGENT_DIR"
source .venv/bin/activate
python cli.py "$@"
EOF

chmod +x "$HOME/.local/bin/mr-review"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo "⚠️  Add this to your ~/.zshrc or ~/.bashrc:"
    echo 'export PATH="$HOME/.local/bin:$PATH"'
    echo ""
fi

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "Usage:"
echo "  cd /path/to/your/typescript/repo"
echo "  mr-review                    # Review current branch vs main"
echo "  mr-review --base develop     # Review against develop"
echo "  mr-review --help             # Show all options"
echo ""
echo "Test installation:"
echo "  mr-review test-ollama"
echo ""
