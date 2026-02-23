#!/bin/bash
# Installation and Setup Script for ML CTF Challenge Platform

echo "======================================"
echo "ML CTF Challenge Platform - Setup"
echo "======================================"
echo ""

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

echo "✓ Python found"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts\activate

# Install requirements
echo ""
echo "Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Initialize database
echo ""
echo "Initializing database..."
python src/main.py --init-db
echo "✓ Database initialized"

# Done
echo ""
echo "======================================"
echo "✓ Setup Complete!"
echo "======================================"
echo ""
echo "To start the application, run:"
echo "  python src/main.py --debug"
echo ""
echo "Then visit: http://127.0.0.1:5000"
echo ""
echo "For quick reference: See QUICK_START.md"
echo ""
