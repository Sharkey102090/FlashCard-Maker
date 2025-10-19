"""
Flashcard Viewer Component
==========================

Interactive flashcard viewer for study mode.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Optional, List
import random
from datetime import datetime

from ...core.models import FlashcardSet, Flashcard
from ...utils.security import logger

class FlashcardViewer(ctk.CTkFrame):
    """Interactive flashcard viewer for studying."""
    
    def __init__(self, parent, flashcard_set: Optional[FlashcardSet] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.flashcard_set = flashcard_set or FlashcardSet()
        self.current_cards: List[Flashcard] = []
        self.current_index = 0
        self.show_front = True
        self.study_session_start = datetime.now()
        
        self._setup_ui()
        self._load_flashcards()
    
    def _setup_ui(self):
        """Set up the viewer UI."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Study Mode",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.progress_label = ctk.CTkLabel(
            self.header_frame,
            text="0 / 0",
            font=ctk.CTkFont(size=14)
        )
        self.progress_label.grid(row=0, column=1, padx=10, pady=10)
        
        # Card display
        self.card_frame = ctk.CTkFrame(self)
        self.card_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.card_frame.grid_columnconfigure(0, weight=1)
        self.card_frame.grid_rowconfigure(0, weight=1)
        
        # Create an inner frame to help vertically center the card content.
        # We use three rows: top spacer (weight=1), content (weight=0), bottom spacer (weight=1)
        # This allows the content to stay vertically centered while the card_frame expands.
        self.card_inner = ctk.CTkFrame(self.card_frame)
        self.card_inner.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.card_inner.grid_rowconfigure(0, weight=1)
        self.card_inner.grid_rowconfigure(1, weight=0)
        self.card_inner.grid_rowconfigure(2, weight=1)
        self.card_inner.grid_columnconfigure(0, weight=1)

        # Label used to display card text. We'll center this label for front cards
        # and left-align for back cards as needed.
        self.card_content_label = ctk.CTkLabel(
            self.card_inner,
            text="",
            font=ctk.CTkFont(size=16),
            wraplength=1000,
            anchor="center"
        )
        # Place in middle row so top/bottom spacers center it vertically
        self.card_content_label.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Side indicator
        self.side_label = ctk.CTkLabel(
            self.card_frame,
            text="FRONT",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="blue"
        )
        self.side_label.grid(row=1, column=0, padx=20, pady=(0, 10))
        
        # Controls
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        self.flip_button = ctk.CTkButton(
            self.controls_frame,
            text="Flip Card",
            command=self._flip_card,
            width=100
        )
        self.flip_button.grid(row=0, column=0, padx=10, pady=10)
        
        self.prev_button = ctk.CTkButton(
            self.controls_frame,
            text="Previous",
            command=self._previous_card,
            width=100
        )
        self.prev_button.grid(row=0, column=1, padx=10, pady=10)
        
        self.next_button = ctk.CTkButton(
            self.controls_frame,
            text="Next",
            command=self._next_card,
            width=100
        )
        self.next_button.grid(row=0, column=2, padx=10, pady=10)
        
        self.shuffle_button = ctk.CTkButton(
            self.controls_frame,
            text="Shuffle",
            command=self._shuffle_cards,
            width=100
        )
        self.shuffle_button.grid(row=0, column=3, padx=10, pady=10)
        
        # Study tracking
        self.tracking_frame = ctk.CTkFrame(self)
        self.tracking_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        
        self.tracking_label = ctk.CTkLabel(
            self.tracking_frame,
            text="How well did you know this card?",
            font=ctk.CTkFont(size=14)
        )
        self.tracking_label.grid(row=0, column=0, columnspan=3, padx=10, pady=5)
        
        self.easy_button = ctk.CTkButton(
            self.tracking_frame,
            text="Easy",
            command=lambda: self._mark_difficulty("easy"),
            fg_color="green",
            width=80
        )
        self.easy_button.grid(row=1, column=0, padx=10, pady=5)
        
        self.medium_button = ctk.CTkButton(
            self.tracking_frame,
            text="Medium",
            command=lambda: self._mark_difficulty("medium"),
            fg_color="orange",
            width=80
        )
        self.medium_button.grid(row=1, column=1, padx=10, pady=5)
        
        self.hard_button = ctk.CTkButton(
            self.tracking_frame,
            text="Hard",
            command=lambda: self._mark_difficulty("hard"),
            fg_color="red",
            width=80
        )
        self.hard_button.grid(row=1, column=2, padx=10, pady=5)
    
    def _load_flashcards(self):
        """Load flashcards for study session."""
        self.current_cards = self.flashcard_set.flashcards.copy()
        self.current_index = 0
        self._update_display()
    
    def _update_display(self):
        """Update the card display."""
        if not self.current_cards:
            # Show empty state in the centered label
            self.card_content_label.configure(text="No flashcards available", anchor="center")
            self.progress_label.configure(text="0 / 0")
            return
        
        current_card = self.current_cards[self.current_index]
        
        # Show content based on current side
        content = current_card.front_text if self.show_front else current_card.back_text
        
        # Remove HTML tags for display (simple approach)
        import re
        content = re.sub(r'<[^>]+>', '', content)
        
        # Update display using the label. Center front cards both horizontally
        # and vertically by using the inner frame spacers and centering properties.
        if self.show_front:
            # Center horizontally and vertically
            self.card_content_label.configure(text=content, anchor="center")
        else:
            # Left-align the back side for readability
            self.card_content_label.configure(text=content, anchor="w")
        
        # Update labels
        self.side_label.configure(
            text="FRONT" if self.show_front else "BACK",
            text_color="blue" if self.show_front else "green"
        )
        
        self.progress_label.configure(
            text=f"{self.current_index + 1} / {len(self.current_cards)}"
        )
    
    def _flip_card(self):
        """Flip the current card."""
        self.show_front = not self.show_front
        self._update_display()
    
    def _next_card(self):
        """Go to next card."""
        if self.current_cards and self.current_index < len(self.current_cards) - 1:
            self.current_index += 1
            self.show_front = True
            self._update_display()
    
    def _previous_card(self):
        """Go to previous card."""
        if self.current_cards and self.current_index > 0:
            self.current_index -= 1
            self.show_front = True
            self._update_display()
    
    def _shuffle_cards(self):
        """Shuffle the cards."""
        if self.current_cards:
            random.shuffle(self.current_cards)
            self.current_index = 0
            self.show_front = True
            self._update_display()
            logger.info("Cards shuffled")
    
    def _mark_difficulty(self, difficulty: str):
        """Mark the difficulty of the current card."""
        if not self.current_cards:
            return
        
        current_card = self.current_cards[self.current_index]
        
        # Determine if correct based on difficulty
        correct = difficulty == "easy"
        
        # Update study statistics
        current_card.study(correct)
        
        # Auto-advance to next card
        self._next_card()
        
        logger.info(f"Card marked as {difficulty}: {current_card.id}")
    
    def set_flashcard_set(self, flashcard_set: FlashcardSet):
        """Set a new flashcard set."""
        self.flashcard_set = flashcard_set
        self._load_flashcards()