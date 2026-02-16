"""
Clipboard Utilities
Cross-platform clipboard functionality for Streamlit
"""
import streamlit.components.v1 as components
import json


def copy_to_clipboard(text: str, key: str) -> bool:
    """
    Copy text to clipboard using JavaScript
    Works on both HTTP and HTTPS (with fallback)
    
    Args:
        text: Text to copy
        key: Unique key for the component
        
    Returns:
        True if component was rendered
    """
    # Escape text properly for JavaScript string
    json_escaped = json.dumps(text)
    
    # JavaScript to copy to clipboard with robust fallback
    js_code = f"""
        <script>
        (function() {{
            const textToCopy = {json_escaped};
            
            function fallbackCopy(text) {{
                // Create a hidden textarea
                const ta = document.createElement('textarea');
                ta.value = text;
                ta.style.position = 'fixed';
                ta.style.left = '-9999px';
                ta.style.top = '0';
                ta.style.opacity = '0';
                ta.style.zIndex = '9999';
                document.body.appendChild(ta);
                ta.focus();
                ta.select();
                
                try {{
                    const successful = document.execCommand('copy');
                    if (successful) {{
                        showSuccess();
                    }} else {{
                        showError();
                    }}
                }} catch (err) {{
                    showError();
                }}
                
                document.body.removeChild(ta);
            }}
            
            function showSuccess() {{
                const msg = document.getElementById('copy-msg-{key}');
                if (msg) {{
                    msg.innerHTML = '✅ คัดลอกแล้ว!';
                    msg.style.color = '#00c853';
                    msg.style.fontWeight = 'bold';
                }}
            }}
            
            function showError() {{
                const msg = document.getElementById('copy-msg-{key}');
                if (msg) {{
                    msg.innerHTML = '⚠️ กรุณาเลือกข้อความและกด Ctrl+C';
                    msg.style.color = '#ff9800';
                }}
            }}
            
            // Try modern clipboard API first (requires HTTPS or localhost)
            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(textToCopy)
                    .then(showSuccess)
                    .catch(() => fallbackCopy(textToCopy));
            }} else {{
                // Use fallback for non-secure contexts (HTTP)
                fallbackCopy(textToCopy);
            }}
        }})();
        </script>
        <div id="copy-msg-{key}" style="color: #888; font-size: 14px; margin-top: 5px; padding: 5px; border-radius: 4px; background: #f0f0f0;">⏳ กำลังคัดลอก...</div>
    """
    
    # Increase height to 60px for better visibility
    components.html(js_code, height=60)
    return True
