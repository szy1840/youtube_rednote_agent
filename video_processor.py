import asyncio
import logging
import os
import shutil
import subprocess
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from config import settings

class VideoProcessor:
    """Simplified video processor that uses VideoLingo's batch processor directly"""
    
    def __init__(self):
        # Use configured paths from settings
        self.storage_base = Path(settings.download_folder_path_normalized)
        self.input_folder = self.storage_base / "input"
        self.output_folder = Path(settings.processed_folder_path)
        self.videolingo_path = Path(settings.videolingo_path)
        
        # VideoLingo batch processor paths
        self.videolingo_batch_input = self.videolingo_path / "batch" / "input"
        self.videolingo_batch_output = self.videolingo_path / "batch" / "output"
        self.videolingo_tasks_file = self.videolingo_path / "batch" / "tasks_setting.xlsx"
        
        # Ensure directories exist
        self._ensure_folders_exist()
    
    def _ensure_folders_exist(self):
        """Create required folders if they don't exist"""
        self.storage_base.mkdir(parents=True, exist_ok=True)
        self.input_folder.mkdir(parents=True, exist_ok=True)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.videolingo_batch_input.mkdir(parents=True, exist_ok=True)
        self.videolingo_batch_output.mkdir(parents=True, exist_ok=True)
        
        logging.info("📁 DIRECTORY STRUCTURE:")
        logging.info(f"   📥 Storage base: {self.storage_base}")
        logging.info(f"   📥 Download folder: {self.input_folder}")
        logging.info(f"   📤 Final output folder: {self.output_folder}")
        logging.info(f"   🎯 VideoLingo path: {self.videolingo_path}")
        logging.info(f"   🎯 VideoLingo batch input: {self.videolingo_batch_input}")
        logging.info(f"   🎯 VideoLingo batch output: {self.videolingo_batch_output}")
        
        # Create and log absolute paths
        logging.info("📁 ABSOLUTE PATHS:")
        logging.info(f"   📥 Download: {self.input_folder.absolute()}")
        logging.info(f"   📤 Output: {self.output_folder.absolute()}")
        logging.info(f"   🎯 VideoLingo: {self.videolingo_path.absolute()}")

    async def download_video(self, video_url: str, video_title: str = "") -> Optional[Path]:
        """Download video from YouTube to configured storage directory"""
        try:
            # Generate safe filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = self._sanitize_filename(video_title) if video_title else "video"
            base_filename = f"{safe_title}_{timestamp}"
            
            # Download to configured storage
            cmd = [
                settings.python_executable, "-m", "yt_dlp",
                "--format", "best[height<=720]/best",  # Medium quality
                "--output", str(self.input_folder / f"{base_filename}.%(ext)s"),
                "--no-playlist",
                video_url
            ]
            
            logging.info(f"🎬 Downloading video: {video_url}")
            logging.info(f"📁 To configured storage: {self.input_folder}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=1800  # 30 minutes timeout
            )
            
            if result.returncode != 0:
                logging.error(f"❌ yt-dlp failed: {result.stderr}")
                return None
            
            # Find the downloaded video file
            video_files = list(self.input_folder.glob(f"{base_filename}.*"))
            video_files = [f for f in video_files if f.suffix.lower() in ['.mp4', '.webm', '.mkv', '.avi']]
            
            if not video_files:
                logging.error(f"❌ No video file found after download")
                return None
            
            video_file = video_files[0]
            logging.info(f"✅ Video downloaded: {video_file.name}")
            logging.info(f"📊 Size: {video_file.stat().st_size / 1024 / 1024:.1f} MB")
            
            return video_file
            
        except subprocess.TimeoutExpired:
            logging.error("❌ Video download timed out (30 minutes)")
            return None
        except Exception as e:
            logging.error(f"❌ Video download failed: {e}")
            return None

    async def process_with_videolingo(self, video_path: Path) -> Optional[Tuple[str, Path]]:
        """Process video using VideoLingo's batch processor directly"""
        try:
            logging.info(f"🎯 Processing with VideoLingo batch processor: {video_path.name}")
            
            # Step 0: Clean VideoLingo batch input directory first
            logging.info("🧹 Cleaning VideoLingo batch input directory...")
            if self.videolingo_batch_input.exists():
                for item in self.videolingo_batch_input.glob("*"):
                    try:
                        if item.is_file():
                            item.unlink()
                            logging.debug(f"🗑️ Removed old file: {item.name}")
                    except Exception as e:
                        logging.warning(f"⚠️ Failed to remove {item.name}: {e}")
            
            # Step 1: Copy video to VideoLingo batch input
            videolingo_video_path = self.videolingo_batch_input / video_path.name
            shutil.copy2(str(video_path), str(videolingo_video_path))
            logging.info(f"📄 Copied video to VideoLingo input: {videolingo_video_path.name}")
            
            # Step 2: Create VideoLingo task file
            self._create_videolingo_task(video_path.name)
            
            # Step 3: Run VideoLingo batch processor
            success = await self._run_videolingo_batch_processor()
            
            if not success:
                logging.error("❌ VideoLingo batch processor failed")
                return None
            
            # Step 4: Extract results from VideoLingo output
            english_text = self._extract_english_subtitles()
            processed_video = self._find_processed_video(video_path.stem)
            
            if not processed_video:
                logging.error("❌ Could not find VideoLingo processed video")
                return None
            
            # Step 5: Move final video to our output folder
            final_output_path = self.output_folder / f"{video_path.stem}_processed{processed_video.suffix}"
            
            logging.info("📋 FILE MOVEMENT:")
            logging.info(f"   🔄 Moving: {processed_video}")
            logging.info(f"   📤 To: {final_output_path}")
            
            shutil.move(str(processed_video), str(final_output_path))
            
            logging.info(f"✅ VideoLingo processing completed successfully")
            logging.info(f"📝 English text length: {len(english_text)} characters")
            logging.info(f"🎬 Final video: {final_output_path.name}")
            logging.info(f"📊 Final video size: {final_output_path.stat().st_size / 1024 / 1024:.1f} MB")
            
            # Step 6: Cleanup VideoLingo temporary files
            self._cleanup_videolingo_files()
            
            return english_text, final_output_path
            
        except Exception as e:
            logging.error(f"❌ VideoLingo processing failed: {e}")
            self._cleanup_videolingo_files()
            return None

    def _create_videolingo_task(self, video_filename: str):
        """Create VideoLingo task Excel file"""
        task_data = {
            'Video File': [video_filename],
            'Source Language': ['en'],  # English source
            'Target Language': [settings.target_language],  # Chinese target
            'Dubbing': [0],  # No dubbing
            'Status': [None]  # Empty status for new task
        }
        
        df = pd.DataFrame(task_data)
        df.to_excel(self.videolingo_tasks_file, index=False)
        logging.info(f"📋 Created VideoLingo task: {video_filename} -> Chinese (no dubbing)")

    async def _run_videolingo_batch_processor(self) -> bool:
        """Run VideoLingo batch processor"""
        try:
            # Change to VideoLingo directory and run batch processor
            original_cwd = os.getcwd()
            os.chdir(self.videolingo_path)
            
            try:
                cmd = [
                    settings.python_executable, 
                    "-c", 
                    "import sys; sys.path.insert(0, '.'); exec(open('batch/utils/batch_processor.py').read())"
                ]
                
                logging.info("🚀 Running VideoLingo batch processor...")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=3600  # 1 hour timeout
                )
                
                # Log VideoLingo output for debugging
                if result.stdout:
                    logging.info("📋 VideoLingo output:")
                    for line in result.stdout.split('\n')[-20:]:  # Last 20 lines
                        if line.strip():
                            logging.info(f"   {line}")
                
                if result.returncode == 0:
                    logging.info("✅ VideoLingo batch processor completed successfully")
                    
                    # Check if task was actually successful
                    if self.videolingo_tasks_file.exists():
                        import pandas as pd
                        try:
                            df = pd.read_excel(self.videolingo_tasks_file)
                            if len(df) > 0:
                                status = df.iloc[0]['Status']
                                logging.info(f"📊 VideoLingo task status: {status}")
                                if 'Error' in str(status):
                                    logging.error(f"❌ VideoLingo processing failed: {status}")
                                    return False
                        except Exception as e:
                            logging.warning(f"⚠️ Could not read task status: {e}")
                    
                    return True
                else:
                    logging.error(f"❌ VideoLingo batch processor failed with return code {result.returncode}")
                    if result.stderr:
                        logging.error(f"   Stderr: {result.stderr}")
                    if result.stdout:
                        logging.error(f"   Stdout: {result.stdout}")
                    return False
                    
            finally:
                os.chdir(original_cwd)
                
        except subprocess.TimeoutExpired:
            logging.error("❌ VideoLingo batch processor timed out (1 hour)")
            return False
        except Exception as e:
            logging.error(f"❌ VideoLingo batch processor error: {e}")
            return False

    def _extract_english_subtitles(self) -> str:
        """Extract English subtitles from VideoLingo output"""
        try:
            # Look for English text files in VideoLingo output directories
            search_dirs = [
                self.videolingo_batch_output,
                self.videolingo_path / "output"
            ]
            
            for search_dir in search_dirs:
                if not search_dir.exists():
                    continue
                    
                # Search for text files recursively
                for text_file in search_dir.rglob("*.txt"):
                    try:
                        if text_file.is_file():
                            with open(text_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Basic check for English content
                            if len(content) > 50 and any(word in content.lower() 
                                                       for word in ['the', 'and', 'is', 'a', 'to', 'of']):
                                logging.info(f"📝 Extracted English subtitles from: {text_file.name}")
                                return content.strip()
                    except Exception:
                        continue
            
            # Fallback message
            logging.warning("⚠️ Could not find English subtitles in VideoLingo output")
            return "Video processed by VideoLingo - English subtitles not available for content generation"
            
        except Exception as e:
            logging.error(f"❌ Failed to extract English subtitles: {e}")
            return "Error extracting subtitles"

    def _find_processed_video(self, video_stem: str) -> Optional[Path]:
        """Find the processed video from VideoLingo output"""
        try:
            video_extensions = ['.mp4', '.webm', '.mkv', '.avi']
            
            # Search in VideoLingo output directories
            search_dirs = [
                self.videolingo_batch_output,
                self.videolingo_path / "output"
            ]
            
            for search_dir in search_dirs:
                if not search_dir.exists():
                    continue
                    
                # Look for video files recursively
                for video_file in search_dir.rglob("*"):
                    if (video_file.is_file() and 
                        video_file.suffix.lower() in video_extensions):
                        logging.info(f"🎬 Found processed video: {video_file.name}")
                        return video_file
            
            return None
            
        except Exception as e:
            logging.error(f"❌ Failed to find processed video: {e}")
            return None

    def _cleanup_videolingo_files(self):
        """Clean up VideoLingo temporary files"""
        try:
            # Clean up directories
            cleanup_dirs = [
                self.videolingo_batch_input,
                self.videolingo_batch_output,
                self.videolingo_path / "output"
            ]
            
            for cleanup_dir in cleanup_dirs:
                if cleanup_dir.exists():
                    for item in cleanup_dir.glob("*"):
                        try:
                            if item.is_file():
                                item.unlink()
                            elif item.is_dir():
                                shutil.rmtree(item)
                        except Exception:
                            pass  # Ignore individual cleanup failures
            
            # Clean up task file
            if self.videolingo_tasks_file.exists():
                self.videolingo_tasks_file.unlink()
            
            logging.debug("🧹 Cleaned up VideoLingo temporary files")
            
        except Exception as e:
            logging.warning(f"⚠️ Failed to cleanup some files: {e}")

    def cleanup_temp_files(self, video_path: Path):
        """Clean up our temporary files"""
        try:
            # Remove the original downloaded video since processing is complete
            if video_path.exists():
                video_path.unlink()
                logging.debug(f"🧹 Removed processed video from input: {video_path.name}")
            
        except Exception as e:
            logging.warning(f"⚠️ Failed to cleanup temp files: {e}")

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for cross-platform compatibility"""
        import re
        
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\s+', '_', filename)
        filename = filename.strip('._')
        
        # Limit length
        if len(filename) > 50:
            filename = filename[:50]
        
        return filename or "video"

async def main():
    """Test the simplified video processor"""
    processor = VideoProcessor()
    
    # Test with a YouTube URL
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    video_path = await processor.download_video(test_url, "Test Video")
    
    if video_path:
        print(f"✅ Video downloaded: {video_path}")
        
        result = await processor.process_with_videolingo(video_path)
        if result:
            english_text, processed_video = result
            print(f"✅ Processing successful")
            print(f"📝 English text length: {len(english_text)}")
            print(f"🎬 Final video: {processed_video}")
        else:
            print("❌ Processing failed")
    else:
        print("❌ Download failed")

if __name__ == "__main__":
    asyncio.run(main()) 