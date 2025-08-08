import logging
import sys
import os
from datetime import datetime
from typing import List
import textwrap

# Define the log file path
log_file = "/var/log/disk_erase.log"

# Session tracking - capture all logs during current session
_session_logs = []
_session_active = False

class SessionCapturingHandler(logging.Handler):
    """Custom handler to capture session logs"""
    def emit(self, record):
        global _session_logs, _session_active
        if _session_active:
            # Format the message the same way as the file handler
            timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
            formatted_message = f"[{timestamp}] {record.levelname}: {record.getMessage()}"
            _session_logs.append(formatted_message)

# Configure logging with basic format
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Add session capturing handler
session_handler = SessionCapturingHandler()
logger.addHandler(session_handler)

try:
    log_handler = logging.FileHandler(log_file)
    log_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
except PermissionError:
    print("Error: Permission denied. Please run the script with sudo.", file=sys.stderr)
    sys.exit(1)  # Exit the script to enforce sudo usage


def log_info(message: str) -> None:
    """Log general information to both the console and log file."""
    logger.info(message)

def log_error(message: str) -> None:
    """Log error message to both the console and log file."""
    logger.error(message)

def log_warning(message: str) -> None:
    """Log warning message to both the console and log file."""
    logger.warning(message)

def log_erase_operation(disk_id: str, filesystem: str, method: str) -> None:
    """Log detailed erasure operation with stable disk identifier."""
    message = f"Erasure operation for disk ID: {disk_id}. Filesystem: {filesystem}. Erase method: {method}"
    logger.info(message)

def log_disk_completed(disk_id: str) -> None:
    """Log completion of operations on a single disk without ending session."""
    message = f"Completed operations on disk ID: {disk_id}"
    logger.info(message)

def session_start() -> None:
    """Log session start with clear separator and begin session log capture"""
    global _session_logs, _session_active
    
    # Clear previous session logs and start capturing
    _session_logs = []
    _session_active = True
    
    separator = "=" * 80
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"\n{separator}\n")
        f.write(f"SESSION START: {timestamp}\n")
        f.write(f"{separator}\n")
    
    # This will be captured in session logs too
    log_info(f"New session started at {timestamp}")

def session_end() -> None:
    """Log session end with clear separator and stop session log capture"""
    global _session_active
    
    separator = "=" * 80
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Log session end (this will be captured before we stop)
    log_info(f"Session ended at {timestamp}")
    
    # Stop capturing session logs
    _session_active = False
    
    with open(log_file, "a") as f:
        f.write(f"\n{separator}\n")
        f.write(f"SESSION END: {timestamp}\n")
        f.write(f"{separator}\n\n")

def log_application_exit(exit_method: str = "Exit button") -> None:
    """Log application exit and end session properly."""
    log_info(f"Application closed by user via {exit_method}")
    session_end()

def log_erasure_process_completed() -> None:
    """Log that the erasure process is completed but don't end session."""
    log_info("Erasure process completed")

def log_erasure_process_stopped() -> None:
    """Log that the erasure process was stopped by user but don't end session."""
    log_info("Erasure process stopped by user")

def get_current_session_logs() -> List[str]:
    """Get all logs from the current session"""
    global _session_logs
    return _session_logs.copy()

def generate_session_pdf() -> str:
    """
    Generate a PDF from current session logs using built-in libraries only.
    
    Returns:
        str: Path to the generated PDF file
    
    Raises:
        Exception: If PDF generation fails
    """
    try:
        # Get current session logs
        session_logs = get_current_session_logs()
        
        if not session_logs:
            raise Exception("No session logs available to generate PDF")
        
        # Create output directory if it doesn't exist
        output_dir = "/tmp/disk_cloner_logs"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"disk_cloner_session_{timestamp}.pdf"
        pdf_path = os.path.join(output_dir, pdf_filename)
        
        # Create PDF using basic PDF structure
        _create_simple_pdf(
            pdf_path,
            "Disk Cloner - Session Log Report",
            session_logs,
            f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Log Entries: {len(session_logs)}"
        )
        
        log_info(f"Session log PDF generated successfully: {pdf_path}")
        return pdf_path
        
    except PermissionError as e:
        error_msg = f"Permission denied writing PDF to {output_dir}: {str(e)}"
        log_error(error_msg)
        raise Exception(error_msg)
    except OSError as e:
        error_msg = f"OS error during PDF generation: {str(e)}"
        log_error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error during session PDF generation: {str(e)}"
        log_error(error_msg)
        raise Exception(error_msg)

def generate_log_file_pdf() -> str:
    """
    Generate a PDF from the complete log file using built-in libraries only.
    
    Returns:
        str: Path to the generated PDF file
    
    Raises:
        Exception: If PDF generation fails
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = "/tmp/disk_cloner_logs"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"disk_cloner_complete_log_{timestamp}.pdf"
        pdf_path = os.path.join(output_dir, pdf_filename)
        
        # Read log file
        if not os.path.exists(log_file):
            raise FileNotFoundError(f"Log file not found: {log_file}")
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_lines = [line.strip() for line in f.readlines() if line.strip()]
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            with open(log_file, 'r', encoding='latin-1') as f:
                log_lines = [line.strip() for line in f.readlines() if line.strip()]
        
        # Create PDF using basic PDF structure
        _create_simple_pdf(
            pdf_path,
            "Disk Cloner - Complete Log File Report",
            log_lines,
            f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Log File: {log_file}",
            f"Total Log Lines: {len(log_lines)}"
        )
        
        log_info(f"Complete log file PDF generated successfully: {pdf_path}")
        return pdf_path
        
    except FileNotFoundError as e:
        error_msg = f"Log file not found: {str(e)}"
        log_error(error_msg)
        raise Exception(error_msg)
    except PermissionError as e:
        error_msg = f"Permission denied: {str(e)}"
        log_error(error_msg)
        raise Exception(error_msg)
    except OSError as e:
        error_msg = f"OS error during PDF generation: {str(e)}"
        log_error(error_msg)
        raise Exception(error_msg)
    except UnicodeDecodeError as e:
        error_msg = f"Error reading log file - encoding issue: {str(e)}"
        log_error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error during complete log PDF generation: {str(e)}"
        log_error(error_msg)
        raise Exception(error_msg)

def _create_simple_pdf(file_path: str, title: str, content_lines: List[str], *info_lines: str) -> None:
    """
    Create a simple PDF file using basic PDF structure without external libraries.
    Supports multiple pages automatically.
    
    Args:
        file_path: Path where to save the PDF
        title: Title of the document
        content_lines: List of content lines to include
        *info_lines: Additional info lines to include in header
    """
    try:
        with open(file_path, 'wb') as f:
            # PDF Header
            f.write(b'%PDF-1.4\n')
            
            # Prepare content and calculate pages needed
            pages_content = _prepare_pdf_pages(title, content_lines, *info_lines)
            
            # Track object positions for xref table
            object_positions = {}
            page_objects = []
            
            # Object 1: Catalog
            object_positions[1] = f.tell()
            catalog_obj = b'''1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
'''
            f.write(catalog_obj)
            
            # Object 2: Pages (parent)
            object_positions[2] = f.tell()
            num_pages = len(pages_content)
            page_refs = " ".join([f"{3 + i} 0 R" for i in range(num_pages)])
            pages_obj = f'''2 0 obj
<<
/Type /Pages
/Kids [{page_refs}]
/Count {num_pages}
>>
endobj
'''.encode('utf-8')
            f.write(pages_obj)
            
            # Create page objects and content streams
            obj_counter = 3
            for page_idx, page_content in enumerate(pages_content):
                content_bytes = page_content.encode('utf-8')
                content_length = len(content_bytes)
                
                # Page object
                object_positions[obj_counter] = f.tell()
                page_obj = f'''{obj_counter} 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents {obj_counter + 1} 0 R
/Resources <<
/Font <<
/F1 {3 + num_pages * 2} 0 R
>>
>>
>>
endobj
'''.encode('utf-8')
                f.write(page_obj)
                obj_counter += 1
                
                # Content stream object
                object_positions[obj_counter] = f.tell()
                content_obj = f'''{obj_counter} 0 obj
<<
/Length {content_length}
>>
stream
{page_content}
endstream
endobj
'''.encode('utf-8')
                f.write(content_obj)
                obj_counter += 1
            
            # Font object
            font_obj_num = obj_counter
            object_positions[font_obj_num] = f.tell()
            font_obj = f'''{font_obj_num} 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Courier
>>
endobj
'''.encode('utf-8')
            f.write(font_obj)
            
            # Cross-reference table
            xref_start = f.tell()
            f.write(b'xref\n')
            f.write(f'0 {font_obj_num + 1}\n'.encode())
            f.write(b'0000000000 65535 f \n')
            for i in range(1, font_obj_num + 1):
                f.write(f'{object_positions[i]:010d} 00000 n \n'.encode())
            
            # Trailer
            trailer = f'''trailer
<<
/Size {font_obj_num + 1}
/Root 1 0 R
>>
startxref
{xref_start}
%%EOF
'''.encode('utf-8')
            f.write(trailer)
            
    except Exception as e:
        raise Exception(f"Error creating PDF structure: {str(e)}")

def _prepare_pdf_pages(title: str, content_lines: List[str], *info_lines: str) -> List[str]:
    """
    Prepare PDF content split into multiple pages.
    
    Args:
        title: Document title
        content_lines: List of content lines
        *info_lines: Additional info lines
    
    Returns:
        List[str]: List of page contents (PDF content streams)
    """
    try:
        pages = []
        lines_per_page = 55  # Conservative estimate for 8pt font
        header_lines = 8  # Space needed for title and info
        
        # Wrap all content lines first
        wrapped_lines = []
        display_line_number = 1
        
        if not content_lines:
            wrapped_lines = ["No content available."]
        else:
            for content_line in content_lines:
                wrapped_content = _wrap_log_line(content_line, display_line_number)
                wrapped_lines.extend(wrapped_content)
                display_line_number += 1
        
        # Split wrapped lines into pages
        current_page_lines = []
        remaining_space = lines_per_page - header_lines
        
        for line in wrapped_lines:
            if remaining_space <= 0:
                # Start new page
                if current_page_lines:
                    pages.append(_create_page_content(title, current_page_lines, len(pages) + 1, *info_lines))
                current_page_lines = []
                remaining_space = lines_per_page - (5 if len(pages) > 0 else header_lines)  # Less header space on subsequent pages
            
            current_page_lines.append(line)
            remaining_space -= 1
        
        # Add the last page if there are remaining lines
        if current_page_lines:
            pages.append(_create_page_content(title, current_page_lines, len(pages) + 1, *info_lines))
        
        # Ensure at least one page
        if not pages:
            pages.append(_create_page_content(title, ["No content available."], 1, *info_lines))
        
        return pages
        
    except Exception as e:
        raise Exception(f"Error preparing PDF pages: {str(e)}")

def _create_page_content(title: str, content_lines: List[str], page_number: int, *info_lines: str) -> str:
    """
    Create PDF content stream for a single page.
    
    Args:
        title: Document title
        content_lines: List of content lines for this page
        page_number: Current page number
        *info_lines: Additional info lines
    
    Returns:
        str: PDF content stream for this page
    """
    try:
        lines = []
        
        # Start content stream
        lines.append("BT")  # Begin text
        
        y_position = 750  # Start near top of page
        
        if page_number == 1:
            # Add title only on first page
            lines.append(f"50 {y_position} Td")  # Move to position
            lines.append("/F1 16 Tf")  # Larger font for title
            lines.append(f"({_escape_pdf_string(title)}) Tj")
            y_position -= 30
            
            # Add info lines only on first page
            lines.append("/F1 10 Tf")  # Smaller font for info
            for info_line in info_lines:
                lines.append(f"0 -{15} Td")  # Move down 15 points
                lines.append(f"({_escape_pdf_string(info_line)}) Tj")
                y_position -= 15
            
            y_position -= 20  # Extra space before content
        else:
            # Subsequent pages: just show page number and title
            lines.append(f"50 {y_position} Td")  # Move to position
            lines.append("/F1 12 Tf")  # Medium font for page header
            lines.append(f"({_escape_pdf_string(f'{title} - Page {page_number}')}) Tj")
            y_position -= 25
        
        # Add content lines
        lines.append("/F1 8 Tf")  # Small font for content
        if page_number == 1:
            lines.append(f"0 -{20} Td")  # Move down from header
        else:
            lines.append(f"0 -{15} Td")  # Less space on subsequent pages
        
        for content_line in content_lines:
            lines.append(f"0 -{12} Td")  # Move down 12 points
            lines.append(f"({_escape_pdf_string(content_line)}) Tj")
        
        # Add page number at bottom
        lines.append(f"/F1 8 Tf")
        lines.append(f"0 -{750 - len(content_lines) * 12} Td")  # Move to bottom
        lines.append(f"({_escape_pdf_string(f'Page {page_number}')}) Tj")
        
        lines.append("ET")  # End text
        
        return "\n".join(lines)
        
    except Exception as e:
        raise Exception(f"Error creating page content: {str(e)}")

def _prepare_pdf_content(title: str, content_lines: List[str], *info_lines: str) -> str:
    """
    DEPRECATED: Use _prepare_pdf_pages instead for multi-page support.
    Prepare PDF content stream with proper formatting and line wrapping.
    
    Args:
        title: Document title
        content_lines: List of content lines
        *info_lines: Additional info lines
    
    Returns:
        str: Formatted PDF content stream
    """
    # This function is kept for backward compatibility but should not be used
    pages = _prepare_pdf_pages(title, content_lines, *info_lines)
    return pages[0] if pages else "BT\n(No content available.)\nET"

def _wrap_log_line(content_line: str, line_number: int, max_width: int = 75) -> List[str]:
    """
    Wrap a single log line into multiple lines if it's too long.
    
    Args:
        content_line: The original log line
        line_number: The line number to display
        max_width: Maximum characters per line (accounting for line number prefix)
    
    Returns:
        List[str]: List of wrapped lines with proper formatting
    """
    try:
        # Calculate available width after line number prefix
        line_prefix = f"{line_number:4d}: "
        continuation_prefix = "      "  # 6 spaces to align with content
        available_width = max_width - len(line_prefix)
        
        # Use textwrap to break long lines at word boundaries
        wrapped_content = textwrap.fill(
            content_line,
            width=available_width,
            break_long_words=True,
            break_on_hyphens=True,
            expand_tabs=True,
            replace_whitespace=False
        )
        
        wrapped_lines = wrapped_content.split('\n')
        
        # Format the lines with proper prefixes
        formatted_lines = []
        for i, line in enumerate(wrapped_lines):
            if i == 0:
                # First line gets the line number
                formatted_lines.append(f"{line_prefix}{line}")
            else:
                # Continuation lines get indented to align with content
                formatted_lines.append(f"{continuation_prefix}{line}")
        
        return formatted_lines
        
    except Exception as e:
        # Fallback to simple truncation if wrapping fails
        if len(content_line) > max_width - 6:
            return [f"{line_number:4d}: {content_line[:max_width-9]}..."]
        else:
            return [f"{line_number:4d}: {content_line}"]

def _escape_pdf_string(text: str) -> str:
    """
    Escape special characters in PDF strings.
    
    Args:
        text: Text to escape
    
    Returns:
        str: Escaped text safe for PDF
    """
    try:
        # Replace special PDF string characters
        text = str(text)
        text = text.replace('\\', '\\\\')  # Backslash must be first
        text = text.replace('(', '\\(')
        text = text.replace(')', '\\)')
        text = text.replace('\r', ' ')
        text = text.replace('\n', ' ')
        text = text.replace('\t', ' ')
        
        # Remove or replace non-printable characters
        cleaned_text = ""
        for char in text:
            if ord(char) >= 32 and ord(char) <= 126:
                cleaned_text += char
            else:
                cleaned_text += " "  # Replace with space
        
        return cleaned_text
        
    except Exception as e:
        return f"Error processing text: {str(e)}"

# Deprecated - replaced with session_start() and session_end()
def blank() -> None:
    """Add blank lines to separated erasuring process between different execution"""
    session_end()