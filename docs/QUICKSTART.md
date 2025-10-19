"""
Quick Start Guide
=================

Getting started with the Flashcard Generator.
"""

# Quick Start Guide

## Installation

1. **System Requirements**
   - Python 3.8 or higher
   - Windows, macOS, or Linux
   - At least 500MB free disk space

2. **Quick Installation**
   ```bash
   # Option 1: Use the startup script (recommended)
   python start.py
   
   # Option 2: Manual installation
   pip install -r requirements.txt
   python main.py
   ```

## First Steps

### Creating Your First Flashcard Set

1. **Launch the Application**
   - Run `python start.py` from the project directory
   - The main window will open with a modern dark/light theme

2. **Create a New Set**
   - Click "New Set" in the sidebar
   - You'll see an empty flashcard editor

3. **Add Your First Flashcard**
   - Click the "Add" button in the flashcard list
   - Enter your question in the "Front Side" editor
   - Enter the answer in the "Back Side" editor
   - Add a category and tags if desired

4. **Save Your Set**
   - Click "Save Set" in the sidebar
   - Choose a filename and location
   - Your flashcards are now saved securely

### Importing Existing Data

The application supports importing from:

- **CSV Files**: Use columns named 'front', 'back', 'category', 'tags'
- **Excel Files**: Same column structure as CSV
- **JSON Files**: Structured flashcard data

**Sample CSV format:**
```csv
front,back,category,tags
"What is Python?","A programming language","Programming","coding,syntax"
"What is a variable?","A storage location with a name","Programming","basics,fundamentals"
```

### Study Mode

1. **Switch to Study Mode**
   - Click "Study Mode" in the sidebar
   - Your flashcards will appear one at a time

2. **Study Features**
   - Click "Flip Card" to see the answer
   - Use "Easy", "Medium", "Hard" to track your progress
   - Click "Shuffle" to randomize the order
   - Navigate with "Previous" and "Next" buttons

### Printing Your Flashcards

1. **Configure Print Settings**
   - Go to Settings → Printing tab
   - Set card dimensions (default: 3.5" x 2.5")
   - Choose cards per page layout

2. **Generate PDF**
   - Export your flashcard set
   - Choose PDF format
   - Select single-sided or double-sided printing
   - Print the generated PDF

## Advanced Features

### Rich Text Formatting

The editor supports:
- **Bold**, *italic*, and underlined text
- Different font sizes and colors
- Images (automatically resized)
- Basic HTML formatting

### Security Features

- Data encryption for sensitive flashcards
- Input validation and sanitization
- Secure file handling
- Automatic backups

### Customization

- **Themes**: Light, dark, or system theme
- **Fonts**: Choose your preferred font family and size
- **Print Layouts**: Customize card sizes and layouts
- **Categories and Tags**: Organize your flashcards

## Tips for Effective Use

1. **Organization**
   - Use meaningful categories (e.g., "Spanish Vocabulary", "History Facts")
   - Add relevant tags for easy searching
   - Keep related flashcards in the same set

2. **Content Creation**
   - Keep questions concise and clear
   - Use images when helpful
   - Break complex topics into smaller cards

3. **Study Strategies**
   - Review regularly for better retention
   - Use the difficulty tracking to focus on problem areas
   - Shuffle cards to avoid memorizing order

4. **Data Management**
   - Save frequently (auto-save is enabled)
   - Export important sets as backups
   - Use meaningful filenames

## Troubleshooting

### Common Issues

**Application won't start:**
- Ensure Python 3.8+ is installed
- Run `python start.py` to auto-install dependencies
- Check that tkinter is available (`python -c "import tkinter"`)

**Import fails:**
- Verify file format (CSV, Excel, JSON)
- Check that file isn't corrupted
- Ensure file size is under 50MB

**Printing issues:**
- Verify PDF was generated correctly
- Check printer settings for double-sided printing
- Try different card dimensions if layout looks off

### Getting Help

1. **Check the logs**: Look in `~/.flashcard_maker/logs/` for error messages
2. **Run tests**: Use `python dev.py test` to check for issues
3. **Reset settings**: Delete `~/.flashcard_maker/` folder to reset to defaults

## File Locations

- **User Data**: `~/.flashcard_maker/data/`
- **Configuration**: `~/.flashcard_maker/config.enc`
- **Logs**: `~/.flashcard_maker/logs/`
- **Backups**: `~/.flashcard_maker/data/backups/`

## Keyboard Shortcuts

- `Ctrl+N`: New flashcard set
- `Ctrl+O`: Open flashcard set
- `Ctrl+S`: Save flashcard set
- `F2`: Switch to edit mode
- `F3`: Switch to study mode
- `F1`: Show help

---

**Happy studying! 🎓**