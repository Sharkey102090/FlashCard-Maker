"""
Text Importer
=============

Simple heuristics to convert plain text (TXT/MD) and optional DOCX into flashcards.
"""
from typing import List, Tuple, Optional
from pathlib import Path
import re

try:
    import docx  # type: ignore
    DOCX_AVAILABLE = True
except Exception:
    docx = None
    DOCX_AVAILABLE = False

try:
    from PyPDF2 import PdfReader  # type: ignore
    PDF_PYPDF2 = True
except Exception:
    PdfReader = None
    PDF_PYPDF2 = False

try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text  # type: ignore
    PDF_PDFMINER = True
except Exception:
    pdfminer_extract_text = None
    PDF_PDFMINER = False

from ..core.models import Flashcard


def _read_text_file(path: Path) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def _read_docx_file(path: Path) -> str:
    if not DOCX_AVAILABLE or docx is None:
        raise ImportError('python-docx not available')
    # Import at runtime to satisfy static checkers
    import docx as _docx  # type: ignore
    doc = _docx.Document(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    return '\n\n'.join(paragraphs)


def _read_pdf_file(path: Path) -> str:
    """Read PDF text using PyPDF2 or pdfminer as a fallback."""
    if PDF_PYPDF2 and PdfReader is not None:
        reader = PdfReader(str(path))
        texts = []
        # PyPDF2's extract_text is page-based
        for page in getattr(reader, 'pages', []):
            try:
                t = page.extract_text() or ''
            except Exception:
                t = ''
            texts.append(t)
        return '\n\n'.join(t for t in texts if t).strip()

    if PDF_PDFMINER and pdfminer_extract_text is not None:
        return pdfminer_extract_text(str(path))

    raise ImportError('No PDF reader available. Install PyPDF2 or pdfminer.six')


def load_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in ('.txt', '.md'):
        return _read_text_file(path)
    if suffix in ('.docx',) and DOCX_AVAILABLE:
        return _read_docx_file(path)
    if suffix in ('.docx',) and not DOCX_AVAILABLE:
        raise ImportError('DOCX files require python-docx: pip install python-docx')
    if suffix in ('.pdf',):
        return _read_pdf_file(path)

    # Unknown extension - try to read as text
    return _read_text_file(path)


def split_paragraphs(text: str) -> List[str]:
    parts = re.split(r'\n\s*\n', text.strip())
    return [p.strip() for p in parts if p.strip()]


def _remove_repeated_headers_footers(text: str, threshold: int = 3) -> str:
    """Remove lines that repeat across the document (common headers/footers).

    Simple heuristic: count occurrences of short lines (<=80 chars) and drop those
    that appear more than `threshold` times.
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    counts = {}
    for l in lines:
        if len(l) <= 80:
            counts[l] = counts.get(l, 0) + 1

    filtered_lines = [l for l in lines if counts.get(l, 0) <= threshold]
    return '\n\n'.join(filtered_lines)


def detect_qa_in_paragraph(paragraph: str) -> Optional[Tuple[str, str]]:
    """Try to detect a Q/A pair in a paragraph.

    Heuristics:
    - If contains a colon or dash like 'Term: Definition' or 'Term - Definition'
    - If multiple lines, first line -> rest
    - If has a question mark in first sentence, use sentence up to '?' as question
    """
    # Remove common leading numbering/bullets like '1. ', 'a) ', '- ', '* '
    paragraph = re.sub(r'^\s*\d+[\.)]\s*', '', paragraph)
    paragraph = re.sub(r'^\s*[a-zA-Z][\.)]\s*', '', paragraph)
    paragraph = re.sub(r'^\s*[-\*\u2022]\s*', '', paragraph)

    # Colon/dash pattern
    m = re.match(r'^(?P<q>[^:\-\n]{1,200}?)\s*[:\-]\s*(?P<a>.+)$', paragraph)
    if m:
        q = m.group('q').strip()
        a = m.group('a').strip()
        return q, a

    # Multiple lines
    lines = [l.strip() for l in paragraph.splitlines() if l.strip()]
    if len(lines) >= 2:
        q = lines[0]
        a = '\n'.join(lines[1:])
        return q, a

    # Sentence-based: question mark
    sentences = re.split(r'(?<=[\.?\!])\s+', paragraph)
    if sentences:
        first = sentences[0]
        if '?' in first:
            q = first.strip()
            a = ' '.join(sentences[1:]).strip()
            return q, a

    # Fallback: don't auto-detect
    return None


def generate_flashcards_from_text(text: str, strategy: str = 'paragraphs') -> List[Flashcard]:
    """Generate flashcards from text.

    Strategies:
    - paragraphs: split by blank lines and try to detect Q/A
    - lines: split by line and treat each line as 'front' with empty back
    - sentences: split into sentences and pair consecutive sentences
    """
    cards: List[Flashcard] = []

    if strategy == 'paragraphs':
        # Pre-filter repeated headers/footers which commonly appear in PDFs
        try:
            text = _remove_repeated_headers_footers(text)
        except Exception:
            pass

        parts = split_paragraphs(text)
        for p in parts:
            qa = detect_qa_in_paragraph(p)
            if qa:
                q, a = qa
            else:
                # last resort: first sentence is front
                sentences = re.split(r'(?<=[\.?\!])\s+', p)
                q = sentences[0].strip()
                a = ' '.join(sentences[1:]).strip() if len(sentences) > 1 else ''
            card = Flashcard(front_text=q, back_text=a)
            cards.append(card)

    elif strategy == 'lines':
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            # colon split
            if ':' in line:
                front, back = line.split(':', 1)
            elif '-' in line:
                front, back = line.split('-', 1)
            else:
                front, back = line, ''
            cards.append(Flashcard(front_text=front.strip(), back_text=back.strip()))

    elif strategy == 'sentences':
        sentences = re.split(r'(?<=[\.?\!])\s+', text.strip())
        for i in range(0, len(sentences), 2):
            front = sentences[i].strip()
            back = sentences[i+1].strip() if i+1 < len(sentences) else ''
            cards.append(Flashcard(front_text=front, back_text=back))

    elif strategy == 'numbered':
        # Split text into paragraphs then split numbered items within each paragraph
        parts = split_paragraphs(text)
        for p in parts:
            # Split on numbered list boundaries like '1. ', '1) ', or inline numbering
            items = re.split(r'(?:(?<=\n)|^)(?:\s*\d+[\.)]\s+)', p)
            # If split produced mostly empty first element, try inline numeric separators
            if len(items) <= 1:
                # Fallback: split on patterns like '1. ' occurring inline
                items = re.split(r'\s*\d+[\.)]\s*', p)

            for item in items:
                item = item.strip()
                if not item:
                    continue
                # Remove any leading bullets/letters left over
                item = re.sub(r'^\s*[a-zA-Z][\.)]\s*', '', item)
                item = re.sub(r'^\s*[-\*\u2022]\s*', '', item)
                # Now detect term:definition inside the item
                qa = detect_qa_in_paragraph(item)
                if qa:
                    q, a = qa
                else:
                    # If no colon, try first sentence as front
                    sentences = re.split(r'(?<=[\.\?\!])\s+', item)
                    q = sentences[0].strip()
                    a = ' '.join(sentences[1:]).strip() if len(sentences) > 1 else ''
                cards.append(Flashcard(front_text=q, back_text=a))

    else:
        raise ValueError('Unknown strategy')

    return cards


# Small CLI helper (for testing)
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('path', type=str)
    p.add_argument('--strategy', choices=['paragraphs', 'lines', 'sentences'], default='paragraphs')
    args = p.parse_args()
    txt = load_text(Path(args.path))
    cards = generate_flashcards_from_text(txt, strategy=args.strategy)
    print(f'Generated {len(cards)} cards')
    for c in cards[:10]:
        print('---')
        print('Q:', c.front_text)
        print('A:', c.back_text)
