#!/bin/bash

echo "🤖 Installing AI Doctor Voice Dependencies..."
echo "=============================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ Python 3 found"

# Install TTS dependencies
echo "📦 Installing text-to-speech libraries..."
pip3 install pyttsx3==2.90 gTTS==2.4.0 pygame==2.5.2 SpeechRecognition==3.10.0 pydub==0.25.1 numpy==1.24.3

# Check OS and install system dependencies
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🐧 Linux detected. Installing system dependencies..."
    sudo apt-get update
    sudo apt-get install -y espeak espeak-data
    echo "✅ Linux dependencies installed"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 macOS detected. Installing system dependencies..."
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew not found. Please install Homebrew first: https://brew.sh/"
        exit 1
    fi
    brew install espeak
    echo "✅ macOS dependencies installed"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "🪟 Windows detected. No additional system dependencies needed."
    echo "✅ Windows setup complete"
else
    echo "⚠️ Unknown OS. Please install espeak manually for your system."
fi

echo ""
echo "🎉 AI Doctor Voice installation complete!"
echo ""
echo "Features now available:"
echo "✅ Text-to-Speech for AI doctor"
echo "✅ Real-time voice synthesis"
echo "✅ Multiple voice options (male/female)"
echo "✅ Professional medical voice tones"
echo "✅ Background speech processing"
echo ""
echo "To test the AI doctor voice:"
echo "1. Start the application"
echo "2. Trigger an emergency scenario"
echo "3. Click 'Test AI Doctor Voice' button"
echo "4. You should hear the AI doctor speaking!"
echo ""
echo "🚀 Ready to use AI Doctor Voice in video calls!" 