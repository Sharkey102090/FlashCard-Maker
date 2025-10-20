"""
Main GUI Application Window
===========================

Main application window built with CustomTkinter for modern UI.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from typing import Optional, Dict, Any, List
import sys
from pathlib import Path

# Import custom modules
from ..core.models import FlashcardSet, Flashcard
from ..core.data_manager import data_manager
from ..utils.config import config
from ..utils.security import logger

# Import GUI components (will be created)
from .components.flashcard_editor import FlashcardEditor
from .components.flashcard_viewer import FlashcardViewer
from .components.settings_panel import SettingsPanel
from .components.file_manager import FileManager
from .components.print_system import print_system

class FlashcardApp:
    """Main application class."""
    
    def __init__(self):
        # Set CustomTkinter appearance
        ctk.set_appearance_mode(config.get('gui.theme', 'system'))
        ctk.set_default_color_theme("blue")
        
        # Initialize main window
        self.root = ctk.CTk()
        self.root.title(config.get('app.name', 'Flashcard Generator'))
        self.root.geometry(f"{config.get('gui.window_width', 1200)}x{config.get('gui.window_height', 800)}")
        
        # Application state
        self.current_flashcard_set: Optional[FlashcardSet] = None
        self.current_file_path: Optional[Path] = None
        self.unsaved_changes = False
        self._app_closing = False  # Track if app is already closing
        
        # GUI components
        self.flashcard_editor: Optional[FlashcardEditor] = None
        self.flashcard_viewer: Optional[FlashcardViewer] = None
        self.settings_panel: Optional[SettingsPanel] = None
        self.file_manager: Optional[FileManager] = None
        
        # Initialize GUI
        self._setup_gui()
        self._setup_menu()
        self._setup_shortcuts()
        self._setup_events()
        
        # Load last opened file if available
        self._load_last_session()
        
        logger.info("Flashcard application initialized")
    
    def _setup_gui(self):
        """Set up the main GUI layout."""
        # Configure grid weights
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create sidebar
        self.sidebar = ctk.CTkFrame(self.root, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)
        
        # Sidebar buttons
        self.logo_label = ctk.CTkLabel(
            self.sidebar, 
            text="Flashcard\nGenerator", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.new_set_button = ctk.CTkButton(
            self.sidebar, 
            text="New Set",
            command=self._new_flashcard_set
        )
        self.new_set_button.grid(row=1, column=0, padx=20, pady=10)
        
        self.open_button = ctk.CTkButton(
            self.sidebar,
            text="Open Set", 
            command=self._open_flashcard_set
        )
        self.open_button.grid(row=2, column=0, padx=20, pady=10)
        
        self.save_button = ctk.CTkButton(
            self.sidebar,
            text="Save Set",
            command=self._save_flashcard_set
        )
        self.save_button.grid(row=3, column=0, padx=20, pady=10)
        
        # Created sets dropdown (empty area in sidebar) - shows user-created/imported sets
        try:
            # Use CTkOptionMenu as a dropdown; default shows 'Created Flashcard Sets'
            self.created_sets_menu = ctk.CTkOptionMenu(
                self.sidebar,
                values=["CompTIA Security+"],
                command=lambda v: self._on_created_set_selected(v)
            )
            self.created_sets_menu.set("Created Flashcard Sets")
            self.created_sets_menu.grid(row=4, column=0, padx=20, pady=(8, 8))
        except Exception:
            # Fallback: place a button that opens CompTIA import
            self.created_sets_button = ctk.CTkButton(
                self.sidebar,
                text="CompTIA Security+",
                fg_color="#4CAF50",
                hover_color="#45A049",
                command=self._import_comptia_set
            )
            self.created_sets_button.grid(row=4, column=0, padx=20, pady=(8, 8))

        # Delete set button
        self.delete_set_button = ctk.CTkButton(
            self.sidebar,
            text="Delete Set",
            fg_color="#d9534f",
            hover_color="#c9302c",
            command=self._delete_current_set
        )
        self.delete_set_button.grid(row=4, column=0, padx=20, pady=10)
        
        # Print button
        self.print_button = ctk.CTkButton(
            self.sidebar,
            text="🖨️ Print",
            command=self._print_flashcards
        )
        self.print_button.grid(row=5, column=0, padx=20, pady=10)

        # Import Text button
        self.import_text_button = ctk.CTkButton(
            self.sidebar,
            text="Import Text",
            command=self._import_text_document
        )
        # Place import button on the next row so it doesn't overwrite the Print button
        self.import_text_button.grid(row=6, column=0, padx=20, pady=10)

        # Note: CompTIA import button moved into the Flashcard Editor controls

        # Mode selection
        self.mode_label = ctk.CTkLabel(self.sidebar, text="Mode:", font=ctk.CTkFont(size=14, weight="bold"))
        # Give some spacing above the mode label and place it after the import buttons
        self.mode_label.grid(row=8, column=0, padx=20, pady=(20, 5))
        
        self.edit_mode_button = ctk.CTkButton(
            self.sidebar,
            text="Edit Mode",
            command=self._switch_to_edit_mode
        )
        self.edit_mode_button.grid(row=9, column=0, padx=20, pady=5)
        
        self.study_mode_button = ctk.CTkButton(
            self.sidebar,
            text="Study Mode",
            command=self._switch_to_study_mode
        )
        self.study_mode_button.grid(row=10, column=0, padx=20, pady=5)

        self.settings_button = ctk.CTkButton(
            self.sidebar,
            text="Settings",
            command=self._show_settings
        )
        self.settings_button.grid(row=11, column=0, padx=20, pady=(30, 20))
        
        # Main content area
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.grid(row=0, column=1, padx=(20, 0), pady=(20, 0), sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Status bar
        self.status_frame = ctk.CTkFrame(self.root)
        self.status_frame.grid(row=1, column=1, padx=(20, 0), pady=(10, 20), sticky="ew")
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready - No flashcard set loaded",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.card_count_label = ctk.CTkLabel(
            self.status_frame,
            text="Cards: 0",
            font=ctk.CTkFont(size=12)
        )
        self.card_count_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        
        # Initialize with editor mode
        self._switch_to_edit_mode()
    
    def _setup_menu(self):
        """Set up application menu."""
        # Note: CustomTkinter doesn't have native menu support,
        # so we'll use keyboard shortcuts and buttons instead
        pass
    
    def _setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        self.root.bind('<Control-n>', lambda e: self._new_flashcard_set())
        self.root.bind('<Control-o>', lambda e: self._open_flashcard_set())
        self.root.bind('<Control-s>', lambda e: self._save_flashcard_set())
        self.root.bind('<Control-Shift-S>', lambda e: self._save_flashcard_set_as())
        self.root.bind('<Control-q>', lambda e: self._quit_application())
        self.root.bind('<F1>', lambda e: self._show_help())
        
        # Mode switching
        self.root.bind('<F2>', lambda e: self._switch_to_edit_mode())
        self.root.bind('<F3>', lambda e: self._switch_to_study_mode())
    
    def _setup_events(self):
        """Set up event handlers."""
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Track window state changes
        self.root.bind('<Configure>', self._on_window_configure)
    
    def _delete_current_set(self):
        """Delete the current flashcard set after confirmation."""
        if not self.current_flashcard_set:
            messagebox.showinfo("No set", "There is no flashcard set to delete.")
            return

        result = messagebox.askyesno(
            "Delete Flashcard Set",
            "Are you sure you want to permanently delete the current flashcard set? This action cannot be undone."
        )

        if not result:
            return

        # Clear current set and reset UI
        self.current_flashcard_set = None
        self.current_file_path = None
        self.unsaved_changes = False
        # If editor/viewer open, clear them
        # If editors/viewers are present, reset them to the empty set.
        if self.flashcard_editor is not None:
            try:
                self.flashcard_editor.set_flashcard_set(FlashcardSet())
                self.flashcard_editor._update_flashcard_list()
            except Exception:
                # Non-critical: log exception for diagnostics
                logger.error("Failed to reset flashcard editor during delete_current_set", exc_info=True)

        if self.flashcard_viewer is not None:
            try:
                self.flashcard_viewer.set_flashcard_set(FlashcardSet())
                self.flashcard_viewer._load_flashcards()
            except Exception:
                logger.error("Failed to reset flashcard viewer during delete_current_set", exc_info=True)
        

        self._update_ui()
        messagebox.showinfo("Deleted", "Current flashcard set deleted.")
    
    def _import_comptia_set(self):
        """Load the pre-saved CompTIA set created by the tools script."""
        try:
            path = Path.home() / '.flashcard_maker' / 'data' / 'comptia_security_plus.fcs'
            if not path.exists():
                messagebox.showwarning("Not found", f"CompTIA set not found at {path}")
                return

            if not self._check_unsaved_changes():
                return

            # Show progress dialog while loading/appending
            try:
                from .components.import_progress import ImportProgress
            except Exception:
                from src.gui.components.import_progress import ImportProgress

            progress = ImportProgress(self.root, title="Importing CompTIA set...")

            # Load the CompTIA set from disk (update progress)
            progress.set_progress(5, "Loading file...")
            comptia_set = data_manager.load_flashcard_set(path)

            # If there is no current set, set it directly
            if not self.current_flashcard_set:
                self.current_flashcard_set = comptia_set
            else:
                # Append all flashcards from the comptia set into the current set
                total = len(comptia_set.flashcards) or 1
                added_ids = []
                for idx, card in enumerate(comptia_set.flashcards, start=1):
                    # Check for user cancel request
                    if progress.is_cancelled():
                        break

                    self.current_flashcard_set.add_flashcard(card)
                    added_ids.append(card.id)
                    pct = 5 + int((idx / total) * 90)
                    progress.set_progress(pct, f"Adding card {idx}/{total}...")

                # If cancelled, rollback added cards
                if progress.is_cancelled() and added_ids:
                    for fid in added_ids:
                        try:
                            self.current_flashcard_set.remove_flashcard(fid)
                        except Exception:
                            # Non-critical: continue attempting to remove others
                            pass
                    progress.set_progress(100, "Cancelled")
                    progress.close()
                    self._update_status("Import cancelled")
                    messagebox.showinfo("Import cancelled", "CompTIA import was cancelled. Added cards were removed.")
                    # Refresh UI to reflect rollback
                    self._update_ui()
                    if self.flashcard_editor is not None:
                        try:
                            self.flashcard_editor.set_flashcard_set(self.current_flashcard_set)
                            self.flashcard_editor._update_flashcard_list()
                        except Exception:
                            logger.error("Failed to update flashcard editor after cancelled CompTIA import", exc_info=True)

                    if self.flashcard_viewer is not None:
                        try:
                            self.flashcard_viewer.set_flashcard_set(self.current_flashcard_set)
                            self.flashcard_viewer._load_flashcards()
                        except Exception:
                            logger.error("Failed to update flashcard viewer after cancelled CompTIA import", exc_info=True)

                    return

            progress.set_progress(100, "Done")
            progress.close()

            self.unsaved_changes = True

            # Refresh UI and open components so added cards appear in the editor/list
            self._update_ui()
            if self.flashcard_editor is not None:
                try:
                    self.flashcard_editor.set_flashcard_set(self.current_flashcard_set)
                    self.flashcard_editor._update_flashcard_list()
                except Exception:
                    logger.error("Failed to update flashcard editor after CompTIA import", exc_info=True)

            if self.flashcard_viewer is not None:
                try:
                    self.flashcard_viewer.set_flashcard_set(self.current_flashcard_set)
                    self.flashcard_viewer._load_flashcards()
                except Exception:
                    logger.error("Failed to update flashcard viewer after CompTIA import", exc_info=True)

            messagebox.showinfo("Imported", "CompTIA Security+ cards added to the current set.")
        except Exception as e:
            logger.error(f"Failed to import CompTIA set: {e}")
            messagebox.showerror("Error", f"Failed to import CompTIA set:\n{e}")
    def _load_last_session(self):
        """Load the last opened flashcard set."""
        try:
            last_file = config.get('app.last_opened_file')
            if last_file and Path(last_file).exists():
                self._load_flashcard_set(Path(last_file))
        except Exception as e:
            logger.warning(f"Failed to load last session: {e}")
    
    def _new_flashcard_set(self):
        """Create a new flashcard set."""
        if self._check_unsaved_changes():
            self.current_flashcard_set = FlashcardSet()
            self.current_file_path = None
            self.unsaved_changes = False
            self._update_ui()
            self._update_status("New flashcard set created")
            logger.info("New flashcard set created")
    
    def _open_flashcard_set(self):
        """Open an existing flashcard set."""
        if self._check_unsaved_changes():
            file_path = filedialog.askopenfilename(
                title="Open Flashcard Set",
                filetypes=[
                    ("Flashcard Sets", "*.fcs"),
                    ("JSON Files", "*.json"),
                    ("All Files", "*.*")
                ],
                defaultextension=".fcs"
            )
            
            if file_path:
                self._load_flashcard_set(Path(file_path))
    
    def _load_flashcard_set(self, file_path: Path):
        """Load flashcard set from file."""
        try:
            if file_path.suffix.lower() == '.json':
                flashcard_set = data_manager.import_from_json(file_path)
            else:
                flashcard_set = data_manager.load_flashcard_set(file_path)
            
            self.current_flashcard_set = flashcard_set
            self.current_file_path = file_path
            self.unsaved_changes = False
            
            # Save as last opened file
            config.set('app.last_opened_file', str(file_path))
            
            self._update_ui()
            self._update_status(f"Loaded: {file_path.name}")
            
            logger.info(f"Flashcard set loaded: {file_path}")
        
        except Exception as e:
            logger.error(f"Failed to load flashcard set: {e}")
            messagebox.showerror("Error", f"Failed to load flashcard set:\n{e}")
    
    def _save_flashcard_set(self):
        """Save current flashcard set."""
        if not self.current_flashcard_set:
            return
        
        if self.current_file_path:
            self._save_to_file(self.current_file_path)
        else:
            self._save_flashcard_set_as()
    
    def _save_flashcard_set_as(self):
        """Save flashcard set with new filename."""
        if not self.current_flashcard_set:
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Flashcard Set",
            filetypes=[
                ("Flashcard Sets", "*.fcs"),
                ("JSON Files", "*.json"),
                ("All Files", "*.*")
            ],
            defaultextension=".fcs"
        )
        
        if file_path:
            self._save_to_file(Path(file_path))
    
    def _save_to_file(self, file_path: Path):
        """Save flashcard set to specified file."""
        if not self.current_flashcard_set:
            return
            
        try:
            if file_path.suffix.lower() == '.json':
                data_manager.export_to_json(self.current_flashcard_set, file_path)
            else:
                data_manager.save_flashcard_set(self.current_flashcard_set, file_path.stem)
                self.current_file_path = file_path
            
            self.unsaved_changes = False
            self._update_status(f"Saved: {file_path.name}")
            
            logger.info(f"Flashcard set saved: {file_path}")
        
        except Exception as e:
            logger.error(f"Failed to save flashcard set: {e}")
            messagebox.showerror("Error", f"Failed to save flashcard set:\n{e}")
    
    def _print_flashcards(self):
        """Print current flashcard set."""
        if not self.current_flashcard_set or not self.current_flashcard_set.flashcards:
            messagebox.showwarning("Warning", "No flashcards to print. Please create or load a flashcard set first.")
            return
        
        try:
            success = print_system.show_print_dialog(self.root, self.current_flashcard_set)
            if success:
                self._update_status("Print completed successfully")
            else:
                self._update_status("Print cancelled or failed")
        except Exception as e:
            logger.error(f"Print operation failed: {e}")
            messagebox.showerror("Error", f"Print operation failed:\n{e}")
    
    def _import_text_document(self):
        """Import a text document and generate flashcards from it."""
        try:
            file_path = filedialog.askopenfilename(
                title="Import Text Document",
                filetypes=[
                    ("Text Files", "*.txt *.md"),
                    ("Word Documents", "*.docx"),
                    ("PDF Files", "*.pdf"),
                    ("All Files", "*.*")
                ]
            )
            if not file_path:
                return

            from ..utils.text_importer import load_text, generate_flashcards_from_text
            from .components.text_import_dialog import TextImportDialog

            txt = load_text(Path(file_path))
            cards = generate_flashcards_from_text(txt, strategy='paragraphs')

            if not cards:
                messagebox.showinfo("No cards found", "No flashcards could be generated from the selected document.")
                return

            # Show preview dialog
            dialog = TextImportDialog(self.root, cards)
            self.root.wait_window(dialog)

            result = getattr(dialog, 'result', None)

            if result:
                selected_indices = result
                # Ensure a flashcard set exists
                if not self.current_flashcard_set:
                    self.current_flashcard_set = FlashcardSet()

                # Show progress dialog while adding selected cards
                try:
                    from .components.import_progress import ImportProgress
                except Exception:
                    from src.gui.components.import_progress import ImportProgress

                progress = ImportProgress(self.root, title="Adding imported cards...")
                total = len(selected_indices) or 1
                added_ids = []
                for idx, sel in enumerate(selected_indices, start=1):
                    # Check for cancellation
                    if progress.is_cancelled():
                        break

                    self.current_flashcard_set.add_flashcard(cards[sel])
                    # Track added IDs for potential rollback
                    try:
                        added_ids.append(cards[sel].id)
                    except Exception:
                        pass

                    pct = int((idx / total) * 100)
                    progress.set_progress(pct, f"Adding card {idx}/{total}...")

                # If cancelled, remove added cards and notify user
                if progress.is_cancelled() and added_ids:
                    for fid in added_ids:
                        try:
                            self.current_flashcard_set.remove_flashcard(fid)
                        except Exception:
                            pass
                    progress.set_progress(100, "Cancelled")
                    progress.close()
                    self._update_status("Import cancelled")
                    messagebox.showinfo("Import cancelled", "Text import was cancelled. Added cards were removed.")
                    # Refresh UI after rollback
                    self._update_ui()
                    if self.flashcard_editor is not None:
                        try:
                            self.flashcard_editor.set_flashcard_set(self.current_flashcard_set)
                            self.flashcard_editor._update_flashcard_list()
                        except Exception:
                            logger.error("Failed to update flashcard editor after cancelled import", exc_info=True)

                    if self.flashcard_viewer is not None:
                        try:
                            self.flashcard_viewer.set_flashcard_set(self.current_flashcard_set)
                            self.flashcard_viewer._load_flashcards()
                        except Exception:
                            logger.error("Failed to update flashcard viewer after cancelled import", exc_info=True)

                    return

                progress.set_progress(100, "Done")
                progress.close()
                self.unsaved_changes = True
                # Refresh the UI and any open editors/viewers so imported cards are visible
                self._update_ui()
                if self.flashcard_editor is not None:
                    try:
                        # Replace the editor's set and refresh its list
                        self.flashcard_editor.set_flashcard_set(self.current_flashcard_set)
                        self.flashcard_editor._update_flashcard_list()
                    except Exception:
                        logger.error("Failed to update flashcard editor after import", exc_info=True)

                if self.flashcard_viewer is not None:
                    try:
                        self.flashcard_viewer.set_flashcard_set(self.current_flashcard_set)
                        self.flashcard_viewer._load_flashcards()
                    except Exception:
                        logger.error("Failed to update flashcard viewer after import", exc_info=True)
                messagebox.showinfo("Import complete", f"Added {len(selected_indices)} flashcards to the current set.")
        except Exception as e:
            logger.error(f"Text import failed: {e}")
            messagebox.showerror("Import error", f"Failed to import text document:\n{e}")
    
    def _switch_to_edit_mode(self):
        """Switch to edit mode."""
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Create flashcard editor
        self.flashcard_editor = FlashcardEditor(
            self.main_frame,
            flashcard_set=self.current_flashcard_set,
            on_change_callback=self._on_content_changed,
            on_import_comptia=self._import_comptia_set
        )
        self.flashcard_editor.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Update button states
        self.edit_mode_button.configure(state="disabled")
        self.study_mode_button.configure(state="normal")
        
        self._update_status("Edit mode active")
    
    def _switch_to_study_mode(self):
        """Switch to study mode."""
        if not self.current_flashcard_set or not self.current_flashcard_set.flashcards:
            messagebox.showwarning("Warning", "No flashcards to study. Create some flashcards first.")
            return
        
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Create flashcard viewer
        self.flashcard_viewer = FlashcardViewer(
            self.main_frame,
            flashcard_set=self.current_flashcard_set
        )
        self.flashcard_viewer.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Update button states
        self.edit_mode_button.configure(state="normal")
        self.study_mode_button.configure(state="disabled")
        
        self._update_status("Study mode active")
    
    def _show_settings(self):
        """Show settings panel."""
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("600x500")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        self.settings_panel = SettingsPanel(settings_window)
        self.settings_panel.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        settings_window.grid_columnconfigure(0, weight=1)
        settings_window.grid_rowconfigure(0, weight=1)
    
    def _show_help(self):
        """Show help dialog."""
        help_text = """
Flashcard Generator Help

Keyboard Shortcuts:
• Ctrl+N: New flashcard set
• Ctrl+O: Open flashcard set
• Ctrl+S: Save flashcard set
• Ctrl+Shift+S: Save as...
• F2: Switch to edit mode
• F3: Switch to study mode
• F1: Show this help

Mode Information:
• Edit Mode: Create and edit flashcards
• Study Mode: Review flashcards and track progress

For more information, see the documentation.
        """
        
        messagebox.showinfo("Help", help_text)
    
    def _check_unsaved_changes(self) -> bool:
        """Check for unsaved changes and prompt user."""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before continuing?"
            )
            
            if result is True:  # Yes - save
                self._save_flashcard_set()
                return True
            elif result is False:  # No - don't save
                return True
            else:  # Cancel
                return False
        
        return True
    
    def _on_content_changed(self):
        """Handle content changes."""
        self.unsaved_changes = True
        self._update_ui()
    
    def _update_ui(self):
        """Update UI elements based on current state."""
        if self.current_flashcard_set:
            card_count = len(self.current_flashcard_set.flashcards)
            self.card_count_label.configure(text=f"Cards: {card_count}")
            
            # Update window title
            title = config.get('app.name', 'Flashcard Generator')
            if self.current_file_path:
                title += f" - {self.current_file_path.name}"
            if self.unsaved_changes:
                title += " *"
            
            self.root.title(title)
        else:
            self.card_count_label.configure(text="Cards: 0")
            self.root.title(config.get('app.name', 'Flashcard Generator'))
    
    def _update_status(self, message: str):
        """Update status bar message."""
        self.status_label.configure(text=message)
        
        # Clear status after 3 seconds
        self.root.after(3000, lambda: self.status_label.configure(text="Ready"))

    def _on_created_set_selected(self, value):
        if not value:
            return
        if value == "CompTIA Security+":
            self._import_comptia_set()
        # if using CTkOptionMenu, optionally reset the display to placeholder or first value:
        try:
            # set to a neutral display if needed (or keep the selected value)
            # self.created_sets_menu.set("CompTIA Security+")
            pass
        except Exception:
            pass
    
    def _on_window_configure(self, event):
        """Handle window configuration changes."""
        if event.widget == self.root:
            # Save window dimensions
            config.set('gui.window_width', self.root.winfo_width())
            config.set('gui.window_height', self.root.winfo_height())
    
    def _on_closing(self):
        """Handle application closing."""
        if self._check_unsaved_changes():
            self._quit_application()
    
    def _quit_application(self):
        """Quit the application."""
        if self._app_closing:
            return  # Already in the process of closing
        
        self._app_closing = True
        logger.info("Application closing")
        
        try:
            if self.root.winfo_exists():
                self.root.quit()
                self.root.destroy()
        except tk.TclError:
            # Window already destroyed, ignore
            pass
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
    
    def run(self):
        """Start the application."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Application error: {e}")
            try:
                messagebox.showerror("Application Error", f"An unexpected error occurred:\n{e}")
            except:
                pass  # GUI might not be available for error dialog
        finally:
            # Only quit if not already closing
            if not self._app_closing:
                self._quit_application()