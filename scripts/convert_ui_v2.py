#!/usr/bin/env python3
"""
Comprehensive Thai to English UI Conversion Script v2
Converts ALL remaining UI strings in app.py from Thai to English
"""

# Complete mapping of Thai UI strings to English
UI_TRANSLATIONS = {
    # Navigation & Buttons
    "← ย้อนกลับ": "← Back",
    "🏠 กลับ Home": "🏠 Back to Home",
    "➕ สร้างโปรเจคใหม่": "➕ Create New Project",
    "✏️ แก้ไขชื่อ": "✏️ Edit Title",
    "เปลี่ยนชื่อโปรเจค": "Rename Project",
    "ชื่อใหม่": "New Title",
    "บันทึก": "Save",
    "บันทึกแล้ว!": "Saved!",
    "✅ อนุมัติ": "✅ Approve",
    "❌ ไม่อนุมัติ (ให้คิดใหม่)": "❌ Reject & Revise",
    "← ไปหน้า Ideation": "← Go to Ideation",
    
    # Project & Form Labels
    "📌 ชื่อโปรเจค": "📌 Project Title",
    "เช่น: ลดน้ำหนัก 2 เดือน": "e.g., Weight Loss in 2 Months",
    "บันทึกร่างลงฐานข้อมูล": "Save draft to database",
    "📝 เหตุผลที่ไม่อนุมัติ": "📝 Rejection Reason",
    
    # Messages & Status
    "ยังไม่มีโปรเจค กด 'สร้างโปรเจคใหม่' เพื่อเริ่มต้น": "No projects yet. Click 'Create New Project' to begin",
    "⚠️ กดเลือกข้อความด้านล่างแล้ว Ctrl+C": "⚠️ Select text below and press Ctrl+C",
    "🔑 API Key: ตั้งค่าแล้ว ✅": "🔑 API Key: Configured ✅",
    "🔑 API Key: ไม่พบ (ตั้งค่าใน .env)": "🔑 API Key: Not found (configure in .env)",
    "ไม่มีข้อมูล": "No data available",
    "✅ อนุมัติแล้ว! ไปหน้า Script →": "✅ Approved! Go to Script →",
    
    # Section Headers
    "ขั้นตอนการทำงาน": "Workflow Steps",
    
    # Character Reference Warning
    "⚠️ **Character Reference สั้นเกินไป**": "⚠️ **Character Reference too short**",
    "ตัวอักษร": "characters",
    "เพื่อให้วิดีโอทุกฉากสอดคล้องกัน ควรใส่รายละเอียดตัวละครให้มากขึ้น เช่น:": "For consistent video across scenes, add more character details such as:",
    "- เพศ, อายุ, เชื้อชาติ": "- Gender, age, ethnicity",
    "- เสื้อผ้า (สี, แบบ, สไตล์)": "- Clothing (color, style, type)",
    "- ลักษณะเด่น (ทรงผม, แว่นตา)": "- Distinctive features (hairstyle, glasses)",
    
    # Visual Styles
    "Realistic (สมจริง)": "Realistic",
    "Anime (อนิเมะ)": "Anime",
    "Cinematic (หนัง)": "Cinematic",
    "Documentary (สารคดี)": "Documentary",
    "Energetic (สนุกสนาน)": "Energetic",
    "Digital Art (ดิจิทัล)": "Digital Art",
    "Oil Painting (สีน้ำมัน)": "Oil Painting",
    "Watercolor (สีน้ำ)": "Watercolor",
    "Cartoon (การ์ตูน)": "Cartoon",
    "Comic Book (คอมมิค)": "Comic Book",
    "Sketch (สเกตช์)": "Sketch",
    "Vintage Film (ฟิล์มย้อนยุค)": "Vintage Film",
    "Cyberpunk (ไซเบอร์พังค์)": "Cyberpunk",
    "Steampunk (สตีมพังค์)": "Steampunk",
    "Fantasy (แฟนตาซี)": "Fantasy",
    "Fashion (แฟชั่น)": "Fashion",
    "Portrait (พอร์เทรต)": "Portrait",
    "Product (สินค้า)": "Product",
    "Food (อาหาร)": "Food",
    "Nature (ธรรมชาติ)": "Nature",
    "Street (สตรีท)": "Street",
    "Abstract (แอ็บสแตรกต์)": "Abstract",
    "Surreal (เซอร์เรียล)": "Surreal",
    "Noir (ฟิล์มนัวร์)": "Noir",
    "Pop Art (ป๊อปอาร์ต)": "Pop Art",
    
    # More UI elements that were missed
    "📊 สถิติ": "📊 Statistics",
    "🎨 สไตล์": "🎨 Styles",
    "🏷️ Tags": "🏷️ Tags",
    "🔧 ตั้งค่า": "🔧 Settings",
    "💾 บันทึก": "💾 Save",
    "🗑️ ลบ": "🗑️ Delete",
    "📤 Export": "📤 Export",
    "📥 Import": "📥 Import",
    "🔄 รีเฟรช": "🔄 Refresh",
    "✏️ แก้ไข": "✏️ Edit",
    "👁️ ดู": "👁️ View",
    "📋 คัดลอก": "📋 Copy",
    "🎬 สร้าง": "🎬 Generate",
    "⚙️ ตั้งค่าขั้นสูง": "⚙️ Advanced Settings",
}

def convert_file(input_path, output_path=None):
    """Convert Thai strings to English in a file"""
    if output_path is None:
        output_path = input_path
    
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Apply all translations
    for thai, english in UI_TRANSLATIONS.items():
        content = content.replace(thai, english)
    
    # Count changes
    changes = sum(1 for t, e in UI_TRANSLATIONS.items() if t in original_content)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Converted {changes} strings out of {len(UI_TRANSLATIONS)} total mappings")
    print(f"📝 Saved to: {output_path}")
    return changes

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        changed = convert_file(sys.argv[1])
        print(f"\n{'='*50}")
        print(f"Conversion complete: {changed} changes applied")
    else:
        print("Usage: python3 convert_ui_v2.py <file_path>")
