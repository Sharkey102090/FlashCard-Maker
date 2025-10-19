"""
Development Scripts
===================

Useful scripts for development and maintenance.
"""

import subprocess
import sys
from pathlib import Path

def run_tests():
    """Run the test suite."""
    print("🧪 Running tests...")
    test_file = Path(__file__).parent / "tests" / "test_basic.py"
    
    try:
        result = subprocess.run([sys.executable, str(test_file)], 
                              capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"Failed to run tests: {e}")
        return False

def check_code_style():
    """Check code style with basic linting."""
    print("🔍 Checking code style...")
    
    src_dir = Path(__file__).parent / "src"
    python_files = list(src_dir.rglob("*.py"))
    
    issues = []
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic checks
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if len(line) > 120:
                    issues.append(f"{file_path}:{i} - Line too long ({len(line)} chars)")
                
                if line.strip().endswith('import *'):
                    issues.append(f"{file_path}:{i} - Wildcard import detected")
        
        except Exception as e:
            issues.append(f"{file_path} - Could not read file: {e}")
    
    if issues:
        print(f"Found {len(issues)} style issues:")
        for issue in issues[:10]:  # Show first 10
            print(f"  {issue}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more")
        return False
    else:
        print("✅ No style issues found")
        return True

def generate_documentation():
    """Generate basic documentation."""
    print("📖 Generating documentation...")
    
    src_dir = Path(__file__).parent / "src"
    docs_dir = Path(__file__).parent / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    # Generate module list
    python_files = list(src_dir.rglob("*.py"))
    
    doc_content = "# Flashcard Generator - Code Documentation\n\n"
    doc_content += "## Modules\n\n"
    
    for file_path in sorted(python_files):
        relative_path = file_path.relative_to(src_dir)
        module_name = str(relative_path).replace('/', '.').replace('\\', '.').replace('.py', '')
        
        doc_content += f"### {module_name}\n"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract docstring
            lines = content.split('\n')
            in_docstring = False
            docstring_lines = []
            
            for line in lines:
                if '"""' in line and not in_docstring:
                    in_docstring = True
                    if line.strip() != '"""':
                        docstring_lines.append(line.split('"""')[1])
                elif in_docstring:
                    if '"""' in line:
                        if line.strip() != '"""':
                            docstring_lines.append(line.split('"""')[0])
                        break
                    else:
                        docstring_lines.append(line)
            
            if docstring_lines:
                doc_content += '\n'.join(docstring_lines) + '\n\n'
            else:
                doc_content += "No documentation available.\n\n"
        
        except Exception as e:
            doc_content += f"Could not read file: {e}\n\n"
    
    # Write documentation
    doc_file = docs_dir / "modules.md"
    with open(doc_file, 'w', encoding='utf-8') as f:
        f.write(doc_content)
    
    print(f"✅ Documentation generated: {doc_file}")

def clean_cache():
    """Clean Python cache files."""
    print("🧹 Cleaning cache files...")
    
    root_dir = Path(__file__).parent
    cache_patterns = ['__pycache__', '*.pyc', '*.pyo', '.pytest_cache']
    
    removed_count = 0
    
    for pattern in cache_patterns:
        if pattern.startswith('__') or pattern.startswith('.'):
            # Directory patterns
            for cache_dir in root_dir.rglob(pattern):
                if cache_dir.is_dir():
                    import shutil
                    shutil.rmtree(cache_dir)
                    removed_count += 1
        else:
            # File patterns
            for cache_file in root_dir.rglob(pattern):
                if cache_file.is_file():
                    cache_file.unlink()
                    removed_count += 1
    
    print(f"✅ Removed {removed_count} cache files/directories")

def build_requirements():
    """Generate requirements.txt from imports."""
    print("📦 Analyzing imports...")
    
    src_dir = Path(__file__).parent / "src"
    python_files = list(src_dir.rglob("*.py"))
    
    imports = set()
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    # Extract module name
                    if line.startswith('import '):
                        module = line.split('import ')[1].split()[0].split('.')[0]
                    else:
                        module = line.split('from ')[1].split()[0].split('.')[0]
                    
                    # Skip standard library and local modules
                    if module not in ['sys', 'os', 'pathlib', 'typing', 'datetime', 
                                    'json', 'csv', 'io', 're', 'uuid', 'random', 
                                    'unittest', 'tempfile', 'subprocess']:
                        imports.add(module)
        
        except Exception:
            continue
    
    # Map to pip package names
    pip_mapping = {
        'customtkinter': 'customtkinter>=5.2.0',
        'PIL': 'Pillow>=10.0.0',
        'pandas': 'pandas>=2.0.0',
        'cryptography': 'cryptography>=41.0.0',
        'cerberus': 'Cerberus>=1.3.4',
        'yaml': 'PyYAML>=6.0',
        'reportlab': 'reportlab>=4.0.4',
        'bleach': 'bleach>=6.0.0'
    }
    
    requirements = []
    for imp in sorted(imports):
        if imp in pip_mapping:
            requirements.append(pip_mapping[imp])
        else:
            requirements.append(imp)
    
    req_file = Path(__file__).parent / "requirements_auto.txt"
    with open(req_file, 'w') as f:
        f.write('\n'.join(requirements))
    
    print(f"✅ Auto-generated requirements: {req_file}")
    print("Found packages:", ', '.join(sorted(imports)))

def main():
    """Main development script."""
    if len(sys.argv) < 2:
        print("Usage: python dev.py <command>")
        print("Commands:")
        print("  test          - Run tests")
        print("  style         - Check code style")
        print("  docs          - Generate documentation")
        print("  clean         - Clean cache files")
        print("  requirements  - Generate requirements.txt")
        print("  all           - Run all checks")
        return
    
    command = sys.argv[1]
    
    if command == "test":
        run_tests()
    elif command == "style":
        check_code_style()
    elif command == "docs":
        generate_documentation()
    elif command == "clean":
        clean_cache()
    elif command == "requirements":
        build_requirements()
    elif command == "all":
        print("🔧 Running all development checks...\n")
        clean_cache()
        print()
        check_code_style()
        print()
        run_tests()
        print()
        generate_documentation()
        print()
        build_requirements()
        print("\n✅ All development checks completed!")
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()