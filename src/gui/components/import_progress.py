"""Import Progress Dialog
Displays a modal progress bar and message for long-running import operations.
"""
import customtkinter as ctk
from typing import Optional


class ImportProgress(ctk.CTkToplevel):
    def __init__(self, parent, title: str = "Importing", modal: bool = True, **kwargs):
        super().__init__(parent, **kwargs)
        self.title(title)
        self.geometry("420x120")
        self.resizable(False, False)
        self.transient(parent)
        if modal:
            try:
                self.grab_set()
            except Exception:
                pass

        self.grid_columnconfigure(0, weight=1)

        self.msg_label = ctk.CTkLabel(self, text="Starting...", anchor="w")
        self.msg_label.grid(row=0, column=0, padx=16, pady=(16, 6), sticky="ew")

        self.progress = ctk.CTkProgressBar(self)
        self.progress.grid(row=1, column=0, padx=16, pady=(6, 12), sticky="ew")
        self.progress.set(0.0)
        
        # Cancel control
        self.cancelled = False
        self.cancel_button = ctk.CTkButton(self, text="Cancel", command=self._on_cancel, width=80)
        self.cancel_button.grid(row=2, column=0, sticky="e", padx=16, pady=(0, 12))

    def set_progress(self, percent: int, message: Optional[str] = None):
        """Set progress percent (0-100) and optional message."""
        try:
            pct = max(0, min(100, int(percent)))
            self.progress.set(pct / 100.0)
            if message is not None:
                self.msg_label.configure(text=message)
            # Force UI update
            try:
                self.update_idletasks()
            except Exception:
                pass
        except Exception:
            pass

    def close(self):
        try:
            try:
                self.grab_release()
            except Exception:
                pass
            try:
                self.destroy()
            except Exception:
                pass
        except Exception:
            pass

    def _on_cancel(self):
        try:
            self.cancelled = True
            self.msg_label.configure(text="Cancelling...")
            try:
                self.cancel_button.configure(state="disabled")
            except Exception:
                pass
            try:
                self.update_idletasks()
            except Exception:
                pass
        except Exception:
            pass

    def is_cancelled(self) -> bool:
        return bool(self.cancelled)
