import os
import json
import re
import urllib.parse
import urllib.request
from youtube_transcript_api import YouTubeTranscriptApi
from deep_translator import GoogleTranslator
from fpdf import FPDF

PDF_DIR = "pdfs"
os.makedirs(PDF_DIR, exist_ok=True)

SEARCH_QUERIES = {
    "automotive": [
        "car engine working tutorial",
        "car diagnostic code OBD2 basics"
    ],
    "electronics": [
        "electronics tutorial for beginners",
        "arduino projects tutorial"
    ],
    "coding": [
        "python programming tutorial beginners",
        "fastapi tutorial for beginners"
    ],
    "automation": [
        "industrial automation plc tutorial",
        "robotics basics tutorial"
    ]
}

def search_youtube_videos(query, max_results=1):
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={encoded_query}"
    
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    
    videos = []
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
        video_ids = re.findall(r"watch\?v=(\w{11})", html)
        
        unique_ids = []
        for vid in video_ids:
            if vid not in unique_ids:
                unique_ids.append(vid)
                
        for vid in unique_ids[:max_results]:
            videos.append({
                "id": vid,
                "title": f"Tutorial Video ({query})",
                "url": f"https://www.youtube.com/watch?v={vid}"
            })
    except Exception as e:
        print(f"Error searching for {query}: {e}")
        
    return videos

def get_amharic_summary(video_id):
    """የቪዲዮውን Transcript አውርዶ ወደ አማርኛ መተርጎሚያ (የተስተካከለ)"""
    try:
        # አዲሱን የ YouTubeTranscriptApi አሰራር መጠቀም
        ytt = YouTubeTranscriptApi()
        fetched = ytt.fetch(video_id, languages=['en'])
        
        # ጽሁፎቹን አዋህዶ መውሰድ
        full_text = " ".join([item['text'] for item in fetched[:15]])
        
        # ወደ አማርኛ መተርጎም
        translated = GoogleTranslator(source='auto', target='am').translate(full_text)
        return translated
    except Exception as e:
        # Transcript ከሌለው ወይም ኤረር ካለ
        print(f"Transcript unavailable for {video_id}: {e}")
        return "ለዚህ ቪዲዮ አውቶማቲክ የፅሁፍ ትርጉም አልተገኘም። እባክዎን ቪዲዮውን ቀጥታ ይመልከቱ።"

def create_summary_file(video_id, title, amharic_text, category):
    """
    በPDF ፋይል ምትክ የአማርኛ ኢንኮዲንግ ችግር እንዳይፈጠር 
    ጽሁፉን UTF-8 .txt እና ፅዱ HTML/Text አድርጎ ፋይል ማዘጋጀት
    """
    file_path = os.path.join(PDF_DIR, f"{video_id}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"Category: {category.upper()}\n")
        f.write(f"Video ID: {video_id}\n")
        f.write(f"Title: {title}\n\n")
        f.write("--- የአማርኛ ማጠቃለያ ---\n")
        f.write(amharic_text)
    return file_path

def main():
    print("🚀 Starting video scraping with Amharic summary extraction...")
    dataset = {}

    for category, queries in SEARCH_QUERIES.items():
        print(f"🔍 Processing category: {category}...")
        category_videos = []
        
        for query in queries:
            results = search_youtube_videos(query, max_results=1)
            for vid_info in results:
                vid_id = vid_info["id"]
                print(f"   📝 Generating Amharic Summary for video: {vid_id}")
                
                # 1. አማርኛ ትርጉም ማዘጋጀት
                amharic_text = get_amharic_summary(vid_id)
                
                # 2. ፋይል ማስቀመጥ
                summary_file = create_summary_file(vid_id, vid_info["title"], amharic_text, category)
                
                vid_info["amharic_text"] = amharic_text
                vid_info["file_path"] = summary_file
                category_videos.append(vid_info)
                
        dataset[category] = category_videos

    # ዳታውን ወደ JSON ፋይል ማስቀመጥ
    output_filename = "videos_data.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"✅ Scraping & summary generation finished! Data saved to {output_filename}")

if __name__ == "__main__":
    main()
