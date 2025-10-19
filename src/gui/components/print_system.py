"""
Enhanced Print System with GUI
===============================

Advanced printing system with one-sided and two-sided printing support,
print dialog, and enhanced PDF generation options.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import customtkinter as ctk
from typing import List, Dict, Any, Optional, Callable
import subprocess
import sys
import tempfile
import os
from pathlib import Path

from ...utils.pdf_generator import PDFPrintManager
from ...core.models import FlashcardSet, Flashcard
from ...utils.config import config
from ...utils.security import logger

class PrintDialog(ctk.CTkToplevel):
    """Advanced print dialog with comprehensive options."""
    
    def __init__(self, parent, flashcard_set: FlashcardSet, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.flashcard_set = flashcard_set
        self.result = None
        
        # Window setup
        self.title("Print Flashcards")
        self.geometry("600x700")
        self.transient(parent)
        self.grab_set()
        
        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"600x700+{x}+{y}")
        
        self._create_widgets()
        self._load_settings()
    
    def _create_widgets(self):
        """Create print dialog widgets."""
        # Main container with scrolling
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="🖨️ Print Flashcards",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Print Layout Section
        layout_frame = ctk.CTkFrame(main_frame)
        layout_frame.pack(fill="x", pady=(0, 15))
        
        layout_title = ctk.CTkLabel(
            layout_frame,
            text="📋 Print Layout",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        layout_title.pack(pady=(15, 10))
        
        # Print mode selection
        self.print_mode_var = tk.StringVar(value="one_sided")        
        mode_frame = ctk.CTkFrame(layout_frame)
        mode_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        mode_label = ctk.CTkLabel(mode_frame, text="Print Mode:")
        mode_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.one_sided_radio = ctk.CTkRadioButton(
            mode_frame,
            text="📄 One-Sided (Front only)",
            variable=self.print_mode_var,
            value="one_sided"
        )
        self.one_sided_radio.pack(anchor="w", padx=20, pady=2)
        
        self.two_sided_radio = ctk.CTkRadioButton(
            mode_frame,
            text="📑 Two-Sided (Front and Back)",
            variable=self.print_mode_var,
            value="two_sided"
        )
        self.two_sided_radio.pack(anchor="w", padx=20, pady=2)
        
        self.double_sided_radio = ctk.CTkRadioButton(
            mode_frame,
            text="🔄 Double-Sided (Duplex)",
            variable=self.print_mode_var,
            value="double_sided"
        )
        self.double_sided_radio.pack(anchor="w", padx=20, pady=(2, 10))
        
        # Card Selection Section
        selection_frame = ctk.CTkFrame(main_frame)
        selection_frame.pack(fill="x", pady=(0, 15))
        
        selection_title = ctk.CTkLabel(
            selection_frame,
            text="🎯 Card Selection",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        selection_title.pack(pady=(15, 10))
        
        # Selection options
        self.selection_var = tk.StringVar(value="all")        
        selection_options_frame = ctk.CTkFrame(selection_frame)
        selection_options_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.all_cards_radio = ctk.CTkRadioButton(
            selection_options_frame,
            text=f"📚 All Cards ({len(self.flashcard_set.flashcards)} cards)",
            variable=self.selection_var,
            value="all"
        )
        self.all_cards_radio.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.range_radio = ctk.CTkRadioButton(
            selection_options_frame,
            text="📊 Custom Range",
            variable=self.selection_var,
            value="range"
        )
        self.range_radio.pack(anchor="w", padx=10, pady=5)
        
        # Range selection
        range_frame = ctk.CTkFrame(selection_options_frame)
        range_frame.pack(fill="x", padx=30, pady=(5, 10))
        
        range_label = ctk.CTkLabel(range_frame, text="Range:")
        range_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.start_var = tk.StringVar(value="1")
        start_entry = ctk.CTkEntry(range_frame, textvariable=self.start_var, width=60)
        start_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(range_frame, text="to").grid(row=0, column=2, padx=5, pady=5)
        
        self.end_var = tk.StringVar(value=str(len(self.flashcard_set.flashcards)))
        end_entry = ctk.CTkEntry(range_frame, textvariable=self.end_var, width=60)
        end_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Page Layout Section
        page_frame = ctk.CTkFrame(main_frame)
        page_frame.pack(fill="x", pady=(0, 15))
        
        page_title = ctk.CTkLabel(
            page_frame,
            text="📏 Page Layout",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        page_title.pack(pady=(15, 10))
        
        # Layout options
        layout_options_frame = ctk.CTkFrame(page_frame)
        layout_options_frame.pack(fill="x", padx=20, pady=(0, 15))
        layout_options_frame.grid_columnconfigure(1, weight=1)
        
        # Paper size
        ctk.CTkLabel(layout_options_frame, text="Paper Size:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.paper_size_var = tk.StringVar(value="letter")
        paper_combo = ctk.CTkComboBox(
            layout_options_frame,
            variable=self.paper_size_var,
            values=["letter", "a4", "legal"],
            state="readonly"
        )
        paper_combo.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # Cards per row
        ctk.CTkLabel(layout_options_frame, text="Cards per Row:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.cards_per_row_var = tk.StringVar(value="2")
        row_entry = ctk.CTkEntry(layout_options_frame, textvariable=self.cards_per_row_var, width=100)
        row_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        # Cards per column
        ctk.CTkLabel(layout_options_frame, text="Cards per Column:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.cards_per_column_var = tk.StringVar(value="3")
        col_entry = ctk.CTkEntry(layout_options_frame, textvariable=self.cards_per_column_var, width=100)
        col_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        # Margins
        ctk.CTkLabel(layout_options_frame, text="Margin (inches):").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.margin_var = tk.StringVar(value="0.5")
        margin_entry = ctk.CTkEntry(layout_options_frame, textvariable=self.margin_var, width=100)
        margin_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        
        # Style Section
        style_frame = ctk.CTkFrame(main_frame)
        style_frame.pack(fill="x", pady=(0, 15))
        
        style_title = ctk.CTkLabel(
            style_frame,
            text="🎨 Style Options",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        style_title.pack(pady=(15, 10))
        
        # Style options
        style_options_frame = ctk.CTkFrame(style_frame)
        style_options_frame.pack(fill="x", padx=20, pady=(0, 15))
        style_options_frame.grid_columnconfigure(1, weight=1)
        
        # Font size
        ctk.CTkLabel(style_options_frame, text="Font Size:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.font_size_var = tk.StringVar(value="12")
        font_size_entry = ctk.CTkEntry(style_options_frame, textvariable=self.font_size_var, width=100)
        font_size_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Include borders
        self.include_borders_var = tk.BooleanVar(value=True)
        borders_check = ctk.CTkCheckBox(
            style_options_frame,
            text="Include card borders",
            variable=self.include_borders_var
        )
        borders_check.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        # Include headers
        self.include_headers_var = tk.BooleanVar(value=True)
        headers_check = ctk.CTkCheckBox(
            style_options_frame,
            text="Include front/back labels",
            variable=self.include_headers_var
        )
        headers_check.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        # Output Section
        output_frame = ctk.CTkFrame(main_frame)
        output_frame.pack(fill="x", pady=(0, 15))
        
        output_title = ctk.CTkLabel(
            output_frame,
            text="💾 Output Options",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        output_title.pack(pady=(15, 10))
        
        # Output options
        output_options_frame = ctk.CTkFrame(output_frame)
        output_options_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.output_action_var = tk.StringVar(value="preview")
        
        self.preview_radio = ctk.CTkRadioButton(
            output_options_frame,
            text="👁️ Preview PDF (Open in viewer)",
            variable=self.output_action_var,
            value="preview"
        )
        self.preview_radio.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.save_radio = ctk.CTkRadioButton(
            output_options_frame,
            text="💾 Save PDF to file",
            variable=self.output_action_var,
            value="save"
        )
        self.save_radio.pack(anchor="w", padx=10, pady=5)
        
        self.print_radio = ctk.CTkRadioButton(
            output_options_frame,
            text="🖨️ Send directly to printer",
            variable=self.output_action_var,
            value="print"
        )
        self.print_radio.pack(anchor="w", padx=10, pady=(5, 10))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(15, 0))
        
        buttons_container = ctk.CTkFrame(button_frame)
        buttons_container.pack(pady=15)
        
        cancel_button = ctk.CTkButton(
            buttons_container,
            text="Cancel",
            command=self._cancel,
            width=100
        )
        cancel_button.grid(row=0, column=0, padx=10, pady=10)
        
        preview_button = ctk.CTkButton(
            buttons_container,
            text="Preview",
            command=self._preview,
            width=100
        )
        preview_button.grid(row=0, column=1, padx=10, pady=10)
        
        print_button = ctk.CTkButton(
            buttons_container,
            text="Print",
            command=self._print,
            width=100,
            fg_color="green"
        )
        print_button.grid(row=0, column=2, padx=10, pady=10)
    
    def _load_settings(self):
        """Load settings from configuration."""
        try:
            self.paper_size_var.set(config.get('printing.paper_size', 'letter'))
            self.cards_per_row_var.set(str(config.get('printing.cards_per_row', 2)))
            self.cards_per_column_var.set(str(config.get('printing.cards_per_column', 3)))
            self.margin_var.set(str(config.get('printing.margin', 0.5)))
            self.font_size_var.set(str(config.get('printing.font_size', 12)))
        except Exception as e:
            logger.warning(f"Failed to load print settings: {e}")
    
    def _save_settings(self):
        """Save current settings to configuration."""
        try:
            config.set('printing.paper_size', self.paper_size_var.get())
            config.set('printing.cards_per_row', int(self.cards_per_row_var.get()))
            config.set('printing.cards_per_column', int(self.cards_per_column_var.get()))
            config.set('printing.margin', float(self.margin_var.get()))
            config.set('printing.font_size', int(self.font_size_var.get()))
        except Exception as e:
            logger.warning(f"Failed to save print settings: {e}")
    
    def _get_print_options(self) -> Dict[str, Any]:
        """Get current print options."""
        try:
            # Get card selection
            if self.selection_var.get() == "all":
                start_idx = 0
                end_idx = len(self.flashcard_set.flashcards)
            else:
                start_idx = max(0, int(self.start_var.get()) - 1)
                end_idx = min(len(self.flashcard_set.flashcards), int(self.end_var.get()))
            
            return {
                'print_mode': self.print_mode_var.get(),
                'selection': self.selection_var.get(),
                'start_index': start_idx,
                'end_index': end_idx,
                'paper_size': self.paper_size_var.get(),
                'cards_per_row': int(self.cards_per_row_var.get()),
                'cards_per_column': int(self.cards_per_column_var.get()),
                'margin': float(self.margin_var.get()),
                'font_size': int(self.font_size_var.get()),
                'include_borders': self.include_borders_var.get(),
                'include_headers': self.include_headers_var.get(),
                'output_action': self.output_action_var.get()
            }
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input values: {e}")
            return {}
    
    def _preview(self):
        """Preview the print output."""
        options = self._get_print_options()
        if options:
            options['output_action'] = 'preview'
            self.result = options
            self._save_settings()
            self.destroy()
    
    def _print(self):
        """Confirm print action."""
        options = self._get_print_options()
        if options:
            self.result = options
            self._save_settings()
            self.destroy()
    
    def _cancel(self):
        """Cancel the print dialog."""
        self.result = None
        self.destroy()

class EnhancedPrintSystem:
    """Enhanced print system with GUI integration."""
    
    def __init__(self):
        self.pdf_manager = PDFPrintManager()
    
    def show_print_dialog(self, parent, flashcard_set: FlashcardSet) -> bool:
        """Show print dialog and handle printing."""
        if not flashcard_set or not flashcard_set.flashcards:
            messagebox.showwarning("Warning", "No flashcards to print.")
            return False
        
        dialog = PrintDialog(parent, flashcard_set)
        parent.wait_window(dialog)
        
        if dialog.result:
            return self._handle_print_request(dialog.result, flashcard_set)
        
        return False
    
    def _handle_print_request(self, options: Dict[str, Any], flashcard_set: FlashcardSet) -> bool:
        """Handle the print request based on options."""
        try:
            # Get selected cards
            start_idx = options['start_index']
            end_idx = options['end_index']
            selected_cards = flashcard_set.flashcards[start_idx:end_idx]
            
            if not selected_cards:
                messagebox.showwarning("Warning", "No cards selected for printing.")
                return False
            
            # Generate PDF based on print mode
            if options['print_mode'] == 'one_sided':
                pdf_data = self._generate_one_sided_pdf(selected_cards, options)
            elif options['print_mode'] == 'two_sided':
                pdf_data = self._generate_two_sided_pdf(selected_cards, options)
            else:  # double_sided
                pdf_data = self._generate_double_sided_pdf(selected_cards, options)
            
            if not pdf_data:
                messagebox.showerror("Error", "Failed to generate PDF.")
                return False
            
            # Handle output action
            return self._handle_output_action(pdf_data, options, flashcard_set)
        
        except Exception as e:
            logger.error(f"Print request failed: {e}")
            messagebox.showerror("Error", f"Printing failed: {e}")
            return False
    
    def _generate_one_sided_pdf(self, cards: List[Flashcard], options: Dict[str, Any]) -> Optional[bytes]:
        """Generate one-sided PDF (front only)."""
        try:
            # Create temporary flashcard set
            from ...core.models import FlashcardSet
            temp_set = FlashcardSet()
            temp_set.flashcards = cards
            
            # Create temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)
            
            # Generate PDF
            success = self.pdf_manager.generate_single_sided_pdf(
                temp_set, 
                tmp_path,
                show_fronts=True
            )
            
            if success:
                with open(tmp_path, 'rb') as f:
                    pdf_data = f.read()
                os.unlink(tmp_path)
                return pdf_data
            
            return None
        except Exception as e:
            logger.error(f"Failed to generate one-sided PDF: {e}")
            return None
    
    def _generate_two_sided_pdf(self, cards: List[Flashcard], options: Dict[str, Any]) -> Optional[bytes]:
        """Generate two-sided PDF (separate front and back pages)."""
        try:
            # Create temporary flashcard set
            from ...core.models import FlashcardSet
            temp_set = FlashcardSet()
            temp_set.flashcards = cards
            
            # Create temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)
            
            # Generate double-sided PDF
            success = self.pdf_manager.generate_double_sided_pdf(temp_set, tmp_path)
            
            if success:
                with open(tmp_path, 'rb') as f:
                    pdf_data = f.read()
                os.unlink(tmp_path)
                return pdf_data
            
            return None
        except Exception as e:
            logger.error(f"Failed to generate two-sided PDF: {e}")
            return None
    
    def _generate_double_sided_pdf(self, cards: List[Flashcard], options: Dict[str, Any]) -> Optional[bytes]:
        """Generate double-sided PDF (duplex printing)."""
        # For now, use the same as two-sided
        return self._generate_two_sided_pdf(cards, options)
    
    def _handle_output_action(self, pdf_data: bytes, options: Dict[str, Any], flashcard_set: FlashcardSet) -> bool:
        """Handle the output action (preview, save, or print)."""
        action = options['output_action']
        
        if action == 'preview':
            return self._preview_pdf(pdf_data)
        elif action == 'save':
            return self._save_pdf(pdf_data, flashcard_set)
        elif action == 'print':
            return self._print_pdf(pdf_data)
        
        return False
    
    def _preview_pdf(self, pdf_data: bytes) -> bool:
        """Preview PDF in default viewer."""
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(pdf_data)
                tmp_file.flush()
                
                # Open with default PDF viewer
                if sys.platform.startswith('win'):
                    os.startfile(tmp_file.name)
                elif sys.platform.startswith('darwin'):
                    subprocess.run(['open', tmp_file.name])
                else:
                    subprocess.run(['xdg-open', tmp_file.name])
                
                return True
        
        except Exception as e:
            logger.error(f"Failed to preview PDF: {e}")
            messagebox.showerror("Error", f"Failed to preview PDF: {e}")
            return False
    
    def _save_pdf(self, pdf_data: bytes, flashcard_set: FlashcardSet) -> bool:
        """Save PDF to file."""
        try:
            default_name = f"{flashcard_set.name}_flashcards.pdf"
            file_path = filedialog.asksaveasfilename(
                title="Save PDF",
                defaultextension=".pdf",
                filetypes=[("PDF Files", "*.pdf")],
                initialfile=default_name
            )
            
            if file_path:
                with open(file_path, 'wb') as f:
                    f.write(pdf_data)
                
                messagebox.showinfo("Success", f"PDF saved to {file_path}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to save PDF: {e}")
            messagebox.showerror("Error", f"Failed to save PDF: {e}")
            return False
    
    def _print_pdf(self, pdf_data: bytes) -> bool:
        """Send PDF directly to printer."""
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(pdf_data)
                tmp_file.flush()
                
                # Platform-specific printing
                if sys.platform.startswith('win'):
                    # Windows: use default print command
                    os.startfile(tmp_file.name, "print")
                elif sys.platform.startswith('darwin'):
                    # macOS: use lpr
                    subprocess.run(['lpr', tmp_file.name])
                else:
                    # Linux: use lpr or try to open print dialog
                    try:
                        subprocess.run(['lpr', tmp_file.name])
                    except FileNotFoundError:
                        # Fallback to opening with default viewer
                        subprocess.run(['xdg-open', tmp_file.name])
                
                messagebox.showinfo("Success", "Print job sent to printer.")
                return True
        
        except Exception as e:
            logger.error(f"Failed to print PDF: {e}")
            messagebox.showerror("Error", f"Failed to print PDF: {e}")
            return False

# Global print system instance
print_system = EnhancedPrintSystem()