"""
Frontend Pages
VDO Content V3 - 5-Step Workflow Pages
"""

# 5-Step Workflow Pages
from . import step1_project
from . import step2_content
from . import step3_script
from . import step4_video_prompt
from . import step5_upload

# Management Pages
from . import database_tags
from . import settings

__all__ = [
    # 5-step workflow
    "step1_project",
    "step2_content", 
    "step3_script",
    "step4_video_prompt",
    "step5_upload",
    # Management
    "database_tags",
    "settings",
]
