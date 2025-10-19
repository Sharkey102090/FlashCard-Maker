# Flashcard Generator

A secure, feature-rich GUI-based flashcard generator with double-sided printing support.

## Features

- 🖥️ **Modern GUI**: Built with CustomTkinter for a modern, responsive interface
- 📚 **Rich Editor**: Format text, add images, and create beautiful flashcards
- 🖨️ **Double-Sided Printing**: Perfect alignment for professional flashcards
- 📥 **Multiple Import Formats**: CSV, Excel, JSON support with validation
- 🎨 **Customizable Themes**: Light/dark themes with custom styling
- 🧠 **Study Modes**: Interactive flashcard viewer with quiz functionality
- 🔒 **Secure**: Input validation, data encryption, and secure file handling
- 🔍 **Search & Tags**: Organize and find flashcards easily
- 📊 **Progress Tracking**: Monitor study performance and statistics

## Installation

1. Clone or download this repository
2. Install Python 3.8 or higher
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python main.py
   ```

## Security Features

- Input validation and sanitization
- Secure file handling with path traversal protection
- Data encryption for sensitive information
- Comprehensive error handling and logging
- Memory-safe operations

## Project Structure

```
flashcard-maker/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── src/                   # Source code
│   ├── core/             # Core business logic
│   ├── gui/              # GUI components
│   └── utils/            # Utility functions
├── assets/               # Themes, icons, resources
├── data/                # User data and configurations
├── tests/               # Test suite
└── docs/                # Documentation
```

## Usage

1. **Create Flashcards**: Use the rich text editor to create front/back content
2. **Import Data**: Drag and drop CSV/Excel files or use the import dialog
3. **Customize Layout**: Choose card sizes, themes, and print settings
4. **Generate PDF**: Create print-ready PDFs with double-sided alignment
5. **Study Mode**: Use the interactive viewer to study your flashcards

## Contributing

This is a personal project, but suggestions and improvements are welcome!

## License

MIT License - See LICENSE file for details