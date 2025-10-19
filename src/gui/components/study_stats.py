"""
Study Statistics Dashboard Component
===================================

Comprehensive study analytics and progress tracking GUI component.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone
import math

from ...core.spaced_repetition import spaced_repetition, ReviewResult
from ...core.models import FlashcardSet

class StudyStatsDashboard(ctk.CTkFrame):
    """Study statistics dashboard showing comprehensive learning analytics."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.flashcard_set: Optional[FlashcardSet] = None
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Create widgets
        self._create_header()
        self._create_stats_notebook()
        self._create_refresh_button()
        
    def _create_header(self):
        """Create dashboard header."""
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="📊 Study Statistics Dashboard",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        self.last_updated_label = ctk.CTkLabel(
            header_frame,
            text="Last updated: Never",
            font=ctk.CTkFont(size=12)
        )
        self.last_updated_label.grid(row=0, column=1, padx=20, pady=15, sticky="e")
    
    def _create_stats_notebook(self):
        """Create tabbed notebook for different statistics views."""
        # Create notebook frame
        notebook_frame = ctk.CTkFrame(self)
        notebook_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        notebook_frame.grid_columnconfigure(0, weight=1)
        notebook_frame.grid_rowconfigure(1, weight=1)
        
        # Tab buttons
        tab_frame = ctk.CTkFrame(notebook_frame)
        tab_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        self.overview_button = ctk.CTkButton(
            tab_frame,
            text="Overview",
            command=lambda: self._switch_tab("overview")
        )
        self.overview_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.performance_button = ctk.CTkButton(
            tab_frame,
            text="Performance",
            command=lambda: self._switch_tab("performance")
        )
        self.performance_button.grid(row=0, column=1, padx=5, pady=5)
        
        self.schedule_button = ctk.CTkButton(
            tab_frame,
            text="Schedule",
            command=lambda: self._switch_tab("schedule")
        )
        self.schedule_button.grid(row=0, column=2, padx=5, pady=5)
        
        self.trends_button = ctk.CTkButton(
            tab_frame,
            text="Trends",
            command=lambda: self._switch_tab("trends")
        )
        self.trends_button.grid(row=0, column=3, padx=5, pady=5)
        
        # Content frame
        self.content_frame = ctk.CTkFrame(notebook_frame)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Initialize with overview tab
        self.current_tab = "overview"
        self._create_overview_tab()
    
    def _create_refresh_button(self):
        """Create refresh button."""
        self.refresh_button = ctk.CTkButton(
            self,
            text="🔄 Refresh Statistics",
            command=self.refresh_stats
        )
        self.refresh_button.grid(row=2, column=0, pady=10)
    
    def _switch_tab(self, tab_name: str):
        """Switch to a different tab."""
        if self.current_tab == tab_name:
            return
        
        # Update button states
        buttons = {
            "overview": self.overview_button,
            "performance": self.performance_button,
            "schedule": self.schedule_button,
            "trends": self.trends_button
        }
        
        for name, button in buttons.items():
            if name == tab_name:
                button.configure(fg_color=("gray70", "gray30"))
            else:
                button.configure(fg_color=("gray85", "gray25"))
        
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Create new tab content
        self.current_tab = tab_name
        
        if tab_name == "overview":
            self._create_overview_tab()
        elif tab_name == "performance":
            self._create_performance_tab()
        elif tab_name == "schedule":
            self._create_schedule_tab()
        elif tab_name == "trends":
            self._create_trends_tab()
    
    def _create_overview_tab(self):
        """Create overview statistics tab."""
        # Scrollable frame
        scrollable = ctk.CTkScrollableFrame(self.content_frame)
        scrollable.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scrollable.grid_columnconfigure(0, weight=1)
        
        if not self.flashcard_set:
            no_data_label = ctk.CTkLabel(
                scrollable,
                text="No flashcard set loaded",
                font=ctk.CTkFont(size=16)
            )
            no_data_label.grid(row=0, column=0, pady=50)
            return
        
        # Get statistics
        card_ids = [card.id for card in self.flashcard_set.flashcards]
        stats = spaced_repetition.get_study_stats(card_ids)
        
        # Quick stats cards
        self._create_stats_cards(scrollable, stats)
        
        # Study progress section
        self._create_study_progress(scrollable, stats, row_start=2)
        
        # Recent activity
        self._create_recent_activity(scrollable, card_ids, row_start=4)
    
    def _create_stats_cards(self, parent, stats: Dict[str, Any]):
        """Create overview statistics cards."""
        cards_frame = ctk.CTkFrame(parent)
        cards_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Total cards
        self._create_stat_card(
            cards_frame, 0, 0,
            "📚 Total Cards",
            str(stats["total_cards"]),
            "Cards in set"
        )
        
        # New cards
        self._create_stat_card(
            cards_frame, 0, 1,
            "🆕 New Cards",
            str(stats["new_cards"]),
            "Never studied"
        )
        
        # Due cards
        self._create_stat_card(
            cards_frame, 0, 2,
            "⏰ Due Cards",
            str(stats["due_cards"]),
            "Ready to review"
        )
        
        # Success rate
        success_rate = stats["success_rate"] * 100
        self._create_stat_card(
            cards_frame, 0, 3,
            "✅ Success Rate",
            f"{success_rate:.1f}%",
            "Overall accuracy"
        )
        
        # Second row
        # Learning cards
        self._create_stat_card(
            cards_frame, 1, 0,
            "📖 Learning",
            str(stats["learning_cards"]),
            "In learning phase"
        )
        
        # Total reviews
        self._create_stat_card(
            cards_frame, 1, 1,
            "🔄 Reviews",
            str(stats["total_reviews"]),
            "Total completed"
        )
        
        # Study time
        hours = stats["total_study_time"] / 3600
        time_text = f"{hours:.1f}h" if hours >= 1 else f"{stats['total_study_time']/60:.1f}m"
        self._create_stat_card(
            cards_frame, 1, 2,
            "⏱️ Study Time",
            time_text,
            "Total time spent"
        )
        
        # Average ease
        self._create_stat_card(
            cards_frame, 1, 3,
            "📈 Avg Ease",
            f"{stats['average_ease']:.2f}",
            "Difficulty factor"
        )
    
    def _create_stat_card(self, parent, row: int, col: int, title: str, value: str, subtitle: str):
        """Create a single statistics card."""
        card = ctk.CTkFrame(parent)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=10, pady=(10, 2))
        
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=20, weight="bold")
        )
        value_label.grid(row=1, column=0, padx=10, pady=2)
        
        subtitle_label = ctk.CTkLabel(
            card,
            text=subtitle,
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        subtitle_label.grid(row=2, column=0, padx=10, pady=(2, 10))
    
    def _create_study_progress(self, parent, stats: Dict[str, Any], row_start: int):
        """Create study progress visualization."""
        progress_frame = ctk.CTkFrame(parent)
        progress_frame.grid(row=row_start, column=0, sticky="ew", pady=(0, 20))
        progress_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            progress_frame,
            text="📊 Study Progress",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(15, 10))
        
        total_cards = stats["total_cards"]
        if total_cards == 0:
            return
        
        # Create progress bars
        studied_cards = total_cards - stats["new_cards"]
        mastered_cards = total_cards - stats["new_cards"] - stats["learning_cards"] - stats["due_cards"]
        
        # Studied progress
        self._create_progress_bar(
            progress_frame, 1,
            "Cards Studied",
            studied_cards,
            total_cards,
            "green"
        )
        
        # Mastered progress
        self._create_progress_bar(
            progress_frame, 2,
            "Cards Mastered",
            mastered_cards,
            total_cards,
            "blue"
        )
    
    def _create_progress_bar(self, parent, row: int, label: str, current: int, total: int, color: str):
        """Create a progress bar with label."""
        bar_frame = ctk.CTkFrame(parent)
        bar_frame.grid(row=row, column=0, sticky="ew", padx=20, pady=5)
        bar_frame.grid_columnconfigure(1, weight=1)
        
        label_widget = ctk.CTkLabel(
            bar_frame,
            text=label,
            width=120
        )
        label_widget.grid(row=0, column=0, padx=(10, 20), pady=10, sticky="w")
        
        progress = ctk.CTkProgressBar(bar_frame)
        progress.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
        
        if total > 0:
            progress.set(current / total)
        else:
            progress.set(0)
        
        percentage = (current / total * 100) if total > 0 else 0
        percent_label = ctk.CTkLabel(
            bar_frame,
            text=f"{current}/{total} ({percentage:.1f}%)",
            width=100
        )
        percent_label.grid(row=0, column=2, padx=(20, 10), pady=10, sticky="e")
    
    def _create_recent_activity(self, parent, card_ids: List[str], row_start: int):
        """Create recent activity section."""
        activity_frame = ctk.CTkFrame(parent)
        activity_frame.grid(row=row_start, column=0, sticky="ew", pady=(0, 20))
        activity_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            activity_frame,
            text="📅 Recent Activity",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(15, 10))
        
        # Get recent reviews
        recent_reviews = self._get_recent_reviews(card_ids, days=7)
        
        if not recent_reviews:
            no_activity_label = ctk.CTkLabel(
                activity_frame,
                text="No recent activity",
                text_color="gray"
            )
            no_activity_label.grid(row=1, column=0, pady=10)
            return
        
        # Create activity list
        activity_list = ctk.CTkScrollableFrame(activity_frame, height=200)
        activity_list.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))
        
        for i, (card_id, timestamp, result, response_time) in enumerate(recent_reviews[:20]):
            self._create_activity_item(activity_list, i, card_id, timestamp, result, response_time)
    
    def _create_activity_item(self, parent, row: int, card_id: str, timestamp: datetime, 
                             result: ReviewResult, response_time: float):
        """Create a single activity item."""
        item_frame = ctk.CTkFrame(parent)
        item_frame.grid(row=row, column=0, sticky="ew", pady=2)
        item_frame.grid_columnconfigure(1, weight=1)
        
        # Result icon
        result_icons = {
            ReviewResult.AGAIN: "❌",
            ReviewResult.HARD: "😓",
            ReviewResult.GOOD: "👍",
            ReviewResult.EASY: "⭐"
        }
        
        icon_label = ctk.CTkLabel(
            item_frame,
            text=result_icons.get(result, "❓"),
            width=30
        )
        icon_label.grid(row=0, column=0, padx=10, pady=5)
        
        # Card info
        card = self._find_card_by_id(card_id)
        card_text = card.front_text[:50] + "..." if card and len(card.front_text) > 50 else (card.front_text if card else "Unknown card")
        
        info_label = ctk.CTkLabel(
            item_frame,
            text=card_text,
            anchor="w"
        )
        info_label.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        
        # Time info
        time_ago = self._format_time_ago(timestamp)
        response_text = f"{response_time:.1f}s" if response_time > 0 else ""
        time_label = ctk.CTkLabel(
            item_frame,
            text=f"{time_ago} • {response_text}",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        time_label.grid(row=0, column=2, padx=10, pady=5)
    
    def _create_performance_tab(self):
        """Create performance analysis tab."""
        scrollable = ctk.CTkScrollableFrame(self.content_frame)
        scrollable.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        if not self.flashcard_set:
            no_data_label = ctk.CTkLabel(
                scrollable,
                text="No flashcard set loaded",
                font=ctk.CTkFont(size=16)
            )
            no_data_label.grid(row=0, column=0, pady=50)
            return
        
        # Performance metrics would go here
        # This is a simplified version
        placeholder_label = ctk.CTkLabel(
            scrollable,
            text="Performance analytics coming soon...",
            font=ctk.CTkFont(size=16)
        )
        placeholder_label.grid(row=0, column=0, pady=50)
    
    def _create_schedule_tab(self):
        """Create schedule view tab."""
        scrollable = ctk.CTkScrollableFrame(self.content_frame)
        scrollable.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        if not self.flashcard_set:
            no_data_label = ctk.CTkLabel(
                scrollable,
                text="No flashcard set loaded",
                font=ctk.CTkFont(size=16)
            )
            no_data_label.grid(row=0, column=0, pady=50)
            return
        
        # Schedule view would go here
        placeholder_label = ctk.CTkLabel(
            scrollable,
            text="Schedule view coming soon...",
            font=ctk.CTkFont(size=16)
        )
        placeholder_label.grid(row=0, column=0, pady=50)
    
    def _create_trends_tab(self):
        """Create trends analysis tab."""
        scrollable = ctk.CTkScrollableFrame(self.content_frame)
        scrollable.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        if not self.flashcard_set:
            no_data_label = ctk.CTkLabel(
                scrollable,
                text="No flashcard set loaded",
                font=ctk.CTkFont(size=16)
            )
            no_data_label.grid(row=0, column=0, pady=50)
            return
        
        # Trends analysis would go here
        placeholder_label = ctk.CTkLabel(
            scrollable,
            text="Trends analysis coming soon...",
            font=ctk.CTkFont(size=16)
        )
        placeholder_label.grid(row=0, column=0, pady=50)
    
    def _get_recent_reviews(self, card_ids: List[str], days: int = 7):
        """Get recent reviews for cards."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        recent_reviews = []
        
        for card_id in card_ids:
            review_data = spaced_repetition.get_review_data(card_id)
            for timestamp, result, response_time in review_data.review_history:
                if timestamp >= cutoff_date:
                    recent_reviews.append((card_id, timestamp, result, response_time))
        
        # Sort by timestamp (newest first)
        recent_reviews.sort(key=lambda x: x[1], reverse=True)
        return recent_reviews
    
    def _find_card_by_id(self, card_id: str):
        """Find card by ID in current flashcard set."""
        if not self.flashcard_set:
            return None
        
        for card in self.flashcard_set.flashcards:
            if card.id == card_id:
                return card
        return None
    
    def _format_time_ago(self, timestamp: datetime) -> str:
        """Format timestamp as 'time ago' string."""
        now = datetime.now(timezone.utc)
        delta = now - timestamp
        
        if delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours}h ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes}m ago"
        else:
            return "Just now"
    
    def set_flashcard_set(self, flashcard_set: Optional[FlashcardSet]):
        """Set the flashcard set to analyze."""
        self.flashcard_set = flashcard_set
        self.refresh_stats()
    
    def refresh_stats(self):
        """Refresh all statistics."""
        # Update last updated time
        now = datetime.now()
        self.last_updated_label.configure(text=f"Last updated: {now.strftime('%H:%M:%S')}")
        
        # Refresh current tab
        self._switch_tab(self.current_tab)