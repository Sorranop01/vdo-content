"""
Unit Tests for ProjectExporter
"""

import pytest
import zipfile
import io
import json
from core.exporter import ProjectExporter
from core.models import Project, Scene


class TestProjectExporter:
    """Test suite for ProjectExporter class"""
    
    def test_export_full_package_returns_bytes(self, sample_project, exporter):
        """Test that export_full_package returns bytes"""
        result = exporter.export_full_package(sample_project)
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_export_full_package_is_valid_zip(self, sample_project, exporter):
        """Test that the returned bytes are a valid ZIP file"""
        zip_bytes = exporter.export_full_package(sample_project)
        
        # Should be valid ZIP
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
            # Check required files exist
            file_names = zf.namelist()
            assert 'prompts.txt' in file_names
            assert 'scenes.json' in file_names
            assert 'metadata.json' in file_names
            assert 'README.md' in file_names
    
    def test_export_full_package_prompts_content(self, sample_project, exporter):
        """Test that prompts.txt contains correct content"""
        zip_bytes = exporter.export_full_package(sample_project)
        
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
            prompts_content = zf.read('prompts.txt').decode('utf-8')
            
            # Should contain project title
            assert sample_project.title in prompts_content
            
            # Should contain all prompts
            for scene in sample_project.scenes:
                if scene.veo_prompt:
                    assert scene.veo_prompt in prompts_content
    
    def test_export_full_package_scenes_json_valid(self, sample_project, exporter):
        """Test that scenes.json is valid JSON with correct structure"""
        zip_bytes = exporter.export_full_package(sample_project)
        
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
            scenes_content = zf.read('scenes.json').decode('utf-8')
            scenes_data = json.loads(scenes_content)
            
            assert isinstance(scenes_data, list)
            assert len(scenes_data) == len(sample_project.scenes)
            
            # Check scene structure
            for scene_dict in scenes_data:
                assert 'order' in scene_dict
                assert 'narration_text' in scene_dict
                assert 'veo_prompt' in scene_dict
    
    def test_export_full_package_metadata_json_valid(self, sample_project, exporter):
        """Test that metadata.json is valid JSON with project info"""
        zip_bytes = exporter.export_full_package(sample_project)
        
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
            metadata_content = zf.read('metadata.json').decode('utf-8')
            metadata = json.loads(metadata_content)
            
            assert metadata['project_id'] == sample_project.project_id
            assert metadata['title'] == sample_project.title
            assert metadata['topic'] == sample_project.topic
            assert metadata['scene_count'] == len(sample_project.scenes)
    
    def test_export_full_package_empty_project(self, sample_project_no_scenes, exporter):
        """Test exporting a project with no scenes"""
        zip_bytes = exporter.export_full_package(sample_project_no_scenes)
        
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
            scenes_content = zf.read('scenes.json').decode('utf-8')
            scenes_data = json.loads(scenes_content)
            assert scenes_data == []
    
    def test_export_all_prompts_text_returns_string(self, sample_project, exporter):
        """Test that export_all_prompts_text returns a string"""
        result = exporter.export_all_prompts_text(sample_project)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_export_all_prompts_text_contains_prompts(self, sample_project, exporter):
        """Test that the prompts text contains all scene prompts"""
        result = exporter.export_all_prompts_text(sample_project)
        
        for scene in sample_project.scenes:
            if scene.veo_prompt:
                assert scene.veo_prompt in result
    
    def test_export_all_prompts_text_has_scene_markers(self, sample_project, exporter):
        """Test that the prompts text has scene markers"""
        result = exporter.export_all_prompts_text(sample_project)
        
        for i, scene in enumerate(sample_project.scenes):
            assert f"SCENE {scene.order}" in result
    
    def test_export_all_prompts_text_empty_project(self, sample_project_no_scenes, exporter):
        """Test exporting prompts for a project with no scenes"""
        result = exporter.export_all_prompts_text(sample_project_no_scenes)
        assert isinstance(result, str)
        # Empty project should return message about no scenes
        assert "No scenes found" in result


class TestProjectExporterEdgeCases:
    """Edge case tests for ProjectExporter"""
    
    def test_unicode_in_project_title(self, exporter):
        """Test handling of Unicode characters in project title"""
        project = Project(
            title="โปรเจคทดสอบ ภาษาไทย 🎬",
            topic="ทดสอบ Unicode",
            scenes=[
                Scene(order=1, narration_text="ทดสอบ", veo_prompt="Test", start_time=0, end_time=5)
            ]
        )
        
        zip_bytes = exporter.export_full_package(project)
        assert len(zip_bytes) > 0
        
        # Should be valid ZIP
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
            readme_content = zf.read('README.md').decode('utf-8')
            assert 'โปรเจคทดสอบ' in readme_content
    
    def test_special_characters_in_prompts(self, exporter):
        """Test handling of special characters in prompts"""
        project = Project(
            title="Special Chars Test",
            topic="Testing special characters",
            scenes=[
                Scene(
                    order=1,
                    narration_text="Test with \"quotes\" and 'apostrophes'",
                    veo_prompt="Scene with <brackets> & ampersands",
                    start_time=0,
                    end_time=5
                )
            ]
        )
        
        prompts_text = exporter.export_all_prompts_text(project)
        assert "<brackets>" in prompts_text
        assert "& ampersands" in prompts_text
