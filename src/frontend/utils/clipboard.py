"""
Clipboard Utilities
Cross-platform clipboard functionality for Streamlit

Problem: navigator.clipboard API requires HTTPS + secure context.
         Streamlit components.html() runs inside sandboxed iframes
         that block clipboard access in most browsers.

Solution: Use Streamlit's native st.code() which has a built-in copy
           button that works reliably, plus st.download_button() as
           a universal fallback that always works.
"""
import streamlit as st


def copy_to_clipboard(text: str, key: str) -> bool:
    """
    Display text with copy functionality using multiple reliable methods.
    
    Strategy:
    1. st.code() — has a built-in copy button (works on HTTPS)
    2. Download button — always works as a fallback
    
    Args:
        text: Text to copy
        key: Unique key for the component
        
    Returns:
        True if component was rendered
    """
    if not text:
        st.warning("ไม่มีข้อความให้คัดลอก")
        return False
    
    # Method 1: st.code() has a built-in copy icon button (top-right corner)
    # This uses Streamlit's native clipboard integration which works on HTTPS
    st.code(text, language=None)
    
    # Method 2: Download as .txt fallback — always works regardless of browser/HTTPS
    st.download_button(
        "💾 ดาวน์โหลดเป็นไฟล์ .txt",
        data=text,
        file_name=f"{key}.txt",
        mime="text/plain",
        key=f"dl_{key}",
        use_container_width=True,
    )
    
    return True


def copy_code_block(text: str, label: str = "") -> None:
    """
    Show text in a code block with built-in copy button.
    Simpler version — just st.code() with optional label.
    
    Args:
        text: Text to display
        label: Optional label above the code block
    """
    if label:
        st.caption(label)
    st.code(text or "(ว่าง)", language=None)
