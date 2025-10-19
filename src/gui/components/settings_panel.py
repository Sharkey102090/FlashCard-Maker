"""
Settings Panel Component
========================

Configuration panel for application settings.
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from typing import Dict, Any

from ...utils.config import config
from ...utils.security import logger

class SettingsPanel(ctk.CTkFrame):
    """Settings configuration panel."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """Set up the settings UI."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Create tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Appearance tab
        self.appearance_tab = self.tabview.add("Appearance")
        self._setup_appearance_tab()
        
        # Security tab
        self.security_tab = self.tabview.add("Security")
        self._setup_security_tab()
        
        # Printing tab
        self.printing_tab = self.tabview.add("Printing")
        self._setup_printing_tab()
        
        # Buttons
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        
        self.save_button = ctk.CTkButton(
            self.button_frame,
            text="Save",
            command=self._save_settings
        )
        self.save_button.grid(row=0, column=0, padx=10, pady=10)
        
        self.reset_button = ctk.CTkButton(
            self.button_frame,
            text="Reset to Defaults",
            command=self._reset_settings
        )
        self.reset_button.grid(row=0, column=1, padx=10, pady=10)
    
    def _setup_appearance_tab(self):
        """Set up appearance settings."""
        # Theme selection
        self.theme_label = ctk.CTkLabel(self.appearance_tab, text="Theme:")
        self.theme_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.theme_var = tk.StringVar()
        self.theme_combo = ctk.CTkComboBox(
            self.appearance_tab,
            values=["light", "dark", "system"],
            variable=self.theme_var
        )
        self.theme_combo.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # Font family
        self.font_family_label = ctk.CTkLabel(self.appearance_tab, text="Font Family:")
        self.font_family_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.font_family_var = tk.StringVar()
        self.font_family_combo = ctk.CTkComboBox(
            self.appearance_tab,
            values=["Segoe UI", "Arial", "Times New Roman", "Calibri", "Comic Sans MS"],
            variable=self.font_family_var
        )
        self.font_family_combo.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Font size
        self.font_size_label = ctk.CTkLabel(self.appearance_tab, text="Font Size:")
        self.font_size_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        self.font_size_var = tk.StringVar()
        self.font_size_combo = ctk.CTkComboBox(
            self.appearance_tab,
            values=["8", "9", "10", "11", "12", "14", "16", "18"],
            variable=self.font_size_var
        )
        self.font_size_combo.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        # Window size
        self.window_size_label = ctk.CTkLabel(self.appearance_tab, text="Default Window Size:")
        self.window_size_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        
        self.window_size_frame = ctk.CTkFrame(self.appearance_tab)
        self.window_size_frame.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        self.width_var = tk.StringVar()
        self.width_entry = ctk.CTkEntry(self.window_size_frame, textvariable=self.width_var, width=80)
        self.width_entry.grid(row=0, column=0, padx=5, pady=5)
        
        self.x_label = ctk.CTkLabel(self.window_size_frame, text="x")
        self.x_label.grid(row=0, column=1, padx=5, pady=5)
        
        self.height_var = tk.StringVar()
        self.height_entry = ctk.CTkEntry(self.window_size_frame, textvariable=self.height_var, width=80)
        self.height_entry.grid(row=0, column=2, padx=5, pady=5)
        
        # Configure grid weights
        self.appearance_tab.grid_columnconfigure(1, weight=1)
    
    def _setup_security_tab(self):
        """Set up security settings."""
        # Data encryption
        self.encrypt_var = tk.BooleanVar()
        self.encrypt_check = ctk.CTkCheckBox(
            self.security_tab,
            text="Encrypt stored data",
            variable=self.encrypt_var
        )
        self.encrypt_check.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Max file size
        self.max_file_size_label = ctk.CTkLabel(self.security_tab, text="Max File Size (MB):")
        self.max_file_size_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.max_file_size_var = tk.StringVar()
        self.max_file_size_entry = ctk.CTkEntry(
            self.security_tab,
            textvariable=self.max_file_size_var
        )
        self.max_file_size_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Session timeout
        self.session_timeout_label = ctk.CTkLabel(self.security_tab, text="Session Timeout (minutes):")
        self.session_timeout_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        self.session_timeout_var = tk.StringVar()
        self.session_timeout_entry = ctk.CTkEntry(
            self.security_tab,
            textvariable=self.session_timeout_var
        )
        self.session_timeout_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        # Configure grid weights
        self.security_tab.grid_columnconfigure(1, weight=1)
    
    def _setup_printing_tab(self):
        """Set up printing settings."""
        # Card dimensions
        self.card_width_label = ctk.CTkLabel(self.printing_tab, text="Card Width (inches):")
        self.card_width_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.card_width_var = tk.StringVar()
        self.card_width_entry = ctk.CTkEntry(
            self.printing_tab,
            textvariable=self.card_width_var
        )
        self.card_width_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        self.card_height_label = ctk.CTkLabel(self.printing_tab, text="Card Height (inches):")
        self.card_height_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.card_height_var = tk.StringVar()
        self.card_height_entry = ctk.CTkEntry(
            self.printing_tab,
            textvariable=self.card_height_var
        )
        self.card_height_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Margin
        self.margin_label = ctk.CTkLabel(self.printing_tab, text="Margin (inches):")
        self.margin_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        self.margin_var = tk.StringVar()
        self.margin_entry = ctk.CTkEntry(
            self.printing_tab,
            textvariable=self.margin_var
        )
        self.margin_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        # Cards per page
        self.cards_per_row_label = ctk.CTkLabel(self.printing_tab, text="Cards per Row:")
        self.cards_per_row_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        
        self.cards_per_row_var = tk.StringVar()
        self.cards_per_row_combo = ctk.CTkComboBox(
            self.printing_tab,
            values=["1", "2", "3", "4", "5", "6"],
            variable=self.cards_per_row_var
        )
        self.cards_per_row_combo.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        self.cards_per_column_label = ctk.CTkLabel(self.printing_tab, text="Cards per Column:")
        self.cards_per_column_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        
        self.cards_per_column_var = tk.StringVar()
        self.cards_per_column_combo = ctk.CTkComboBox(
            self.printing_tab,
            values=["1", "2", "3", "4", "5", "6"],
            variable=self.cards_per_column_var
        )
        self.cards_per_column_combo.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        
        # Configure grid weights
        self.printing_tab.grid_columnconfigure(1, weight=1)
    
    def _load_settings(self):
        """Load current settings into the UI."""
        # Appearance settings
        self.theme_var.set(config.get('gui.theme', 'system'))
        self.font_family_var.set(config.get('gui.font_family', 'Segoe UI'))
        self.font_size_var.set(str(config.get('gui.font_size', 11)))
        self.width_var.set(str(config.get('gui.window_width', 1200)))
        self.height_var.set(str(config.get('gui.window_height', 800)))
        
        # Security settings
        self.encrypt_var.set(config.get('security.encrypt_data', True))
        max_size_mb = config.get('security.max_file_size', 50 * 1024 * 1024) // (1024 * 1024)
        self.max_file_size_var.set(str(max_size_mb))
        timeout_min = config.get('security.session_timeout', 1800) // 60
        self.session_timeout_var.set(str(timeout_min))
        
        # Printing settings
        self.card_width_var.set(str(config.get('printing.card_width', 3.5)))
        self.card_height_var.set(str(config.get('printing.card_height', 2.5)))
        self.margin_var.set(str(config.get('printing.margin', 0.25)))
        self.cards_per_row_var.set(str(config.get('printing.cards_per_row', 2)))
        self.cards_per_column_var.set(str(config.get('printing.cards_per_column', 3)))
    
    def _save_settings(self):
        """Save settings to configuration."""
        try:
            # Validate and save appearance settings
            config.set('gui.theme', self.theme_var.get())
            config.set('gui.font_family', self.font_family_var.get())
            config.set('gui.font_size', int(self.font_size_var.get()))
            config.set('gui.window_width', int(self.width_var.get()))
            config.set('gui.window_height', int(self.height_var.get()))
            
            # Validate and save security settings
            config.set('security.encrypt_data', self.encrypt_var.get())
            max_size_mb = int(self.max_file_size_var.get())
            config.set('security.max_file_size', max_size_mb * 1024 * 1024)
            timeout_min = int(self.session_timeout_var.get())
            config.set('security.session_timeout', timeout_min * 60)
            
            # Validate and save printing settings
            config.set('printing.card_width', float(self.card_width_var.get()))
            config.set('printing.card_height', float(self.card_height_var.get()))
            config.set('printing.margin', float(self.margin_var.get()))
            config.set('printing.cards_per_row', int(self.cards_per_row_var.get()))
            config.set('printing.cards_per_column', int(self.cards_per_column_var.get()))
            
            logger.info("Settings saved successfully")
            
            # Close window
            self.master.destroy()
        
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please check your input values: {e}")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def _reset_settings(self):
        """Reset settings to defaults."""
        result = messagebox.askyesno(
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?"
        )
        
        if result:
            config.reset_to_defaults()
            self._load_settings()
            logger.info("Settings reset to defaults")