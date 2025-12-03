"""
High-performance file system monitor for automatic image processing.
Uses watchdog for real-time file system events with optimized processing.
"""
import os
import time
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from PIL import Image


class ImageFileHandler(FileSystemEventHandler):
    """
    Optimized file system event handler for image files.
    
    Performance features:
    - Debouncing to handle file write completion
    - Deduplication to avoid reprocessing
    - Thread pool for non-blocking verification
    - Efficient file type checking
    - Bounded queue to prevent memory exhaustion
    """
    
    VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    DEBOUNCE_SECONDS = 1.0
    
    def __init__(
        self, 
        process_callback: Callable,
        data_dir: str,
        executor: ThreadPoolExecutor,
        loop: asyncio.AbstractEventLoop,
        max_queue_size: int = 100
    ):
        """
        Initialize the handler.
        
        Args:
            process_callback: Async function to process images
            data_dir: Directory being monitored
            executor: Thread pool for blocking operations
            loop: Event loop for async operations
            max_queue_size: Maximum number of files that can be queued
        """
        self.process_callback = process_callback
        self.data_dir = data_dir
        self.executor = executor
        self.loop = loop
        self.max_queue_size = max_queue_size
        self.processing_files: Set[str] = set()
        self.pending_files: Set[str] = set()
        self.dropped_files: int = 0
        
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        filepath = event.src_path
        
        # Quick extension check before any I/O
        if not self._is_image_extension(filepath):
            return
        
        # Avoid duplicate processing
        if filepath in self.processing_files or filepath in self.pending_files:
            return
        
        # Check queue size limit
        total_queued = len(self.pending_files) + len(self.processing_files)
        if total_queued >= self.max_queue_size:
            self.dropped_files += 1
            filename = os.path.basename(filepath)
            print(f"[FileMonitor] Queue full ({total_queued}/{self.max_queue_size}), dropping: {filename} (total dropped: {self.dropped_files})")
            return
        
        self.pending_files.add(filepath)
        
        # Schedule debounced processing in thread pool
        self.executor.submit(self._debounce_and_process, filepath)
    
    def _is_image_extension(self, filepath: str) -> bool:
        """Fast extension check without file I/O."""
        return Path(filepath).suffix.lower() in self.VALID_EXTENSIONS
    
    def _debounce_and_process(self, filepath: str):
        """
        Wait for file write completion, verify, then process.
        Runs in thread pool to avoid blocking the event loop.
        """
        try:
            # Wait for file to be fully written
            time.sleep(self.DEBOUNCE_SECONDS)
            
            # Remove from pending
            self.pending_files.discard(filepath)
            
            # Check if file still exists and is readable
            if not os.path.exists(filepath):
                return
            
            # Verify it's a valid image without loading the full file
            try:
                with Image.open(filepath) as img:
                    img.verify()
            except Exception as e:
                print(f"Invalid image file {filepath}: {e}")
                return
            
            # Mark as processing
            self.processing_files.add(filepath)
            
            # Schedule async processing in the event loop
            asyncio.run_coroutine_threadsafe(
                self._process_file(filepath),
                self.loop
            )
            
        except Exception as e:
            print(f"Error in debounce for {filepath}: {e}")
            self.pending_files.discard(filepath)
    
    async def _process_file(self, filepath: str):
        """Process the file asynchronously."""
        try:
            print(f"[FileMonitor] Processing new file: {os.path.basename(filepath)}")
            await self.process_callback(filepath)
            print(f"[FileMonitor] Successfully processed: {os.path.basename(filepath)}")
        except Exception as e:
            print(f"[FileMonitor] Error processing {filepath}: {e}")
        finally:
            self.processing_files.discard(filepath)


class FileMonitor:
    """
    High-performance file system monitor.
    
    Manages the watchdog observer and provides lifecycle management.
    """
    
    def __init__(
        self,
        data_dir: str,
        process_callback: Callable,
        executor: ThreadPoolExecutor,
        loop: asyncio.AbstractEventLoop,
        max_queue_size: int = 100
    ):
        """
        Initialize the file monitor.
        
        Args:
            data_dir: Directory to monitor
            process_callback: Async function to process new files
            executor: Thread pool for blocking operations
            loop: Event loop for async operations
            max_queue_size: Maximum number of files that can be queued
        """
        self.data_dir = data_dir
        self.process_callback = process_callback
        self.executor = executor
        self.loop = loop
        self.max_queue_size = max_queue_size
        self.observer = None
        self.handler = None
    
    def start(self):
        """Start monitoring the directory."""
        if self.observer is not None:
            print("[FileMonitor] Already running")
            return
        
        print(f"[FileMonitor] Starting monitor for: {self.data_dir} (max queue: {self.max_queue_size})")
        
        self.handler = ImageFileHandler(
            self.process_callback,
            self.data_dir,
            self.executor,
            self.loop,
            self.max_queue_size
        )
        
        self.observer = Observer()
        self.observer.schedule(self.handler, self.data_dir, recursive=False)
        self.observer.start()
        
        print("[FileMonitor] Monitor started successfully")
    
    def stop(self):
        """Stop monitoring the directory."""
        if self.observer is None:
            return
        
        print("[FileMonitor] Stopping monitor...")
        self.observer.stop()
        self.observer.join(timeout=5)
        self.observer = None
        self.handler = None
        print("[FileMonitor] Monitor stopped")
    
    def is_running(self) -> bool:
        """Check if the monitor is running."""
        return self.observer is not None and self.observer.is_alive()
