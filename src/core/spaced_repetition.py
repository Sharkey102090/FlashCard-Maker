"""
Spaced Repetition System
========================

Advanced spaced repetition algorithm based on SuperMemo and SM-2 algorithm.
Automatically schedules flashcard reviews based on performance and difficulty.
"""

import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

class ReviewResult(Enum):
    """Possible results from reviewing a flashcard."""
    AGAIN = 0      # Complete blackout
    HARD = 1       # Incorrect response; correct response remembered
    GOOD = 2       # Correct response after hesitation
    EASY = 3       # Perfect response

@dataclass
class ReviewData:
    """Stores review statistics for spaced repetition."""
    ease_factor: float = 2.5      # Ease factor (minimum 1.3)
    interval: int = 1             # Current interval in days
    repetition: int = 0           # Number of consecutive correct answers
    last_review: Optional[datetime] = None
    next_review: Optional[datetime] = None
    total_reviews: int = 0
    total_time_spent: float = 0.0  # In seconds
    
    # Learning phase tracking
    learning_step: int = 0        # Current step in learning phase
    graduated: bool = False       # Whether card has graduated from learning
    
    # Additional metrics
    response_times: List[float] = field(default_factory=list)  # Response times in seconds
    review_history: List[Tuple[datetime, ReviewResult, float]] = field(default_factory=list)
    
    def add_review(self, result: ReviewResult, response_time: float):
        """Add a review to the history."""
        self.review_history.append((datetime.now(timezone.utc), result, response_time))
        self.response_times.append(response_time)
        self.total_reviews += 1
        self.total_time_spent += response_time
        
        # Keep only last 50 response times for performance
        if len(self.response_times) > 50:
            self.response_times = self.response_times[-50:]
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time."""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate based on review history."""
        if not self.review_history:
            return 0.0
        
        successful = sum(1 for _, result, _ in self.review_history 
                        if result in [ReviewResult.GOOD, ReviewResult.EASY])
        return successful / len(self.review_history)

class SpacedRepetitionEngine:
    """
    Spaced repetition engine implementing modified SM-2 algorithm.
    
    Features:
    - Learning phase for new cards
    - Graduated review scheduling
    - Dynamic difficulty adjustment
    - Performance-based scheduling
    """
    
    # Learning steps (in minutes)
    LEARNING_STEPS = [1, 10, 1440]  # 1 min, 10 min, 1 day
    
    # Graduating interval (days)
    GRADUATING_INTERVAL = 1
    EASY_INTERVAL = 4
    
    # Interval modifiers
    HARD_INTERVAL_FACTOR = 1.2
    EASY_INTERVAL_FACTOR = 1.3
    
    # Ease factor bounds
    MIN_EASE_FACTOR = 1.3
    MAX_EASE_FACTOR = 5.0
    
    def __init__(self):
        self.review_data: Dict[str, ReviewData] = {}
    
    def get_review_data(self, card_id: str) -> ReviewData:
        """Get or create review data for a card."""
        if card_id not in self.review_data:
            self.review_data[card_id] = ReviewData()
        return self.review_data[card_id]
    
    def review_card(self, card_id: str, result: ReviewResult, response_time: float = 0.0) -> None:
        """Process a card review and update scheduling."""
        data = self.get_review_data(card_id)
        data.add_review(result, response_time)
        data.last_review = datetime.now(timezone.utc)
        
        if not data.graduated:
            self._process_learning_review(data, result)
        else:
            self._process_graduated_review(data, result)
        
        self._calculate_next_review(data)
    
    def _process_learning_review(self, data: ReviewData, result: ReviewResult) -> None:
        """Process review for cards in learning phase."""
        if result == ReviewResult.AGAIN:
            # Reset to first learning step
            data.learning_step = 0
        elif result in [ReviewResult.GOOD, ReviewResult.EASY]:
            # Advance to next learning step
            data.learning_step += 1
            
            # Check if graduated
            if data.learning_step >= len(self.LEARNING_STEPS):
                data.graduated = True
                data.repetition = 1
                
                if result == ReviewResult.EASY:
                    data.interval = self.EASY_INTERVAL
                else:
                    data.interval = self.GRADUATING_INTERVAL
        else:  # HARD
            # Stay at current step but don't advance
            pass
    
    def _process_graduated_review(self, data: ReviewData, result: ReviewResult) -> None:
        """Process review for graduated cards."""
        if result == ReviewResult.AGAIN:
            # Reset to learning
            data.graduated = False
            data.learning_step = 0
            data.repetition = 0
            data.interval = 1
            data.ease_factor = max(self.MIN_EASE_FACTOR, data.ease_factor - 0.2)
        else:
            # Update ease factor based on performance
            self._update_ease_factor(data, result)
            
            # Calculate new interval
            if data.repetition == 0:
                data.interval = 1
            elif data.repetition == 1:
                data.interval = 6
            else:
                if result == ReviewResult.HARD:
                    data.interval = max(1, int(data.interval * self.HARD_INTERVAL_FACTOR))
                elif result == ReviewResult.EASY:
                    data.interval = int(data.interval * data.ease_factor * self.EASY_INTERVAL_FACTOR)
                else:  # GOOD
                    data.interval = int(data.interval * data.ease_factor)
            
            data.repetition += 1
    
    def _update_ease_factor(self, data: ReviewData, result: ReviewResult) -> None:
        """Update ease factor based on review result."""
        if result == ReviewResult.HARD:
            data.ease_factor = max(self.MIN_EASE_FACTOR, data.ease_factor - 0.15)
        elif result == ReviewResult.EASY:
            data.ease_factor = min(self.MAX_EASE_FACTOR, data.ease_factor + 0.1)
        # GOOD doesn't change ease factor significantly
        elif result == ReviewResult.GOOD:
            data.ease_factor = max(self.MIN_EASE_FACTOR, data.ease_factor - 0.02)
    
    def _calculate_next_review(self, data: ReviewData) -> None:
        """Calculate when the card should be reviewed next."""
        now = datetime.now(timezone.utc)
        
        if not data.graduated:
            # In learning phase, use learning steps
            if data.learning_step < len(self.LEARNING_STEPS):
                minutes = self.LEARNING_STEPS[data.learning_step]
                data.next_review = now + timedelta(minutes=minutes)
            else:
                # Shouldn't happen, but fallback
                data.next_review = now + timedelta(days=1)
        else:
            # Graduated, use interval
            data.next_review = now + timedelta(days=data.interval)
    
    def get_due_cards(self, card_ids: List[str]) -> List[str]:
        """Get list of card IDs that are due for review."""
        now = datetime.now(timezone.utc)
        due_cards = []
        
        for card_id in card_ids:
            data = self.get_review_data(card_id)
            
            # New cards (never reviewed) are always due
            if data.next_review is None:
                due_cards.append(card_id)
            elif data.next_review <= now:
                due_cards.append(card_id)
        
        return due_cards
    
    def get_study_stats(self, card_ids: List[str]) -> Dict[str, Any]:
        """Get comprehensive study statistics."""
        if not card_ids:
            return {
                "total_cards": 0,
                "new_cards": 0,
                "learning_cards": 0,
                "due_cards": 0,
                "total_reviews": 0,
                "average_ease": 0.0,
                "average_interval": 0.0,
                "success_rate": 0.0,
                "total_study_time": 0.0
            }
        
        now = datetime.now(timezone.utc)
        new_cards = 0
        learning_cards = 0
        due_cards = 0
        total_reviews = 0
        total_ease = 0.0
        total_interval = 0.0
        graduated_count = 0
        total_study_time = 0.0
        successful_reviews = 0
        
        for card_id in card_ids:
            data = self.get_review_data(card_id)
            
            # Count card types
            if data.next_review is None:
                new_cards += 1
            elif not data.graduated:
                learning_cards += 1
            elif data.next_review <= now:
                due_cards += 1
            
            # Accumulate stats
            total_reviews += data.total_reviews
            total_study_time += data.total_time_spent
            
            if data.graduated:
                total_ease += data.ease_factor
                total_interval += data.interval
                graduated_count += 1
            
            # Count successful reviews
            successful_reviews += sum(1 for _, result, _ in data.review_history 
                                    if result in [ReviewResult.GOOD, ReviewResult.EASY])
        
        return {
            "total_cards": len(card_ids),
            "new_cards": new_cards,
            "learning_cards": learning_cards,
            "due_cards": due_cards,
            "total_reviews": total_reviews,
            "average_ease": total_ease / graduated_count if graduated_count > 0 else 2.5,
            "average_interval": total_interval / graduated_count if graduated_count > 0 else 0.0,
            "success_rate": successful_reviews / total_reviews if total_reviews > 0 else 0.0,
            "total_study_time": total_study_time
        }
    
    def export_data(self) -> Dict[str, Any]:
        """Export review data for persistence."""
        export_data = {}
        for card_id, data in self.review_data.items():
            export_data[card_id] = {
                "ease_factor": data.ease_factor,
                "interval": data.interval,
                "repetition": data.repetition,
                "last_review": data.last_review.isoformat() if data.last_review else None,
                "next_review": data.next_review.isoformat() if data.next_review else None,
                "total_reviews": data.total_reviews,
                "total_time_spent": data.total_time_spent,
                "learning_step": data.learning_step,
                "graduated": data.graduated,
                "response_times": data.response_times,
                "review_history": [
                    (timestamp.isoformat(), result.value, time) 
                    for timestamp, result, time in data.review_history
                ]
            }
        return export_data
    
    def import_data(self, data: Dict[str, Any]) -> None:
        """Import review data from persistence."""
        for card_id, card_data in data.items():
            review_data = ReviewData()
            review_data.ease_factor = card_data.get("ease_factor", 2.5)
            review_data.interval = card_data.get("interval", 1)
            review_data.repetition = card_data.get("repetition", 0)
            review_data.total_reviews = card_data.get("total_reviews", 0)
            review_data.total_time_spent = card_data.get("total_time_spent", 0.0)
            review_data.learning_step = card_data.get("learning_step", 0)
            review_data.graduated = card_data.get("graduated", False)
            review_data.response_times = card_data.get("response_times", [])
            
            # Parse datetime strings
            if card_data.get("last_review"):
                review_data.last_review = datetime.fromisoformat(card_data["last_review"])
            if card_data.get("next_review"):
                review_data.next_review = datetime.fromisoformat(card_data["next_review"])
            
            # Parse review history
            review_data.review_history = []
            for timestamp_str, result_val, time in card_data.get("review_history", []):
                timestamp = datetime.fromisoformat(timestamp_str)
                result = ReviewResult(result_val)
                review_data.review_history.append((timestamp, result, time))
            
            self.review_data[card_id] = review_data

# Global spaced repetition engine instance
spaced_repetition = SpacedRepetitionEngine()