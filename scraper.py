import json
import os
import urllib.parse
import urllib.request
import re

# ልንፈልጋቸው ያሰብናቸው የትምህርት ዘርፎች እና ቁልፍ ቃላት (Search Keywords)
SEARCH_QUERIES = {
    "automotive": [
        "automotive repair tutorial",
        "car diagnostic code OBD2 tutorial",
        "car engine working animation 3d"
    ],
    "electronics": [
        "electronics tutorial for beginners",
        "arduino projects tutorial",
        "circuit design basics"
    ],
    "coding": [
        "python programming tutorial",
        "fastapi tutorial for beginners",
        "web scraping tutorial python"
    ],
    "automation": [
        "industrial automation plc tutorial",
        "robotics tutorial for beginners",
        "mechatronics engineering tutorial"
    ]
}

def search_youtube_videos(query, max_results=3):
    """የተሰጠውን ቁልፍ ቃል በመጠቀም ከYouTube የቪዲዮ መረጃዎችን አውጥቶ ያመጣል"""
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={encoded_query}"
    
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    
    videos = []
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
        # Video ID እና Title ከHTML ለመንቀስቀስ
        video_ids = re.findall(r"watch\?v=(\w{11})", html)
        
        # የተደጋገሙ IDዎችን ማስወገድ
        unique_ids = []
        for vid in video_ids:
            if vid not in unique_ids:
                unique_ids.append(vid)
                
        for vid in unique_ids[:max_results]:
            video_url = f"https://www.youtube.com/watch?v={vid}"
            videos.append({
                "id": vid,
                "title": f"Tutorial Video ({query})",
                "url": video_url,
                "embed_url": f"https://www.youtube.com/embed/{vid}"
            })
    except Exception as e:
        print(f"Error searching for {query}: {e}")
        
    return videos

def main():
    print("🚀 Starting educational video scraping...")
    dataset = {}

    for category, queries in SEARCH_QUERIES.items():
        print(f"🔍 Scraping category: {category}...")
        category_videos = []
        for query in queries:
            results = search_youtube_videos(query, max_results=2)
            category_videos.extend(results)
        
        # ID ድግግሞሽን ለማስወገድ
        seen_ids = set()
        deduped_videos = []
        for v in category_videos:
            if v["id"] not in seen_ids:
                seen_ids.add(v["id"])
                deduped_videos.append(v)
                
        dataset[category] = deduped_videos

    # ዳታውን ወደ json ፋይል ማስቀመጥ
    output_filename = "videos_data.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"✅ Scraping finished! Data saved to {output_filename}")

if __name__ == "__main__":
    main()
