from typing import Dict, Any, Tuple
from app.services.notifications.generator import NotificationGenerator
import random

class TemplateNotificationGenerator(NotificationGenerator):
    def __init__(self):
        self.templates = {
            "action": ["Ready for some action? {title} is waiting on your watchlist."],
            "sci-fi": ["Feeling like a sci-fi night? {title} is ready for you."],
            "drama": ["In the mood for a great story? {title} could be just right."],
            "comedy": ["Need a laugh? {title} is still waiting to be watched."],
            "movie": ["Your next great watch is right here: {title}."],
            "tv": ["Binge-worthy alert: {title} is on your watchlist."],
            "generic": ["Still haven't watched {title}? Tonight might be the night."]
        }

    async def generate(self, media_item: Dict[str, Any]) -> Tuple[str, str]:
        title = media_item.get("title", "this")
        genres = media_item.get("genres", [])
        media_type = media_item.get("media_type", "generic")
        
        genre_names = [g.get("name", "").lower() for g in genres] if isinstance(genres, list) else []
        
        selected_template = None
        for g in genre_names:
            if "action" in g and "action" in self.templates:
                selected_template = random.choice(self.templates["action"])
                break
            elif "sci-fi" in g or "science fiction" in g:
                selected_template = random.choice(self.templates["sci-fi"])
                break
            elif "drama" in g:
                selected_template = random.choice(self.templates["drama"])
                break
            elif "comedy" in g:
                selected_template = random.choice(self.templates["comedy"])
                break
                
        if not selected_template:
            if media_type == "movie":
                selected_template = random.choice(self.templates["movie"])
            elif media_type == "tv":
                selected_template = random.choice(self.templates["tv"])
            else:
                selected_template = random.choice(self.templates["generic"])
                
        return selected_template.format(title=title), "template"
