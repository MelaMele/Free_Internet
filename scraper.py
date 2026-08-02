import os
import json
import re
import urllib.parse
import urllib.request
from youtube_transcript_api import YouTubeTranscriptApi
from deep_translator import GoogleTranslator
from fpdf import FPDF

# PDFዎች የሚቀመጡበት ፎልደር
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
    """ከYouTube የቪዲዮ IDዎችን እና መረጃዎችን መፈለጊያ"""
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
                "title": f"የትምህርት ቪዲዮ ({query})",
                "url": f"https://www.youtube.com/watch?v={vid}"
            })
    except Exception as e:
        print(f"Error searching for {query}: {e}")
        
    return videos

def get_amharic_summary(video_id):
    """የቪዲዮውን Transcript አውርዶ ወደ አማርኛ መተርጎሚያ"""
    try:
        # የቪዲዮውን Subtitle/Transcript ማውረድ
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        full_text = " ".join([item['text'] for item in transcript_list[:15]]) # የመጀመሪያዎቹን ጥቂት አረፍተ ነገሮች መውሰድ
        
        # ወደ አማርኛ መተርጎም
        translated = GoogleTranslator(source='auto', target='am').translate(full_text)
        return translated
    except Exception as e:
        print(f"Could not extract transcript for {video_id}: {e}")
        return "ለዚህ ቪዲዮ የጽሁፍ ትርጉም ማዘጋጀት አልተቻለም። እባክዎን ቪዲዮውን ቀጥታ ይመልከቱ።"

def create_pdf(video_id, title, amharic_text, category):
    """የተተረጎመውን ጽሁፍ ወደ PDF ፋይል መቀየሪያ"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt=f"Category: {category.upper()}", ln=1, align='C')
    pdf.cell(200, 10, txt=f"Video ID: {video_id}", ln=2, align='C')
    pdf.ln(10)
    
    # የጽሁፉን ይዘት በPDF ውስጥ ማስገባት
    pdf.multi_cell(0, 10, txt=f"Amharic Summary:\n\n{amharic_text}")
    
    pdf_filename = os.path.join(PDF_DIR, f"{video_id}.pdf")
    pdf.output(pdf_filename)
    return pdf_filename

def main():
    print("🚀 Starting video scraping with Amharic PDF generation...")
    dataset = {}

    for category, queries in SEARCH_QUERIES.items():
        print(f"🔍 Processing category: {category}...")
        category_videos = []
        
        for query in queries:
            results = search_youtube_videos(query, max_results=1)
            for vid_info in results:
                vid_id = vid_info["id"]
                print(f"   📄 Generating Amharic PDF for video: {vid_id}")
                
                # 1. አማርኛ ትርጉም ማዘጋጀት
                amharic_text = get_amharic_summary(vid_id)
                
                # 2. PDF ፋይል መፍጠር
                pdf_path = create_pdf(vid_id, vid_info["title"], amharic_text, category)
                
                vid_info["amharic_text"] = amharic_text
                vid_info["pdf_path"] = pdf_path
                category_videos.append(vid_info)
                
        dataset[category] = category_videos

    # ዳታውን ወደ JSON ፋይል ማስቀመጥ
    output_filename = "videos_data.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"✅ Scraping & PDF generation finished! Data saved to {output_filename}")

if __name__ == "__main__":
    main()
