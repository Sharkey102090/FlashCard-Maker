"""
PDF Print System
================

Generate print-ready PDFs with double-sided printing support.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.platypus.flowables import Flowable

import io
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ..core.models import FlashcardSet, Flashcard
from ..utils.config import config
from ..utils.security import logger

class FlashcardFlowable(Flowable):
    """Custom flowable for rendering flashcards."""
    
    def __init__(self, front_text: str, back_text: str, width: float, height: float, 
                 is_back: bool = False, card_style: Optional[Dict[str, Any]] = None):
        self.front_text = front_text
        self.back_text = back_text
        self.width = width
        self.height = height
        self.is_back = is_back
        self.card_style = card_style or {}
        
        # Set dimensions
        self._width = width
        self._height = height
    
    def draw(self):
        """Draw the flashcard."""
        canvas = self.canv
        
        # Draw card border
        border_width = self.card_style.get('border_width', 1)
        border_color = self.card_style.get('border_color', colors.black)
        
        canvas.setStrokeColor(border_color)
        canvas.setLineWidth(border_width)
        canvas.rect(0, 0, self.width, self.height)
        
        # Add background color if specified
        bg_color = self.card_style.get('background_color')
        if bg_color:
            canvas.setFillColor(bg_color)
            canvas.rect(0, 0, self.width, self.height, fill=1, stroke=0)
            canvas.setStrokeColor(border_color)
            canvas.setLineWidth(border_width)
            canvas.rect(0, 0, self.width, self.height, fill=0, stroke=1)
        
        # Text content
        text = self.back_text if self.is_back else self.front_text
        
        # Clean HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # Text styling
        font_name = self.card_style.get('font_name', 'Helvetica')
        font_size = self.card_style.get('font_size', 12)
        text_color = self.card_style.get('text_color', colors.black)
        
        canvas.setFont(font_name, font_size)
        canvas.setFillColor(text_color)
        
        # Text positioning
        margin = self.card_style.get('margin', 10)
        max_width = self.width - (2 * margin)
        max_height = self.height - (2 * margin)
        
        # Word wrapping
        lines = self._wrap_text(clean_text, font_name, font_size, max_width)
        
        # Calculate starting y position (center vertically)
        line_height = font_size * 1.2
        total_text_height = len(lines) * line_height
        start_y = self.height - margin - (max_height - total_text_height) / 2
        
        # Draw text lines
        for i, line in enumerate(lines):
            y_pos = start_y - (i * line_height)
            if y_pos < margin:  # Stop if we run out of space
                break
            # Center front-side text horizontally within the card; keep back-side left-aligned
            if not self.is_back:
                # drawCentredString expects x coordinate of center
                center_x = self.width / 2
                canvas.drawCentredString(center_x, y_pos, line)
            else:
                canvas.drawString(margin, y_pos, line)
        
        # Add side indicator
        indicator_text = "BACK" if self.is_back else "FRONT"
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(colors.gray)
        canvas.drawRightString(self.width - 5, 5, indicator_text)
    
    def _wrap_text(self, text: str, font_name: str, font_size: int, max_width: float) -> List[str]:
        """Wrap text to fit within specified width."""
        from reportlab.pdfbase.pdfmetrics import stringWidth
        
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            text_width = stringWidth(test_line, font_name, font_size)
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Single word is too long, truncate it
                    lines.append(word[:50] + "...")
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines

class PDFPrintManager:
    """Manages PDF generation for flashcard printing."""
    
    def __init__(self):
        self.page_size = letter  # Default page size
        self.margin = 0.5 * inch
        self.card_styles = self._get_default_card_styles()
    
    def _get_default_card_styles(self) -> Dict[str, Any]:
        """Get default card styling."""
        return {
            'border_width': 1,
            'border_color': colors.black,
            'background_color': None,
            'font_name': 'Helvetica',
            'font_size': 12,
            'text_color': colors.black,
            'margin': 10
        }
    
    def _calculate_card_dimensions(self) -> Tuple[float, float]:
        """Calculate card dimensions based on configuration."""
        card_width = config.get('printing.card_width', 3.5) * inch
        card_height = config.get('printing.card_height', 2.5) * inch
        return card_width, card_height
    
    def _calculate_grid_layout(self, card_width: float, card_height: float) -> Tuple[int, int]:
        """Calculate how many cards fit on a page."""
        page_width, page_height = self.page_size
        
        # Account for margins
        usable_width = page_width - (2 * self.margin)
        usable_height = page_height - (2 * self.margin)
        
        # Calculate maximum cards per row/column
        max_cards_per_row = int(usable_width // card_width)
        max_cards_per_column = int(usable_height // card_height)
        
        # Use configured values if they fit, otherwise use maximum
        cards_per_row = min(config.get('printing.cards_per_row', 2), max_cards_per_row)
        cards_per_column = min(config.get('printing.cards_per_column', 3), max_cards_per_column)
        
        return max(1, cards_per_row), max(1, cards_per_column)
    
    def generate_single_sided_pdf(self, flashcard_set: FlashcardSet, output_path: Path,
                                 show_fronts: bool = True) -> bool:
        """Generate single-sided PDF (all fronts or all backs)."""
        try:
            # Calculate dimensions
            card_width, card_height = self._calculate_card_dimensions()
            cards_per_row, cards_per_column = self._calculate_grid_layout(card_width, card_height)
            cards_per_page = cards_per_row * cards_per_column
            
            # Create PDF
            doc = SimpleDocTemplate(str(output_path), pagesize=self.page_size)
            story = []
            
            # Group cards into pages
            flashcards = flashcard_set.flashcards
            for page_start in range(0, len(flashcards), cards_per_page):
                page_cards = flashcards[page_start:page_start + cards_per_page]
                
                # Create table for card layout
                table_data = []
                for row in range(cards_per_column):
                    row_cards = []
                    for col in range(cards_per_row):
                        card_index = row * cards_per_row + col
                        if card_index < len(page_cards):
                            card = page_cards[card_index]
                            flowable = FlashcardFlowable(
                                card.front_text,
                                card.back_text,
                                card_width,
                                card_height,
                                is_back=not show_fronts,
                                card_style=self.card_styles
                            )
                            row_cards.append(flowable)
                        else:
                            # Empty cell
                            row_cards.append('')
                    table_data.append(row_cards)
                
                # Create table
                table = Table(table_data, colWidths=[card_width] * cards_per_row,
                            rowHeights=[card_height] * cards_per_column)
                
                table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ]))
                
                story.append(table)
                
                # Add page break if not last page
                if page_start + cards_per_page < len(flashcards):
                    story.append(PageBreak())
            
            doc.build(story)
            
            logger.info(f"Single-sided PDF generated: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return False
    
    def generate_double_sided_pdf(self, flashcard_set: FlashcardSet, output_path: Path) -> bool:
        """Generate double-sided PDF with proper alignment."""
        try:
            # Generate fronts PDF
            fronts_path = output_path.with_suffix('.fronts.pdf')
            backs_path = output_path.with_suffix('.backs.pdf')
            
            # Generate both sides
            self.generate_single_sided_pdf(flashcard_set, fronts_path, show_fronts=True)
            self.generate_single_sided_pdf(flashcard_set, backs_path, show_fronts=False)
            
            # Merge PDFs for double-sided printing
            self._merge_for_double_sided(fronts_path, backs_path, output_path)
            
            # Clean up temporary files
            fronts_path.unlink(missing_ok=True)
            backs_path.unlink(missing_ok=True)
            
            logger.info(f"Double-sided PDF generated: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Double-sided PDF generation failed: {e}")
            return False
    
    def _merge_for_double_sided(self, fronts_path: Path, backs_path: Path, output_path: Path):
        """Merge front and back PDFs for double-sided printing."""
        try:
            from PyPDF2 import PdfReader, PdfWriter
            
            # Read PDFs
            fronts_reader = PdfReader(str(fronts_path))
            backs_reader = PdfReader(str(backs_path))
            
            writer = PdfWriter()
            
            # Interleave pages: front, back, front, back, etc.
            max_pages = max(len(fronts_reader.pages), len(backs_reader.pages))
            
            for i in range(max_pages):
                # Add front page
                if i < len(fronts_reader.pages):
                    writer.add_page(fronts_reader.pages[i])
                
                # Add back page (reversed for proper alignment)
                back_index = len(backs_reader.pages) - 1 - i
                if back_index >= 0:
                    writer.add_page(backs_reader.pages[back_index])
            
            # Write merged PDF
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
        
        except ImportError:
            # Fallback: just save fronts if PyPDF2 not available
            logger.warning("PyPDF2 not available, saving fronts only")
            import shutil
            shutil.copy(fronts_path, output_path)
        except Exception as e:
            logger.error(f"PDF merging failed: {e}")
            raise
    
    def generate_study_sheet_pdf(self, flashcard_set: FlashcardSet, output_path: Path) -> bool:
        """Generate a study sheet with questions and answers."""
        try:
            doc = SimpleDocTemplate(str(output_path), pagesize=self.page_size)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                alignment=TA_CENTER,
                spaceAfter=20
            )
            
            title = Paragraph(f"Study Sheet: {flashcard_set.name}", title_style)
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Add flashcards
            for i, flashcard in enumerate(flashcard_set.flashcards, 1):
                # Question
                question_style = ParagraphStyle(
                    'Question',
                    parent=styles['Normal'],
                    fontSize=12,
                    fontName='Helvetica-Bold',
                    leftIndent=0,
                    spaceAfter=6
                )
                
                question_text = re.sub(r'<[^>]+>', '', flashcard.front_text)
                question = Paragraph(f"{i}. {question_text}", question_style)
                story.append(question)
                
                # Answer
                answer_style = ParagraphStyle(
                    'Answer',
                    parent=styles['Normal'],
                    fontSize=11,
                    leftIndent=20,
                    spaceAfter=12
                )
                
                answer_text = re.sub(r'<[^>]+>', '', flashcard.back_text)
                answer = Paragraph(f"Answer: {answer_text}", answer_style)
                story.append(answer)
                
                # Add a line break every 10 questions
                if i % 10 == 0:
                    story.append(PageBreak())
            
            # Add metadata
            story.append(PageBreak())
            story.append(Paragraph("Study Statistics", styles['Heading2']))
            
            stats = flashcard_set.get_statistics()
            metadata_text = f"""
            Total Cards: {stats['total_cards']}
            Categories: {', '.join(stats['categories'])}
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            story.append(Paragraph(metadata_text, styles['Normal']))
            
            doc.build(story)
            
            logger.info(f"Study sheet PDF generated: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Study sheet generation failed: {e}")
            return False
    
    def set_page_size(self, page_size):
        """Set the page size for PDF generation."""
        self.page_size = page_size
    
    def set_margin(self, margin: float):
        """Set the page margin."""
        self.margin = margin
    
    def update_card_styles(self, styles: Dict[str, Any]):
        """Update card styling options."""
        self.card_styles.update(styles)
    
    def get_page_preview(self, flashcard_set: FlashcardSet, page_number: int = 1) -> bytes:
        """Generate a preview of a specific page."""
        try:
            # Create in-memory PDF
            buffer = io.BytesIO()
            
            # Calculate dimensions
            card_width, card_height = self._calculate_card_dimensions()
            cards_per_row, cards_per_column = self._calculate_grid_layout(card_width, card_height)
            cards_per_page = cards_per_row * cards_per_column
            
            # Get cards for this page
            start_index = (page_number - 1) * cards_per_page
            page_cards = flashcard_set.flashcards[start_index:start_index + cards_per_page]
            
            if not page_cards:
                return b''
            
            # Create simple canvas for preview
            c = canvas.Canvas(buffer, pagesize=self.page_size)
            
            # Draw cards on preview
            for i, card in enumerate(page_cards):
                row = i // cards_per_row
                col = i % cards_per_row
                
                x = self.margin + (col * card_width)
                y = self.page_size[1] - self.margin - ((row + 1) * card_height)
                
                # Draw card border
                c.rect(x, y, card_width, card_height)
                
                # Draw front text (simplified)
                text = re.sub(r'<[^>]+>', '', card.front_text)[:100]
                # For preview, center the front text horizontally within the card
                text_x = x + (card_width / 2)
                text_y = y + card_height - 20
                c.drawCentredString(text_x, text_y, text)
            
            c.save()
            return buffer.getvalue()
        
        except Exception as e:
            logger.error(f"Preview generation failed: {e}")
            return b''

# Global PDF manager instance
pdf_manager = PDFPrintManager()