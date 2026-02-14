"""
Base report generator - supports both PDF and Markdown output.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class BaseReport(ABC):
    """Base class for all report generators."""
    
    def __init__(self, output_dir: str = "reports_output"):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def generate_data(self, **kwargs) -> Dict[str, Any]:
        """
        Generate report data.
        
        Returns:
            Dictionary with report data
        """
        pass
    
    @abstractmethod
    def format_markdown(self, data: Dict[str, Any]) -> str:
        """
        Format report as Markdown.
        
        Args:
            data: Report data
            
        Returns:
            Markdown formatted string
        """
        pass
    
    def generate_markdown(self, filename: str = None, **kwargs) -> str:
        """
        Generate Markdown report.
        
        Args:
            filename: Output filename (optional)
            **kwargs: Parameters for generate_data
            
        Returns:
            Path to generated file
        """
        data = self.generate_data(**kwargs)
        markdown = self.format_markdown(data)
        
        if filename:
            output_path = self.output_dir / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            return str(output_path)
        
        return markdown
    
    def generate_pdf(self, filename: str, **kwargs) -> str:
        """
        Generate PDF report.
        
        Args:
            filename: Output filename
            **kwargs: Parameters for generate_data
            
        Returns:
            Path to generated file
        """
        if not REPORTLAB_AVAILABLE:
            print("Warning: reportlab not installed. PDF generation not available.")
            return ""
        
        data = self.generate_data(**kwargs)
        output_path = self.output_dir / filename
        
        # Create PDF
        doc = SimpleDocTemplate(str(output_path), pagesize=A4)
        story = self._build_pdf_story(data)
        doc.build(story)
        
        return str(output_path)
    
    def _build_pdf_story(self, data: Dict[str, Any]) -> list:
        """
        Build PDF story from data.
        
        Args:
            data: Report data
            
        Returns:
            List of reportlab elements
        """
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title = data.get('title', 'Report')
        story.append(Paragraph(title, styles['Title']))
        story.append(Spacer(1, 0.2 * inch))
        
        # Date
        date_str = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        story.append(Paragraph(f"Date: {date_str}", styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Content - subclasses should override this
        content = self.format_markdown(data)
        for line in content.split('\n'):
            if line.strip():
                story.append(Paragraph(line, styles['Normal']))
                story.append(Spacer(1, 0.1 * inch))
        
        return story
    
    def generate_both(self, base_filename: str, **kwargs) -> Dict[str, str]:
        """
        Generate both PDF and Markdown versions.
        
        Args:
            base_filename: Base filename without extension
            **kwargs: Parameters for generate_data
            
        Returns:
            Dictionary with paths to both files
        """
        md_path = self.generate_markdown(f"{base_filename}.md", **kwargs)
        pdf_path = ""
        
        if REPORTLAB_AVAILABLE:
            pdf_path = self.generate_pdf(f"{base_filename}.pdf", **kwargs)
        
        return {
            "markdown": md_path,
            "pdf": pdf_path
        }
