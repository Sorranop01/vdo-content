#!/usr/bin/env python3
"""
Thai to English UI Conversion Script
Converts all UI strings in app.py from Thai to English
"""

# Mapping of Thai UI strings to English
UI_TRANSLATIONS = {
    # Page Titles
    "1️⃣ Ideation - วางแผนเรื่องราว": "1️⃣ Ideation - Story Planning",
    "2️⃣ Script - สร้างบทพากย์": "2️⃣ Script - Create Narration",
    "3️⃣ Audio Sync - วิเคราะห์เสียง": "3️⃣ Audio Sync - Analyze Audio",
    "4️⃣ Prompts - สร้าง Veo Prompts": "4️⃣ Prompts - Generate Veo Prompts",
    "5️⃣ Export - ส่งออกผลลัพธ์": "5️⃣ Export - Export Results",
    
    # Workflow descriptions
    "ใส่หัวข้อที่ต้องการ → AI วิเคราะห์และสร้างโครงเรื่อง → อนุมัติ/ไม่อนุมัติ": "Enter topic → AI analyzes and creates story outline → Approve/Reject",
    
    # Form labels
    "💡 หัวข้อ/เนื้อหาที่ต้องการสร้าง": "💡 Topic/Content to Create",
    "เช่น บทบาทของ AI ในอนาคต, วิธีทำกาแฟ, รีวิวโทรศัพท์มือถือ": "e.g., Role of AI in the future, How to make coffee, Phone review",
    "### 🎬 ประเภทคอนเทนต์": "### 🎬 Content Type",
    "เลือกประเภทคอนเทนต์": "Select Content Type",
    "⚙️ การตั้งค่าเพิ่มเติม": "⚙️ Advanced Settings", 
    "⏱️ ความยาวเป้าหมาย (วินาที)": "⏱️ Target Duration (seconds)",
    
    # Buttons
    "🔍 วิเคราะห์โจทย์": "🔍 Analyze Topic",
    "💾 บันทึกร่าง": "💾 Save Draft",
    "✅ อนุมัติโครงเรื่อง": "✅ Approve Outline",
    "❌ ปฏิเสธ ขอแก้ไข": "❌ Reject & Revise",
    "📝 สร้างบทพากย์ด้วย AI": "📝 Generate Script with AI",
    "🎙️ สร้างเสียงพากย์": "🎙️ Generate Voice",
    "🎬 สร้าง Prompts": "🎬 Generate Prompts",
    
    # Section headers
    "📋 โครงเรื่อง": "📋 Story Outline",
    "🔍 การวิเคราะห์:": "🔍 Analysis:",
    "📖 โครงเรื่อง:": "📖 Outline:",
    "💡 จุดสำคัญ:": "💡 Key Points:",
    "📝 สร้างบทพากย์": "📝 Create Script",
    "⚙️ Settings": "⚙️ Settings",
    "🎭 สไตล์การเขียน (Tone)": "🎭 Writing Style (Tone)",
    "ปรับแต่งน้ำเสียง (Voice Tone)": "Adjust Voice Tone",
    
    # Messages  
    "กรุณาใส่ DeepSeek API Key ใน Settings (sidebar)": "Please enter DeepSeek API Key in Settings (sidebar)",
    "🤔 กำลังวิเคราะห์...": "🤔 Analyzing...",
    "💾 มีร่างที่ยังไม่ได้บันทึก": "💾 Unsaved draft available",
    "✅ บันทึกร่างแล้ว!": "✅ Draft saved!",
    "⚠️ ไม่สามารถบันทึกร่างได้": "⚠️ Could not save draft",
    "⚠️ ไม่พบข้อมูล Video Profiles กรุณาติดต่อผู้ดูแลระบบ": "⚠️ Video profiles not found. Please contact administrator",
    
   # Dropdown options - Content Type  
    "เลือกน้ำเสียงของบทพูด": "Select narration tone",
    
    # Dropdown options - Writing Style
    "Conversational (เป็นกันเอง)": "Conversational (Casual)",
    "Professional (ทางการ)": "Professional (Formal)",
    "Storytelling (เล่าเรื่อง)": "Storytelling (Narrative)",
    "Sales/Persuasive (ขายของ)": "Sales/Persuasive",
    "Educational (ให้ความรู้)": "Educational (Informative)",
    "Humorous (ตลก)": "Humorous (Funny)",
    "Dramatic (ดราม่า)": "Dramatic",
    "Urgent (เร่งรีบ/ตื่นเต้น)": "Urgent (Exciting)",
    
    # Voice Tone options
    "Default (เดิม)": "Default",
    "Warm & Friendly (อบอุ่น เป็นมิตร)": "Warm & Friendly",
    "Professional & Clear (ทางการ ชัดเจน)": "Professional & Clear",
    "Excited & Energetic (ตื่นเต้น มีพลัง)": "Excited & Energetic",
    "Calm & Soothing (สงบ ผ่อนคลาย)": "Calm & Soothing",
    "Serious & Authoritative (จริงจัง น่าเชื่อถือ)": "Serious & Authoritative",
    "Bright & Cheerful (สดใส ร่าเริง)": "Bright & Cheerful",
    
    # Aspect Ratio
    "16:9 (แนวนอน - YouTube)": "16:9 (Landscape - YouTube)",
    "9:16 (แนวตั้ง - TikTok/Reels)": "9:16 (Portrait - TikTok/Reels)",
    "1:1 (สี่เหลี่ยม - IG)": "1:1 (Square - Instagram)",
    "21:9 (Ultrawide)": "21:9 (Ultrawide)",
    
    # Video techniques
    "เลือกเทคนิคพิเศษ (จะนำไปผสมใน Prompt)": "Select special techniques (will be mixed into prompts)",
    "เทคนิคเหล่านี้จะถูกเพิ่มเข้าไปใน prompt ของทุกฉาก": "These techniques will be added to every scene's prompt",
    "Stop Motion (สต็อปโมชัน)": "Stop Motion",
    "Hyperlapse (ไฮเปอร์แลปส์)": "Hyperlapse",
    "Slow Motion (สโลว์โมชัน)": "Slow Motion",
    "Drone Shot (มุมโดรน)": "Drone Shot",
    "Handheld (กล้องมือถือ)": "Handheld",
    "Cinematic (ภาพยนตร์)": "Cinematic",
    "Match Cut (แมทช์คัท)": "Match Cut",
    "Macro (ระยะใกล้มาก)": "Macro (Extreme Close-up)",
    "Minimalist (มินิมอล)": "Minimalist",
    "Vintage Film (ฟิล์มเก่า)": "Vintage Film",
}

def convert_file(input_path, output_path=None):
    """Convert Thai strings to English in a file"""
    if output_path is None:
        output_path = input_path
    
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply all translations
    for thai, english in UI_TRANSLATIONS.items():
        content = content.replace(thai, english)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Converted {len(UI_TRANSLATIONS)} strings")
    print(f"📝 Saved to: {output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        convert_file(sys.argv[1])
    else:
        print("Usage: python convert_ui.py <file_path>")
