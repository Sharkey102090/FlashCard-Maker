"""
Enhanced Startup Script
=======================

Better startup with dependency checking and error handling.
"""

import sys
import os
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required.")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'tkinter',
        'customtkinter', 
        'pillow',
        'pandas',
        'cryptography',
        'cerberus',
        'pyyaml',
        'reportlab'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'tkinter':
                import tkinter
            elif package == 'customtkinter':
                import customtkinter
            elif package == 'pillow':
                import PIL
            elif package == 'pandas':
                import pandas
            elif package == 'cryptography':
                import cryptography
            elif package == 'cerberus':
                import cerberus
            elif package == 'pyyaml':
                import yaml
            elif package == 'reportlab':
                import reportlab
            
            print(f"✅ {package} is installed")
        
        except ImportError:
            print(f"❌ {package} is missing")
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies(missing_packages):
    """Attempt to install missing dependencies."""
    if not missing_packages:
        return True
    
    print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
    
    try:
        # Map package names to pip names
        pip_names = {
            'pillow': 'Pillow',
            'pyyaml': 'PyYAML',
            'customtkinter': 'customtkinter',
            'pandas': 'pandas',
            'cryptography': 'cryptography',
            'cerberus': 'Cerberus',
            'reportlab': 'reportlab'
        }
        
        pip_packages = [pip_names.get(pkg, pkg) for pkg in missing_packages if pkg != 'tkinter' and pkg is not None]
        # Filter out any None values to ensure type safety
        pip_packages = [pkg for pkg in pip_packages if pkg is not None]
        
        if 'tkinter' in missing_packages:
            print("❌ tkinter is not available. Please install Python with tkinter support.")
            return False
        
        if pip_packages:
            # Ensure sys.executable is not None
            python_executable = sys.executable
            if not python_executable:
                print("❌ Cannot determine Python executable path")
                return False
            
            # Type-safe command construction
            install_cmd: list[str] = [python_executable, '-m', 'pip', 'install'] + pip_packages
            subprocess.check_call(install_cmd)
            print("✅ Dependencies installed successfully!")
        
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during installation: {e}")
        return False

def setup_directories():
    """Set up necessary directories."""
    app_dir = Path.home() / '.flashcard_maker'
    directories = [
        app_dir,
        app_dir / 'data',
        app_dir / 'logs',
        app_dir / 'backups'
    ]
    
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✅ Directory ready: {directory}")
        except Exception as e:
            print(f"❌ Failed to create directory {directory}: {e}")
            return False
    
    return True

def run_application():
    """Run the main application."""
    try:
        # Add src directory to Python path
        src_path = Path(__file__).parent / "src"
        sys.path.insert(0, str(src_path))
        
        from src.gui.main_window import FlashcardApp
        
        print("\n🚀 Starting Flashcard Generator...")
        app = FlashcardApp()
        app.run()
    
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("This usually means some dependencies are missing.")
        return False
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        return False
    
    return True

def main():
    """Main startup function."""
    print("🃏 Flashcard Generator - Starting up...")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check dependencies
    missing_packages = check_dependencies()
    
    if missing_packages:
        print(f"\n⚠️  Missing dependencies detected.")
        
        install_choice = input("Would you like to install them automatically? (y/n): ").lower().strip()
        
        if install_choice in ['y', 'yes']:
            if not install_dependencies(missing_packages):
                print("\n❌ Failed to install dependencies. Please install manually:")
                print("pip install -r requirements.txt")
                sys.exit(1)
        else:
            print("\n📋 Please install the missing dependencies manually:")
            print("pip install -r requirements.txt")
            sys.exit(1)
    
    # Set up directories
    if not setup_directories():
        print("❌ Failed to set up directories")
        sys.exit(1)
    
    # Run application
    print("\n" + "=" * 50)
    success = run_application()
    
    if not success:
        print("\n❌ Application failed to start")
        sys.exit(1)

if __name__ == "__main__":
    main()