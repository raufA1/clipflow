#!/usr/bin/env python3
"""
Basic tests for ClipFlow main components
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path

# Import ClipFlow components
from clipflow_main import ClipFlowConfig, ClipFlowOrchestrator, ConfigManager


class TestClipFlowConfig:
    """Test ClipFlow configuration"""
    
    def test_default_config(self):
        """Test default configuration creation"""
        config = ClipFlowConfig()
        
        assert config.data_dir == "data"
        assert config.temp_dir == "temp"
        assert config.timezone == "Asia/Baku"
        assert isinstance(config.platform_credentials, dict)
        assert isinstance(config.default_brand_config, dict)
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = ClipFlowConfig(
            data_dir="custom_data",
            telegram_bot_token="test_token",
            timezone="UTC"
        )
        
        assert config.data_dir == "custom_data"
        assert config.telegram_bot_token == "test_token"
        assert config.timezone == "UTC"


class TestConfigManager:
    """Test configuration manager"""
    
    def test_load_from_env_defaults(self):
        """Test loading from environment with defaults"""
        # Clear relevant env vars
        env_vars = [
            'TELEGRAM_BOT_TOKEN', 'YOUTUBE_CLIENT_ID', 
            'INSTAGRAM_ACCESS_TOKEN', 'TIKTOK_CLIENT_KEY'
        ]
        
        old_values = {}
        for var in env_vars:
            old_values[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]
        
        try:
            config = ConfigManager.load_from_env()
            assert config.telegram_bot_token == ""
            assert config.timezone == "Asia/Baku"
            assert len(config.platform_credentials) == 0
        finally:
            # Restore env vars
            for var, value in old_values.items():
                if value is not None:
                    os.environ[var] = value
    
    def test_load_from_env_with_values(self):
        """Test loading from environment with values"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        os.environ['CLIPFLOW_TIMEZONE'] = 'UTC'
        
        try:
            config = ConfigManager.load_from_env()
            assert config.telegram_bot_token == 'test_token'
            assert config.timezone == 'UTC'
        finally:
            # Clean up
            del os.environ['TELEGRAM_BOT_TOKEN']
            del os.environ['CLIPFLOW_TIMEZONE']
    
    def test_save_and_load_from_file(self):
        """Test saving and loading configuration from file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        
        try:
            # Create and save config
            original_config = ClipFlowConfig(
                telegram_bot_token="test_token",
                timezone="UTC"
            )
            
            ConfigManager.save_to_file(original_config, config_path)
            
            # Load config
            loaded_config = ConfigManager.load_from_file(config_path)
            
            assert loaded_config.telegram_bot_token == "test_token"
            assert loaded_config.timezone == "UTC"
            
        finally:
            # Clean up
            if os.path.exists(config_path):
                os.unlink(config_path)


@pytest.mark.asyncio
class TestClipFlowOrchestrator:
    """Test main orchestrator"""
    
    async def test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ClipFlowConfig(
                data_dir=temp_dir,
                temp_dir=temp_dir
            )
            
            orchestrator = ClipFlowOrchestrator(config)
            
            # Check components are initialized
            assert orchestrator.content_manager is not None
            assert orchestrator.video_processor is not None
            assert orchestrator.image_processor is not None
            assert orchestrator.text_generator is not None
            assert orchestrator.audio_processor is not None
            assert orchestrator.publish_manager is not None
            assert orchestrator.scheduler is not None
            assert orchestrator.metrics_collector is not None
    
    async def test_health_check(self):
        """Test system health check"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ClipFlowConfig(
                data_dir=temp_dir,
                temp_dir=temp_dir
            )
            
            orchestrator = ClipFlowOrchestrator(config)
            health = await orchestrator.health_check()
            
            assert isinstance(health, dict)
            assert 'timestamp' in health
            assert 'overall_status' in health
            assert 'components' in health
            
            # Check component health
            components = health['components']
            assert 'content_processing' in components
            assert 'scheduler' in components
            assert 'analytics' in components
    
    async def test_process_content_from_telegram(self):
        """Test content processing from Telegram"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ClipFlowConfig(
                data_dir=temp_dir,
                temp_dir=temp_dir
            )
            
            orchestrator = ClipFlowOrchestrator(config)
            
            # Test text content processing
            result = await orchestrator.process_content_from_telegram(
                user_id=12345,
                content_type="text",
                text_content="Test content for processing",
                caption="Test caption",
                platforms=["youtube", "instagram"]
            )
            
            assert isinstance(result, dict)
            assert 'content_id' in result
            
            # Should have content_id even if processing fails
            if result.get('content_id'):
                assert result['content_id'].startswith('12345_')


class TestUtilities:
    """Test utility functions"""
    
    def test_environment_variable_parsing(self):
        """Test environment variable parsing"""
        # Test with missing env vars
        config = ConfigManager.load_from_env()
        assert isinstance(config, ClipFlowConfig)
        
        # Test with some env vars set
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        os.environ['YOUTUBE_CLIENT_ID'] = 'test_youtube_id'
        
        try:
            config = ConfigManager.load_from_env()
            assert config.telegram_bot_token == 'test_token'
            assert 'youtube' in config.platform_credentials
            assert config.platform_credentials['youtube']['client_id'] == 'test_youtube_id'
        finally:
            # Clean up
            del os.environ['TELEGRAM_BOT_TOKEN']
            del os.environ['YOUTUBE_CLIENT_ID']


# Test data fixtures
@pytest.fixture
def sample_config():
    """Sample configuration for tests"""
    return ClipFlowConfig(
        telegram_bot_token="test_token",
        platform_credentials={
            "youtube": {
                "client_id": "test_id",
                "client_secret": "test_secret",
                "access_token": "test_token"
            }
        }
    )


@pytest.fixture
def temp_orchestrator():
    """Temporary orchestrator for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = ClipFlowConfig(
            data_dir=temp_dir,
            temp_dir=temp_dir,
            telegram_bot_token="test_token"
        )
        yield ClipFlowOrchestrator(config)


# Integration tests
@pytest.mark.asyncio
async def test_full_workflow_simulation(temp_orchestrator):
    """Test a complete workflow simulation"""
    orchestrator = temp_orchestrator
    
    # Simulate processing text content
    result = await orchestrator.process_content_from_telegram(
        user_id=12345,
        content_type="text",
        text_content="Amazing content! 🚀",
        platforms=["instagram"]
    )
    
    # Should return a valid result structure
    assert isinstance(result, dict)
    
    # Should have some form of content_id
    assert 'content_id' in result or 'error' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])