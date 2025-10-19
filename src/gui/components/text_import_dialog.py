"""
Text Import Preview Dialog
==========================

Dialog to preview generated flashcards from a text import and select which to add.
"""
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
# Import Flashcard at runtime to avoid relative import issues
try:
    from ...core.models import Flashcard as _Flashcard  # type: ignore
except Exception:
    # Fallback absolute import
    from src.core.models import Flashcard as _Flashcard  # type: ignore

# We'll import properly in runtime via relative import inside functions to avoid import cycles

class TextImportDialog(ctk.CTkToplevel):
    def __init__(self, parent, generated_cards: list, **kwargs):
        # Import Flashcard at runtime to avoid relative import issues
        try:
            from ...core.models import Flashcard as _Flashcard  # type: ignore
        except Exception:
            # Fallback absolute import
            from src.core.models import Flashcard as _Flashcard  # type: ignore

        super().__init__(parent, **kwargs)
        self.title('Import Text - Preview')
        self.generated_cards = generated_cards
        self.selected_indices = set(range(len(generated_cards)))
        self.geometry('700x500')
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill='both', expand=True, padx=10, pady=10)

        instructions = ctk.CTkLabel(top_frame, text='Review generated flashcards and uncheck any you do not want to import:')
        instructions.pack(anchor='w', pady=(0,10))

        self.list_frame = ctk.CTkScrollableFrame(top_frame)
        self.list_frame.pack(fill='both', expand=True)

        self.check_vars = []
        for i, card in enumerate(self.generated_cards):
            var = tk.BooleanVar(value=True)
            self.check_vars.append(var)
            row = ctk.CTkFrame(self.list_frame)
            row.pack(fill='x', padx=5, pady=5)
            ck = ctk.CTkCheckBox(row, variable=var)
            ck.grid(row=0, column=0, padx=5, pady=5)
            q_lbl = ctk.CTkLabel(row, text=(card.front_text[:200] + '...') if len(card.front_text) > 200 else card.front_text, width=300, anchor='w')
            q_lbl.grid(row=0, column=1, padx=5, pady=5, sticky='w')
            a_lbl = ctk.CTkLabel(row, text=(card.back_text[:200] + '...') if len(card.back_text) > 200 else card.back_text, width=300, anchor='w')
            a_lbl.grid(row=0, column=2, padx=5, pady=5, sticky='w')

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill='x', pady=10)
        cancel = ctk.CTkButton(btn_frame, text='Cancel', command=self._cancel)
        cancel.pack(side='right', padx=10)
        add_btn = ctk.CTkButton(btn_frame, text='Add Selected', fg_color='green', command=self._add_selected)
        add_btn.pack(side='right')

    def _cancel(self):
        self.result = None
        self.destroy()

    def _add_selected(self):
        selected = [i for i, v in enumerate(self.check_vars) if v.get()]
        if not selected:
            messagebox.showwarning('No cards selected', 'Please select at least one card to add.')
            return
        self.result = selected
        self.destroy()
