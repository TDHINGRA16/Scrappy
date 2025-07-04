import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green  
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record):
        # Add color to levelname
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)

def setup_logger(
    name: str = "scrappy",
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """Setup logger with console and optional file output"""
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

class RequestLogger:
    """Logger for HTTP requests and API calls"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_request(self, method: str, url: str, status_code: int, duration: float):
        """Log HTTP request details"""
        color = '\033[32m' if 200 <= status_code < 300 else '\033[31m'
        reset = '\033[0m'
        
        self.logger.info(
            f"{method} {url} - {color}{status_code}{reset} - {duration:.2f}s"
        )
    
    def log_api_call(self, service: str, endpoint: str, success: bool, duration: float):
        """Log external API calls"""
        status = "SUCCESS" if success else "FAILED"
        color = '\033[32m' if success else '\033[31m'
        reset = '\033[0m'
        
        self.logger.info(
            f"API {service} - {endpoint} - {color}{status}{reset} - {duration:.2f}s"
        )

class JobLogger:
    """Logger for scraping and messaging jobs"""
    
    def __init__(self, logger: logging.Logger, job_id: int):
        self.logger = logger
        self.job_id = job_id
    
    def log_job_start(self, job_type: str, query: str):
        """Log job start"""
        self.logger.info(f"Job {self.job_id} STARTED - {job_type} - Query: {query}")
    
    def log_job_progress(self, current: int, total: int, stage: str):
        """Log job progress"""
        percentage = (current / total * 100) if total > 0 else 0
        self.logger.info(
            f"Job {self.job_id} PROGRESS - {stage} - {current}/{total} ({percentage:.1f}%)"
        )
    
    def log_job_complete(self, results_count: int, duration: float):
        """Log job completion"""
        self.logger.info(
            f"Job {self.job_id} COMPLETED - {results_count} results - {duration:.2f}s"
        )
    
    def log_job_error(self, error: str, stage: str):
        """Log job error"""
        self.logger.error(f"Job {self.job_id} ERROR - {stage} - {error}")
    
    def log_scrape_result(self, url: str, success: bool, contact_found: bool = False):
        """Log individual scrape result"""
        status = "SUCCESS" if success else "FAILED"
        contacts = "with contacts" if contact_found else "no contacts"
        self.logger.debug(f"Job {self.job_id} SCRAPE - {url} - {status} - {contacts}")
    
    def log_message_sent(self, contact_method: str, recipient: str, success: bool):
        """Log message sending result"""
        status = "SENT" if success else "FAILED"
        self.logger.info(
            f"Job {self.job_id} MESSAGE - {contact_method} to {recipient} - {status}"
        )

class PerformanceLogger:
    """Logger for performance monitoring"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.start_times = {}
    
    def start_timer(self, operation: str) -> str:
        """Start timing an operation"""
        timer_id = f"{operation}_{datetime.now().timestamp()}"
        self.start_times[timer_id] = datetime.now()
        return timer_id
    
    def end_timer(self, timer_id: str, operation: str, additional_info: str = ""):
        """End timing and log duration"""
        if timer_id in self.start_times:
            duration = (datetime.now() - self.start_times[timer_id]).total_seconds()
            del self.start_times[timer_id]
            
            info = f" - {additional_info}" if additional_info else ""
            self.logger.info(f"PERFORMANCE - {operation} - {duration:.2f}s{info}")
        else:
            self.logger.warning(f"Timer {timer_id} not found for operation {operation}")

# Create default logger instance
logger = setup_logger(
    name="scrappy",
    level="INFO",
    log_file="logs/scrappy.log"
)

# Create specialized loggers
request_logger = RequestLogger(logger)
performance_logger = PerformanceLogger(logger)

def get_job_logger(job_id: int) -> JobLogger:
    """Get a job-specific logger"""
    return JobLogger(logger, job_id)

# Context manager for performance logging
class timer:
    """Context manager for timing operations"""
    
    def __init__(self, operation: str, additional_info: str = ""):
        self.operation = operation
        self.additional_info = additional_info
        self.timer_id = None
    
    def __enter__(self):
        self.timer_id = performance_logger.start_timer(self.operation)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timer_id:
            performance_logger.end_timer(self.timer_id, self.operation, self.additional_info)
