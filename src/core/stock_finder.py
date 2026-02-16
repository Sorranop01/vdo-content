
import logging
import os
import requests
import random
from typing import List, Dict
from dotenv import load_dotenv

logger = logging.getLogger("vdo_content.stock_finder")

class StockVideoFinder:
    """
    Finds free stock videos using Pexels API.
    """
    
    BASE_URL = "https://api.pexels.com/videos"
    
    def __init__(self, api_key: str = None):
        if not api_key:
            load_dotenv()
            self.api_key = os.getenv("PEXELS_API_KEY")
        else:
            self.api_key = api_key
            
    def is_available(self) -> bool:
        return bool(self.api_key)
        
    def search_video(self, query: str, orientation: str = "landscape", per_page: int = 5) -> List[Dict]:
        """
        Search for videos on Pexels.
        
        Args:
            query: Search keywords (e.g. "business meeting", "ocean waves")
            orientation: landscape, portrait, or square
            per_page: Number of results
            
        Returns:
            List of video objects {id, image, video_files, duration, user}
        """
        if not self.is_available():
            return []
            
        headers = {"Authorization": self.api_key}
        params = {
            "query": query,
            "orientation": orientation,
            "size": "medium",
            "per_page": per_page
        }
        
        try:
            response = requests.get(f"{self.BASE_URL}/search", headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._process_results(data.get("videos", []))
            else:
                logger.warning(f"Pexels API Error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Stock video search failed: {e}")
            return []
            
    def _process_results(self, videos: List[Dict]) -> List[Dict]:
        """Extract relevant info from Pexels response"""
        results = []
        for v in videos:
            # Find best video file (HD quality but not too huge)
            video_files = v.get("video_files", [])
            # Sort by width (resolution) descending
            video_files.sort(key=lambda x: x.get("width", 0), reverse=True)
            
            # Prefer HD (1920x1080) or HD-ish
            best_file = next((f for f in video_files if f.get("width") == 1920), video_files[0] if video_files else None)
            
            if best_file:
                results.append({
                    "id": v.get("id"),
                    "thumbnail": v.get("image"),
                    "duration": v.get("duration"),
                    "url": best_file.get("link"),
                    "width": best_file.get("width"),
                    "height": best_file.get("height"),
                    "photographer": v.get("user", {}).get("name", "Unknown")
                })
        return results

# Convenience
def search_stock_videos(query: str, api_key: str = None) -> List[Dict]:
    finder = StockVideoFinder(api_key)
    return finder.search_video(query)
