"""
MinerU API processor for document analysis.
API Documentation: https://mineru.net/apiManage/docs
"""
import os
import time
import requests
import tempfile
from typing import Optional, Tuple, Dict, Any
from pathlib import Path


class MinerUProcessor:
    """MinerU cloud API processor for document analysis."""
    
    # API endpoints
    UPLOAD_ENDPOINT = "/api/v4/file-urls/batch"
    TASK_ENDPOINT = "/api/v4/extract/task"
    RESULT_ENDPOINT = "/api/v4/extract/task/{task_id}"
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        base_url: str = "https://mineru.net"
    ):
        """
        Initialize MinerU API processor.
        
        Args:
            api_key: MinerU API key (from environment if not provided)
            base_url: MinerU API base URL
        """
        self.api_key = api_key or os.getenv('MINERU_API_KEY', '')
        self.base_url = base_url.rstrip('/')
        self.timeout = int(os.getenv('MINERU_TIMEOUT', '600'))  # 10 minutes default
        self.poll_interval = int(os.getenv('MINERU_POLL_INTERVAL', '5'))  # 5 seconds
        
        if not self.api_key:
            print("WARNING: MINERU_API_KEY not set, MinerU processor will not work")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _upload_file(self, pdf_path: str) -> Optional[str]:
        """
        Upload PDF file and get file URL for processing.
        
        Args:
            pdf_path: Local path to PDF file
            
        Returns:
            File URL for MinerU processing, or None on failure
        """
        try:
            # Step 1: Get presigned upload URL
            file_name = Path(pdf_path).name
            file_size = os.path.getsize(pdf_path)
            
            response = requests.post(
                f"{self.base_url}{self.UPLOAD_ENDPOINT}",
                headers=self._get_headers(),
                json={
                    "files": [{
                        "name": file_name,
                        "size": file_size,
                        "is_ocr": True
                    }]
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                print(f"MinerU upload URL request failed: {result.get('msg')}")
                return None
            
            upload_info = result.get("data", {}).get("files", [{}])[0]
            presigned_url = upload_info.get("presigned_url")
            file_url = upload_info.get("url")
            
            if not presigned_url or not file_url:
                print("MinerU: Failed to get upload URLs")
                return None
            
            # Step 2: Upload file to presigned URL
            with open(pdf_path, 'rb') as f:
                upload_response = requests.put(
                    presigned_url,
                    data=f,
                    headers={"Content-Type": "application/pdf"},
                    timeout=120
                )
                upload_response.raise_for_status()
            
            print(f"MinerU: File uploaded successfully, URL: {file_url}")
            return file_url
            
        except requests.RequestException as e:
            print(f"MinerU upload error: {e}")
            return None
        except Exception as e:
            print(f"MinerU upload unexpected error: {e}")
            return None
    
    def _create_task(self, file_url: str, enable_formula: bool = True) -> Optional[str]:
        """
        Create extraction task.
        
        Args:
            file_url: URL of uploaded file
            enable_formula: Whether to enable formula recognition
            
        Returns:
            Task ID, or None on failure
        """
        try:
            response = requests.post(
                f"{self.base_url}{self.TASK_ENDPOINT}",
                headers=self._get_headers(),
                json={
                    "url": file_url,
                    "is_ocr": True,
                    "enable_formula": enable_formula,
                    "enable_table": True,
                    "layout_model": "doclayout_yolo",
                    "language": "ch"
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                print(f"MinerU task creation failed: {result.get('msg')}")
                return None
            
            task_id = result.get("data", {}).get("task_id")
            print(f"MinerU: Task created, ID: {task_id}")
            return task_id
            
        except requests.RequestException as e:
            print(f"MinerU task creation error: {e}")
            return None
    
    def _poll_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Poll task status until completion.
        
        Args:
            task_id: Task ID to poll
            
        Returns:
            Task result data, or None on failure/timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            try:
                response = requests.get(
                    f"{self.base_url}{self.RESULT_ENDPOINT.format(task_id=task_id)}",
                    headers=self._get_headers(),
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("code") != 0:
                    print(f"MinerU task poll error: {result.get('msg')}")
                    return None
                
                data = result.get("data", {})
                status = data.get("state")
                
                if status == "done":
                    print(f"MinerU: Task completed successfully")
                    return data
                elif status == "failed":
                    print(f"MinerU: Task failed - {data.get('err_msg', 'Unknown error')}")
                    return None
                else:
                    # Still processing
                    progress = data.get("progress", 0)
                    print(f"MinerU: Task in progress... {progress}%")
                    time.sleep(self.poll_interval)
                    
            except requests.RequestException as e:
                print(f"MinerU poll error: {e}")
                time.sleep(self.poll_interval)
        
        print(f"MinerU: Task timeout after {self.timeout} seconds")
        return None
    
    def _download_result(
        self, 
        task_data: Dict[str, Any], 
        output_path: Path,
        arxiv_id: str
    ) -> Tuple[Optional[str], list]:
        """
        Download markdown and images from task result.
        
        Args:
            task_data: Task result data from API
            output_path: Output directory path
            arxiv_id: ArXiv paper ID for naming
            
        Returns:
            Tuple of (markdown text, list of saved files)
        """
        saved_files = []
        markdown_text = ""
        
        try:
            # Get result URLs
            full_result = task_data.get("full_zip_url")
            md_url = task_data.get("md_url")
            
            # Download markdown
            if md_url:
                response = requests.get(md_url, timeout=60)
                response.raise_for_status()
                markdown_text = response.text
                
                # Save markdown file
                base_filename = arxiv_id if arxiv_id != "unknown" else "document"
                md_file_path = output_path / f"{base_filename}_mineru.md"
                with open(md_file_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_text)
                saved_files.append(str(md_file_path))
                print(f"MinerU: Markdown saved to {md_file_path}")
            
            # Download and extract images from zip if available
            if full_result:
                import zipfile
                import io
                
                response = requests.get(full_result, timeout=120)
                response.raise_for_status()
                
                imgs_dir = output_path / "imgs"
                imgs_dir.mkdir(exist_ok=True)
                
                with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                    for name in zf.namelist():
                        if name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                            # Extract image
                            img_data = zf.read(name)
                            img_name = Path(name).name
                            img_path = imgs_dir / img_name
                            with open(img_path, 'wb') as f:
                                f.write(img_data)
                            saved_files.append(str(img_path))
                
                print(f"MinerU: Extracted {len(saved_files) - 1} images")
            
            return markdown_text, saved_files
            
        except Exception as e:
            print(f"MinerU download error: {e}")
            return markdown_text, saved_files

    def process_pdf(
        self, 
        pdf_path: str, 
        max_pages: int = 25,
        output_path: Optional[str] = None,
        arxiv_id: str = "unknown"
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Process PDF using MinerU API (same interface as PaddleOCR processor).
        
        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum pages to process (for compatibility, MinerU handles internally)
            output_path: Output directory path
            arxiv_id: ArXiv paper ID for naming
            
        Returns:
            Tuple of (OCR markdown text, status info dict)
        """
        if not self.api_key:
            return None, {
                'error': 'MINERU_API_KEY not configured',
                'total_pages': 0,
                'processed_pages': 0,
                'is_oversized': False,
                'char_count': 0,
                'method': 'mineru',
                'saved_files': []
            }
        
        try:
            # Get page count using PyMuPDF
            import fitz
            pdf_document = fitz.open(pdf_path)
            total_pages = len(pdf_document)
            pdf_document.close()
            
            print(f"MinerU: PDF总页数: {total_pages}")
            
            is_oversized = total_pages > max_pages
            if is_oversized:
                print(f"MinerU: 文档页数({total_pages})超过限制({max_pages})")
            
            # Create output directory
            if output_path:
                output_dir = Path(output_path)
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = Path(tempfile.mkdtemp())
            
            print(f"MinerU: 输出目录: {output_dir}")
            
            # Step 1: Upload file
            print("MinerU: 开始上传文件...")
            file_url = self._upload_file(pdf_path)
            if not file_url:
                return None, {
                    'error': 'Failed to upload file to MinerU',
                    'total_pages': total_pages,
                    'processed_pages': 0,
                    'is_oversized': is_oversized,
                    'char_count': 0,
                    'method': 'mineru',
                    'saved_files': []
                }
            
            # Step 2: Create extraction task
            print("MinerU: 创建提取任务...")
            task_id = self._create_task(file_url)
            if not task_id:
                return None, {
                    'error': 'Failed to create MinerU task',
                    'total_pages': total_pages,
                    'processed_pages': 0,
                    'is_oversized': is_oversized,
                    'char_count': 0,
                    'method': 'mineru',
                    'saved_files': []
                }
            
            # Step 3: Poll for completion
            print("MinerU: 等待任务完成...")
            task_data = self._poll_task(task_id)
            if not task_data:
                return None, {
                    'error': 'MinerU task failed or timed out',
                    'total_pages': total_pages,
                    'processed_pages': 0,
                    'is_oversized': is_oversized,
                    'char_count': 0,
                    'method': 'mineru',
                    'saved_files': []
                }
            
            # Step 4: Download results
            print("MinerU: 下载结果...")
            markdown_text, saved_files = self._download_result(task_data, output_dir, arxiv_id)
            
            if not markdown_text:
                markdown_text = f"# OCR Analysis for {arxiv_id}\n\nMinerU processing completed but no text content was extracted."
            
            # Count images
            images_count = len([f for f in saved_files if not f.endswith('.md')])
            
            status_info = {
                'total_pages': total_pages,
                'processed_pages': total_pages,  # MinerU processes all pages
                'is_oversized': is_oversized,
                'char_count': len(markdown_text),
                'method': 'mineru',
                'images_count': images_count,
                'saved_files': saved_files,
                'task_id': task_id
            }
            
            print(f"MinerU: OCR完成，处理了 {total_pages} 页，提取 {len(markdown_text)} 字符，{images_count} 张图片")
            
            return markdown_text, status_info
            
        except Exception as e:
            print(f"MinerU processing error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, {
                'error': f'MinerU processing error: {str(e)}',
                'total_pages': 0,
                'processed_pages': 0,
                'is_oversized': False,
                'char_count': 0,
                'method': 'mineru',
                'saved_files': []
            }


# Singleton instance for easy import
_mineru_processor: Optional[MinerUProcessor] = None

def get_mineru_processor() -> MinerUProcessor:
    """Get or create MinerU processor singleton."""
    global _mineru_processor
    if _mineru_processor is None:
        _mineru_processor = MinerUProcessor()
    return _mineru_processor
