"""
Flashcard Editor Component
==========================

Rich text editor for creating and editing flashcards.
"""

import tkinter as tk
from tkinter import messagebox, filedialog, colorchooser
import customtkinter as ctk
from typing import Optional, Callable, List, Dict, Any
import base64
from PIL import Image, ImageTk
from pathlib import Path
import re

from ...core.models import FlashcardSet, Flashcard, InputValidator
from ...utils.security import logger
from ...utils.config import config

class RichTextEditor(ctk.CTkFrame):
    """Rich text editor with formatting controls."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.current_text_widget = None
        self.image_references = []  # Store image references to prevent garbage collection
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the rich text editor UI."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Toolbar
        self.toolbar = ctk.CTkFrame(self)
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Formatting buttons
        self.bold_button = ctk.CTkButton(
            self.toolbar, text="B", width=30, height=30,
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self._apply_format("bold")
        )
        self.bold_button.grid(row=0, column=0, padx=2, pady=2)
        
        self.italic_button = ctk.CTkButton(
            self.toolbar, text="I", width=30, height=30,
            font=ctk.CTkFont(slant="italic"),
            command=lambda: self._apply_format("italic")
        )
        self.italic_button.grid(row=0, column=1, padx=2, pady=2)
        
        self.underline_button = ctk.CTkButton(
            self.toolbar, text="U", width=30, height=30,
            font=ctk.CTkFont(underline=True),
            command=lambda: self._apply_format("underline")
        )
        self.underline_button.grid(row=0, column=2, padx=2, pady=2)
        
        # Font size
        self.font_size_var = tk.StringVar(value="12")
        self.font_size_combo = ctk.CTkComboBox(
            self.toolbar,
            values=["8", "10", "12", "14", "16", "18", "20", "24"],
            width=60,
            variable=self.font_size_var,
            command=self._change_font_size
        )
        self.font_size_combo.grid(row=0, column=3, padx=2, pady=2)
        
        # Color button
        self.color_button = ctk.CTkButton(
            self.toolbar, text="Color", width=60, height=30,
            command=self._choose_color
        )
        self.color_button.grid(row=0, column=4, padx=2, pady=2)
        
        # Image button
        self.image_button = ctk.CTkButton(
            self.toolbar, text="Image", width=60, height=30,
            command=self._insert_image
        )
        self.image_button.grid(row=0, column=5, padx=2, pady=2)
        
        # Text area with scrollbar
        self.text_frame = ctk.CTkFrame(self)
        self.text_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.text_frame.grid_columnconfigure(0, weight=1)
        self.text_frame.grid_rowconfigure(0, weight=1)
        
        self.text_widget = tk.Text(
            self.text_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 12),
            bg="#212121" if config.get('gui.theme') == 'dark' else "#ffffff",
            fg="#ffffff" if config.get('gui.theme') == 'dark' else "#000000",
            insertbackground="#ffffff" if config.get('gui.theme') == 'dark' else "#000000",
            selectbackground="#1f538d",
            relief=tk.FLAT,
            borderwidth=0
        )
        self.text_widget.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Scrollbar
        self.scrollbar = ctk.CTkScrollbar(self.text_frame, command=self.text_widget.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns", pady=10)
        self.text_widget.configure(yscrollcommand=self.scrollbar.set)
        
        # Bind events
        self.text_widget.bind('<KeyRelease>', self._on_text_change)
        self.text_widget.bind('<Button-1>', self._on_text_click)
        
        self.current_text_widget = self.text_widget
    
    def _apply_format(self, format_type: str):
        """Apply formatting to selected text."""
        if not self.current_text_widget:
            return
            
        try:
            # Get current selection
            start = self.current_text_widget.index(tk.SEL_FIRST)
            end = self.current_text_widget.index(tk.SEL_LAST)
            
            # Create or get tag
            tag_name = f"{format_type}_{start}_{end}"
            
            if format_type == "bold":
                self.current_text_widget.tag_configure(tag_name, font=("Segoe UI", 12, "bold"))
            elif format_type == "italic":
                self.current_text_widget.tag_configure(tag_name, font=("Segoe UI", 12, "italic"))
            elif format_type == "underline":
                self.current_text_widget.tag_configure(tag_name, underline=True)
            
            # Apply tag
            self.current_text_widget.tag_add(tag_name, start, end)
            
        except tk.TclError:
            # No selection
            pass
    
    def _change_font_size(self, size: str):
        """Change font size for selected text."""
        if not self.current_text_widget:
            return
            
        try:
            start = self.current_text_widget.index(tk.SEL_FIRST)
            end = self.current_text_widget.index(tk.SEL_LAST)
            
            tag_name = f"size_{size}_{start}_{end}"
            self.current_text_widget.tag_configure(tag_name, font=("Segoe UI", int(size)))
            self.current_text_widget.tag_add(tag_name, start, end)
            
        except (tk.TclError, ValueError):
            pass
    
    def _choose_color(self):
        """Choose text color."""
        color = colorchooser.askcolor(title="Choose Text Color")[1]
        if color and self.current_text_widget:
            try:
                start = self.current_text_widget.index(tk.SEL_FIRST)
                end = self.current_text_widget.index(tk.SEL_LAST)
                
                tag_name = f"color_{color}_{start}_{end}"
                self.current_text_widget.tag_configure(tag_name, foreground=color)
                self.current_text_widget.tag_add(tag_name, start, end)
                
            except tk.TclError:
                pass
    
    def _insert_image(self):
        """Insert image into text."""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path and self.current_text_widget:
            try:
                # Validate file size
                max_size = config.get('security.max_file_size', 50 * 1024 * 1024)
                if Path(file_path).stat().st_size > max_size:
                    messagebox.showerror("Error", f"Image file too large. Maximum size: {max_size // (1024*1024)}MB")
                    return
                
                # Load and resize image
                image = Image.open(file_path)
                
                # Resize if too large
                max_width, max_height = 400, 300
                if image.width > max_width or image.height > max_height:
                    image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(image)
                
                # Insert image
                self.current_text_widget.image_create(tk.INSERT, image=photo)
                
                # Keep a reference to prevent garbage collection
                self.image_references.append(photo)
                
            except Exception as e:
                logger.error(f"Failed to insert image: {e}")
                messagebox.showerror("Error", f"Failed to insert image: {e}")
    
    def _on_text_change(self, event):
        """Handle text change events."""
        # This can be overridden by parent components
        pass

    
    def _on_text_click(self, event):
        """Handle text click events."""
        self.current_text_widget = event.widget
    
    def get_content(self) -> str:
        """Get the text content."""
        if self.current_text_widget:
            return self.current_text_widget.get("1.0", tk.END).strip()
        return ""
    
    def set_content(self, content: str):
        """Set the text content."""
        if self.current_text_widget:
            self.current_text_widget.delete("1.0", tk.END)
            self.current_text_widget.insert("1.0", content)
    
    def clear(self):
        """Clear all content."""
        if self.current_text_widget:
            self.current_text_widget.delete("1.0", tk.END)
            self.image_references.clear()  # Clear image references

class FlashcardEditor(ctk.CTkFrame):
    """Main flashcard editor component."""

    def __init__(self, parent, flashcard_set: Optional[FlashcardSet] = None,
                 on_change_callback: Optional[Callable] = None,
                 on_import_comptia: Optional[Callable] = None,
                 **kwargs):
        super().__init__(parent, **kwargs)

        self.flashcard_set = flashcard_set or FlashcardSet()
        self.on_change_callback = on_change_callback
        # Optional callback provided by parent to trigger CompTIA import
        self.on_import_comptia = on_import_comptia
        self.current_flashcard: Optional[Flashcard] = None
        self.current_index = 0

        self._setup_ui()
        self._update_flashcard_list()

        if self.flashcard_set.flashcards:
            self._select_flashcard(0)
    
    def _setup_ui(self):
        """Set up the editor UI."""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Left panel - Flashcard list
        # Increase width and allow the frame to propagate size so controls don't get cut off
        self.left_panel = ctk.CTkFrame(self, width=320)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=6)
        # Allow geometry propagation so children layout can determine size
        try:
            self.left_panel.grid_propagate(True)
        except Exception:
            # Some CTk versions may not support grid_propagate in the same way; ignore
            pass
        self.left_panel.grid_rowconfigure(2, weight=1)
        
        # List header
        self.list_header = ctk.CTkLabel(
            self.left_panel,
            text="Flashcards",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.list_header.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        
        # List controls
        self.controls_frame = ctk.CTkFrame(self.left_panel)
        # Add slightly larger vertical padding so buttons aren't close to the header edge
        self.controls_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(8, 6))
        self.controls_frame.grid_columnconfigure(0, weight=1)
        self.controls_frame.grid_columnconfigure(1, weight=1)
        self.controls_frame.grid_columnconfigure(2, weight=1)
        
        self.add_button = ctk.CTkButton(
            self.controls_frame,
            text="Add",
            command=self._add_flashcard,
            height=34,
            width=120
        )
        # Give more horizontal padding so the button text is clearly visible
        self.add_button.grid(row=0, column=0, padx=(0, 6), pady=4, sticky="ew")
        
        # Unified Delete button: deletes current card or all selected cards if checkboxes are used
        self.delete_button = ctk.CTkButton(
            self.controls_frame,
            text="Delete",
            command=self._delete_button_action,
            height=34,
            width=140,
            fg_color="red",
            hover_color="darkred"
        )
        self.delete_button.grid(row=0, column=1, padx=(6, 0), pady=4, sticky="ew")

        # (CompTIA import button moved to sidebar 'Created Flashcard Sets' menu)

        # Track selected flashcards by id
        self._selected_for_deletion = set()
        
        # Select All checkbox
        self.select_all_var = tk.BooleanVar(value=False)
        self.select_all_chk = ctk.CTkCheckBox(
            self.controls_frame,
            text="Select All",
            variable=self.select_all_var,
            command=self._toggle_select_all
        )
        # Place select-all to the right of the add/delete buttons
        self.select_all_chk.grid(row=1, column=0, columnspan=2, padx=10, pady=(4, 0), sticky='w')
        
        # Flashcard list
        self.list_frame = ctk.CTkScrollableFrame(self.left_panel)
        # Provide extra bottom padding so last items and controls are not clipped
        self.list_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=(6, 12))
        self.list_frame.grid_columnconfigure(0, weight=1)
        
        # Search box
        self.search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(
            self.left_panel,
            placeholder_text="Search flashcards...",
            textvariable=self.search_var
        )
        self.search_entry.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.search_var.trace("w", self._on_search_change)
        
        # Right panel - Editor
        self.right_panel = ctk.CTkFrame(self)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        # Make the front and back editor areas (rows 2 and 4) expand equally
        # Keep label rows (1 and 3) with weight 0 so they don't take extra space
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=0)
        self.right_panel.grid_rowconfigure(2, weight=1)
        self.right_panel.grid_rowconfigure(3, weight=0)
        self.right_panel.grid_rowconfigure(4, weight=1)
        
        # Editor header
        self.editor_header = ctk.CTkLabel(
            self.right_panel,
            text="Flashcard Editor",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.editor_header.grid(row=0, column=0, padx=20, pady=10)
        
        # Front side editor
        self.front_label = ctk.CTkLabel(
            self.right_panel,
            text="Front Side:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.front_label.grid(row=1, column=0, padx=20, pady=(10, 5), sticky="w")
        
        self.front_editor = RichTextEditor(self.right_panel)
        self.front_editor.grid(row=2, column=0, sticky="nsew", padx=20, pady=5)
        self.front_editor._on_text_change = lambda event: self._on_content_change()
        
        # Back side editor
        self.back_label = ctk.CTkLabel(
            self.right_panel,
            text="Back Side:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.back_label.grid(row=3, column=0, padx=20, pady=(10, 5), sticky="w")
        
        self.back_editor = RichTextEditor(self.right_panel)
        self.back_editor.grid(row=4, column=0, sticky="nsew", padx=20, pady=5)
        self.back_editor._on_text_change = lambda event: self._on_content_change()
        
        # Metadata section
        self.metadata_frame = ctk.CTkFrame(self.right_panel)
        self.metadata_frame.grid(row=5, column=0, sticky="ew", padx=20, pady=10)
        self.metadata_frame.grid_columnconfigure(1, weight=1)
        
        # Category
        self.category_label = ctk.CTkLabel(self.metadata_frame, text="Category:")
        self.category_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.category_var = tk.StringVar()
        self.category_entry = ctk.CTkEntry(
            self.metadata_frame,
            textvariable=self.category_var
        )
        self.category_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.category_var.trace("w", lambda *args: self._on_content_change())
        
        # Tags
        self.tags_label = ctk.CTkLabel(self.metadata_frame, text="Tags:")
        self.tags_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.tags_var = tk.StringVar()
        self.tags_entry = ctk.CTkEntry(
            self.metadata_frame,
            textvariable=self.tags_var,
            placeholder_text="Enter tags separated by commas"
        )
        self.tags_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.tags_var.trace("w", lambda *args: self._on_content_change())
        
        # Statistics (read-only)
        self.stats_frame = ctk.CTkFrame(self.right_panel)
        self.stats_frame.grid(row=6, column=0, sticky="ew", padx=20, pady=(0, 10))
        
        self.stats_label = ctk.CTkLabel(
            self.stats_frame,
            text="Statistics: Not studied yet",
            font=ctk.CTkFont(size=12)
        )
        self.stats_label.grid(row=0, column=0, padx=10, pady=5)
        
        # Auto-save timer
        self._auto_save_timer = None
    
    def _update_flashcard_list(self):
        """Update the flashcard list display."""
        # Clear existing items
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        
        # Get search query
        search_query = self.search_var.get().lower().strip()
        
        # Filter flashcards
        if search_query:
            filtered_cards = self.flashcard_set.search_flashcards(search_query)
        else:
            filtered_cards = self.flashcard_set.flashcards
        
        # Add flashcard items
        for i, flashcard in enumerate(filtered_cards):
            self._create_flashcard_item(i, flashcard)
    
    def _create_flashcard_item(self, index: int, flashcard: Flashcard):
        """Create a flashcard list item."""
        # Create item frame
        item_frame = ctk.CTkFrame(self.list_frame)
        item_frame.grid(row=index, column=0, sticky="ew", padx=5, pady=2)
        item_frame.grid_columnconfigure(0, weight=1)
        item_frame.grid_columnconfigure(1, weight=0)
        
        # Truncate front text for display
        display_text = flashcard.front_text[:50]
        if len(flashcard.front_text) > 50:
            display_text += "..."
        
        # Remove HTML tags for display
        display_text = re.sub(r'<[^>]+>', '', display_text)
        
        # Create clickable label
        item_button = ctk.CTkButton(
            item_frame,
            text=display_text,
            command=lambda idx=index: self._select_flashcard(idx),
            height=40,
            anchor="w"
        )
        item_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # Checkbox for selecting this card for bulk deletion
        var = tk.BooleanVar(value=False)
        # If select all is active, set checkbox initially checked
        if getattr(self, 'select_all_var', None) and self.select_all_var.get():
            var.set(True)
            self._selected_for_deletion.add(flashcard.id)

        chk = ctk.CTkCheckBox(item_frame, variable=var, command=lambda v=var, fid=flashcard.id: self._on_checkbox_toggle(v, fid))
        chk.grid(row=0, column=1, padx=5, pady=5, sticky='e')
        
        # Study stats
        if flashcard.metadata.times_studied > 0:
            stats_text = f"Studied: {flashcard.metadata.times_studied} times, {flashcard.metadata.accuracy:.0f}% accuracy"
        else:
            stats_text = "Not studied yet"
        
        stats_label = ctk.CTkLabel(
            item_frame,
            text=stats_text,
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        stats_label.grid(row=1, column=0, padx=5, pady=(0, 5))

    def _on_checkbox_toggle(self, var: tk.BooleanVar, flashcard_id: str):
        """Handle checkbox toggle for selecting flashcards for deletion."""
        try:
            if var.get():
                self._selected_for_deletion.add(flashcard_id)
            else:
                self._selected_for_deletion.discard(flashcard_id)
            # Update delete button label when selection changes
            self._update_delete_button_label()
        except Exception:
            pass

    def _toggle_select_all(self):
        """Toggle select all/deselect all checkboxes in the list."""
        try:
            select_all = self.select_all_var.get()
            # Update internal set
            if select_all:
                for f in self.flashcard_set.flashcards:
                    self._selected_for_deletion.add(f.id)
        except Exception:
            pass

    def _on_comptia_import(self):
        """Invoke the parent-provided CompTIA import callback if available."""
        cb = getattr(self, 'on_import_comptia', None)
        try:
            if callable(cb):
                cb()
            else:
                messagebox.showinfo("CompTIA Import", "No import handler is configured.")
        except Exception as e:
            logger.error(f"CompTIA import handler failed: {e}", exc_info=True)
            try:
                messagebox.showerror("Import Error", f"Failed to start CompTIA import:\n{e}")
            except Exception:
                pass
        finally:
            # Always refresh list and delete button label in case state changed
            try:
                if getattr(self, '_selected_for_deletion', None):
                    # Keep selection state consistent
                    pass
            except Exception:
                pass
            try:
                self._update_flashcard_list()
            except Exception:
                pass
            try:
                self._update_delete_button_label()
            except Exception:
                pass

    def _update_delete_button_label(self):
        """Update the Delete button's label based on selected count."""
        try:
            count = len(self._selected_for_deletion) if getattr(self, '_selected_for_deletion', None) else 0
            if count > 0:
                self.delete_button.configure(text=f"Delete ({count})")
            else:
                self.delete_button.configure(text="Delete")
        except Exception:
            pass

    def _delete_button_action(self):
        """Unified delete action: delete selected checkboxes if any, otherwise delete current card."""
        # If any cards checked, delete them
        if getattr(self, '_selected_for_deletion', None) and len(self._selected_for_deletion) > 0:
            self._delete_selected_flashcards()
            return

        # Otherwise delete the currently selected card
        self._delete_flashcard()

    def _delete_selected_flashcards(self):
        """Delete flashcards that were selected via checkboxes."""
        if not self._selected_for_deletion:
            messagebox.showinfo("No selection", "No flashcards selected for deletion.")
            return

        result = messagebox.askyesno("Confirm Delete", f"Delete {len(self._selected_for_deletion)} selected flashcards?")
        if not result:
            return

        # Remove flashcards by id
        for fid in list(self._selected_for_deletion):
            try:
                self.flashcard_set.remove_flashcard(fid)
            except Exception:
                pass

        self._selected_for_deletion.clear()
        self._update_flashcard_list()
        self._clear_editors()
        if self.on_change_callback:
            self.on_change_callback()
        logger.info("Selected flashcards deleted")
    
    def _select_flashcard(self, index: int):
        """Select a flashcard for editing."""
        if 0 <= index < len(self.flashcard_set.flashcards):
            # Save current flashcard first
            self._save_current_flashcard()
            
            self.current_index = index
            self.current_flashcard = self.flashcard_set.flashcards[index]
            self._load_flashcard_content()
    
    def _load_flashcard_content(self):
        """Load flashcard content into editors."""
        if not self.current_flashcard:
            return
        
        # Load content
        self.front_editor.set_content(self.current_flashcard.front_text)
        self.back_editor.set_content(self.current_flashcard.back_text)
        
        # Load metadata
        self.category_var.set(self.current_flashcard.category)
        self.tags_var.set(", ".join(self.current_flashcard.tags))
        
        # Update statistics
        self._update_statistics_display()
    
    def _save_current_flashcard(self):
        """Save the current flashcard content."""
        if not self.current_flashcard:
            return
        
        try:
            # Get content from editors
            front_content = self.front_editor.get_content()
            back_content = self.back_editor.get_content()
            
            # Validate content
            front_content = InputValidator.sanitize_html(front_content)
            back_content = InputValidator.sanitize_html(back_content)
            
            # Update flashcard
            self.current_flashcard.update_content(front_content, back_content)
            self.current_flashcard.category = InputValidator.sanitize_text(self.category_var.get())
            
            # Update tags
            tags_text = self.tags_var.get()
            if tags_text:
                tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
                self.current_flashcard.tags = []
                for tag in tags:
                    self.current_flashcard.add_tag(tag)
            else:
                self.current_flashcard.tags = []
            
            logger.debug(f"Flashcard saved: {self.current_flashcard.id}")
        
        except Exception as e:
            logger.error(f"Failed to save flashcard: {e}")
            messagebox.showerror("Error", f"Failed to save flashcard: {e}")
    
    def _add_flashcard(self):
        """Add a new flashcard."""
        new_flashcard = Flashcard(
            front_text="New Flashcard Front",
            back_text="New Flashcard Back"
        )
        
        self.flashcard_set.add_flashcard(new_flashcard)
        self._update_flashcard_list()
        
        # Select the new flashcard
        new_index = len(self.flashcard_set.flashcards) - 1
        self._select_flashcard(new_index)
        
        self._on_content_change()
        logger.info("New flashcard added")
    
    def _delete_flashcard(self):
        """Delete the current flashcard."""
        if not self.current_flashcard:
            return
        
        result = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this flashcard?"
        )
        
        if result:
            self.flashcard_set.remove_flashcard(self.current_flashcard.id)
            
            # Update UI
            self._update_flashcard_list()
            
            # Select another flashcard
            if self.flashcard_set.flashcards:
                new_index = min(self.current_index, len(self.flashcard_set.flashcards) - 1)
                self._select_flashcard(new_index)
            else:
                self.current_flashcard = None
                self.current_index = 0
                self._clear_editors()
            
            self._on_content_change()
            logger.info("Flashcard deleted")
    
    def _clear_editors(self):
        """Clear all editors."""
        self.front_editor.clear()
        self.back_editor.clear()
        self.category_var.set("")
        self.tags_var.set("")
        self.stats_label.configure(text="No flashcard selected")
    
    def _on_search_change(self, *args):
        """Handle search query changes."""
        self._update_flashcard_list()
    
    def _on_content_change(self):
        """Handle content changes."""
        # Cancel previous auto-save timer
        if self._auto_save_timer:
            self.after_cancel(self._auto_save_timer)
        
        # Set new auto-save timer (3 seconds)
        self._auto_save_timer = self.after(3000, self._auto_save)
        
        # Notify parent of changes
        if self.on_change_callback:
            self.on_change_callback()
    
    def _auto_save(self):
        """Auto-save current flashcard."""
        self._save_current_flashcard()
        self._auto_save_timer = None
    
    def _update_statistics_display(self):
        """Update the statistics display."""
        if not self.current_flashcard:
            return
        
        metadata = self.current_flashcard.metadata
        if metadata.times_studied > 0:
            stats_text = (
                f"Studied: {metadata.times_studied} times | "
                f"Accuracy: {metadata.accuracy:.1f}% | "
                f"Difficulty: {metadata.difficulty_rating:.1f}"
            )
        else:
            stats_text = "Not studied yet"
        
        self.stats_label.configure(text=stats_text)
    
    def get_flashcard_set(self) -> FlashcardSet:
        """Get the current flashcard set."""
        # Save current flashcard before returning
        self._save_current_flashcard()
        return self.flashcard_set
    
    def set_flashcard_set(self, flashcard_set: FlashcardSet):
        """Set a new flashcard set."""
        self.flashcard_set = flashcard_set
        self.current_flashcard = None
        self.current_index = 0
        
        self._update_flashcard_list()
        
        if self.flashcard_set.flashcards:
            self._select_flashcard(0)
        else:
            self._clear_editors()