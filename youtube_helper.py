import logging
import json
from typing import List, Dict, Optional
import requests
from datetime import datetime
from pathlib import Path
from config import settings

class YouTubeHelper:
    """Helper class for YouTube API operations and playlist management"""
    
    def __init__(self):
        self.api_key = settings.youtube_api_key
        self.playlist_id = settings.youtube_playlist_id
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
        if not self.api_key:
            logging.warning("YouTube API key not configured. Some functions will not work.")
    
    def get_playlist_videos(self) -> List[Dict]:
        """
        Get all videos from the specified playlist
        Returns list of video info dictionaries
        """
        if not self.api_key:
            logging.error("YouTube API key not configured")
            return []
        
        try:
            videos = []
            next_page_token = None
            
            while True:
                # Build API request URL
                url = f"{self.base_url}/playlistItems"
                params = {
                    'part': 'snippet,contentDetails',
                    'playlistId': self.playlist_id,
                    'key': self.api_key,
                    'maxResults': 50
                }
                
                if next_page_token:
                    params['pageToken'] = next_page_token
                
                logging.debug(f"[YouTube] Fetching playlist items: {url}")
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # Process each video
                for item in data.get('items', []):
                    snippet = item.get('snippet', {})
                    content_details = item.get('contentDetails', {})
                    
                    video_info = {
                        'playlist_item_id': item.get('id'),
                        'video_id': content_details.get('videoId'),
                        'title': snippet.get('title'),
                        'description': snippet.get('description'),
                        'published_at': snippet.get('publishedAt'),
                        'channel_title': snippet.get('videoOwnerChannelTitle'),
                        'url': f"https://www.youtube.com/watch?v={content_details.get('videoId')}",
                        'thumbnail_url': snippet.get('thumbnails', {}).get('medium', {}).get('url'),
                        'position': snippet.get('position')
                    }
                    
                    videos.append(video_info)
                
                # Check if there are more pages
                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    break
            
            logging.info(f"[YouTube] Found {len(videos)} videos in playlist {self.playlist_id}")
            return videos
            
        except requests.exceptions.RequestException as e:
            logging.error(f"[YouTube] API request failed: {e}")
            return []
        except Exception as e:
            logging.error(f"[YouTube] Error fetching playlist videos: {e}")
            return []
    
    def remove_video_from_playlist(self, playlist_item_id: str) -> bool:
        """
        Remove a video from the playlist by playlist item ID
        Returns True if successful, False otherwise
        """
        if not self.api_key:
            logging.error("YouTube API key not configured")
            return False
        
        try:
            url = f"{self.base_url}/playlistItems"
            params = {
                'id': playlist_item_id,
                'key': self.api_key
            }
            
            logging.info(f"[YouTube] Removing video from playlist: {playlist_item_id}")
            response = requests.delete(url, params=params, timeout=30)
            response.raise_for_status()
            
            logging.info(f"[YouTube] Successfully removed video from playlist")
            return True
            
        except requests.exceptions.RequestException as e:
            logging.error(f"[YouTube] Failed to remove video from playlist: {e}")
            return False
        except Exception as e:
            logging.error(f"[YouTube] Error removing video from playlist: {e}")
            return False
    
    def get_video_details(self, video_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific video
        Returns video details dictionary or None if failed
        """
        if not self.api_key:
            logging.error("YouTube API key not configured")
            return None
        
        try:
            url = f"{self.base_url}/videos"
            params = {
                'part': 'snippet,contentDetails,statistics',
                'id': video_id,
                'key': self.api_key
            }
            
            logging.debug(f"[YouTube] Fetching video details: {video_id}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                logging.warning(f"[YouTube] Video not found: {video_id}")
                return None
            
            item = items[0]
            snippet = item.get('snippet', {})
            content_details = item.get('contentDetails', {})
            statistics = item.get('statistics', {})
            
            video_details = {
                'video_id': video_id,
                'title': snippet.get('title'),
                'description': snippet.get('description'),
                'published_at': snippet.get('publishedAt'),
                'channel_title': snippet.get('channelTitle'),
                'channel_id': snippet.get('channelId'),
                'duration': content_details.get('duration'),
                'view_count': statistics.get('viewCount'),
                'like_count': statistics.get('likeCount'),
                'comment_count': statistics.get('commentCount'),
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url')
            }
            
            logging.debug(f"[YouTube] Retrieved video details: {snippet.get('title')}")
            return video_details
            
        except requests.exceptions.RequestException as e:
            logging.error(f"[YouTube] API request failed for video {video_id}: {e}")
            return None
        except Exception as e:
            logging.error(f"[YouTube] Error fetching video details {video_id}: {e}")
            return None
    
    def check_for_new_videos(self, processed_videos_file: str = "processed_videos.json") -> List[Dict]:
        """
        Check for new videos in the playlist that haven't been processed yet
        Returns list of new video info dictionaries
        """
        # Load previously processed videos
        processed_videos = self._load_processed_videos(processed_videos_file)
        
        # Get current playlist videos
        current_videos = self.get_playlist_videos()
        
        # Filter out already processed videos
        new_videos = []
        for video in current_videos:
            video_id = video.get('video_id')
            if video_id and video_id not in processed_videos:
                new_videos.append(video)
        
        if new_videos:
            logging.info(f"[YouTube] Found {len(new_videos)} new videos to process")
            for video in new_videos:
                logging.info(f"[YouTube] New video: {video.get('title')}")
        else:
            logging.info("[YouTube] No new videos found in playlist")
        
        return new_videos
    
    def mark_video_as_processed(self, video_id: str, processed_videos_file: str = "processed_videos.json"):
        """
        Mark a video as processed by adding it to the processed videos file
        """
        processed_videos = self._load_processed_videos(processed_videos_file)
        processed_videos[video_id] = {
            'processed_at': datetime.now().isoformat(),
            'status': 'completed'
        }
        self._save_processed_videos(processed_videos, processed_videos_file)
        logging.info(f"[YouTube] Marked video as processed: {video_id}")
    
    def _load_processed_videos(self, filename: str) -> Dict:
        """Load the processed videos tracking file"""
        try:
            if Path(filename).exists():
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logging.warning(f"[YouTube] Could not load processed videos file: {e}")
        return {}
    
    def _save_processed_videos(self, processed_videos: Dict, filename: str):
        """Save the processed videos tracking file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(processed_videos, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logging.error(f"[YouTube] Could not save processed videos file: {e}")
    
    def validate_api_configuration(self) -> bool:
        """
        Validate that the YouTube API is properly configured and accessible
        Returns True if valid, False otherwise
        """
        if not self.api_key:
            logging.error("[YouTube] API key not configured")
            return False
        
        try:
            # Test API access with a simple request
            url = f"{self.base_url}/playlists"
            params = {
                'part': 'snippet',
                'id': self.playlist_id,
                'key': self.api_key
            }
            
            logging.info("[YouTube] Validating API configuration...")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                logging.error(f"[YouTube] Playlist not found or not accessible: {self.playlist_id}")
                return False
            
            playlist_title = items[0].get('snippet', {}).get('title', 'Unknown')
            logging.info(f"[YouTube] API configuration valid. Playlist: '{playlist_title}'")
            return True
            
        except requests.exceptions.RequestException as e:
            logging.error(f"[YouTube] API validation failed: {e}")
            return False
        except Exception as e:
            logging.error(f"[YouTube] Error validating API: {e}")
            return False


# Example usage and testing
async def main():
    """Test the YouTube helper functionality"""
    youtube = YouTubeHelper()
    
    # Test API validation
    if not youtube.validate_api_configuration():
        print("❌ YouTube API configuration invalid")
        return
    
    print("✅ YouTube API configuration valid")
    
    # Test getting playlist videos
    videos = youtube.get_playlist_videos()
    print(f"📺 Found {len(videos)} videos in playlist")
    
    # Test checking for new videos
    new_videos = youtube.check_for_new_videos()
    print(f"🆕 Found {len(new_videos)} new videos to process")
    
    if new_videos:
        # Show details of first new video
        video = new_videos[0]
        print(f"First new video: {video.get('title')}")
        print(f"URL: {video.get('url')}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 