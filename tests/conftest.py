"""
Pytest configuration and shared fixtures for the Telegram Moderation Bot tests.
"""

import pytest
import tempfile
import shutil
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to Python path for all tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Register custom markers
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests") 
    config.addinivalue_line("markers", "gui: GUI tests (may need display)")
    config.addinivalue_line("markers", "slow: Slow tests (> 5 seconds)")
    config.addinivalue_line("markers", "network: Tests requiring network")
    config.addinivalue_line("markers", "ai_models: Tests requiring AI models")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add automatic markers."""
    for item in items:
        # Auto-mark GUI tests
        if "gui" in item.nodeid.lower():
            item.add_marker(pytest.mark.gui)
        
        # Auto-mark model tests
        if "model" in item.nodeid.lower():
            item.add_marker(pytest.mark.ai_models)
        
        # Auto-mark integration tests
        if "integration" in item.name.lower():
            item.add_marker(pytest.mark.integration)
        elif "test_telegram_bot" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        else:
            # Default to unit tests
            item.add_marker(pytest.mark.unit)


# Shared fixtures
@pytest.fixture(scope="session")
def temp_directory():
    """Create a temporary directory for the test session."""
    temp_dir = tempfile.mkdtemp(prefix="telegram_bot_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_config_dir(temp_directory):
    """Create a temporary config directory."""
    config_dir = Path(temp_directory) / "config"
    config_dir.mkdir(exist_ok=True)
    return config_dir


@pytest.fixture
def temp_models_dir(temp_directory):
    """Create a temporary models directory."""
    models_dir = Path(temp_directory) / "models"
    models_dir.mkdir(exist_ok=True)
    return models_dir


@pytest.fixture
def sample_config():
    """Provide sample configuration for testing."""
    return {
        'telegram': {
            'token': 'test_token_123456',
            'allowed_chats': [12345, 67890]
        },
        'moderation': {
            'text_model': {
                'type': 'transformers',
                'path': 'test/text_model'
            },
            'vision_model': {
                'type': 'transformers', 
                'path': 'test/vision_model'
            }
        },
        'policies': [
            {
                'name': 'spam',
                'description': 'Spam detection',
                'threshold': 0.7,
                'action': 'delete'
            },
            {
                'name': 'harassment',
                'description': 'Harassment detection',
                'threshold': 0.8,
                'action': 'warn'
            }
        ],
        'performance': {
            'max_concurrent_requests': 5,
            'request_timeout': 30
        }
    }


@pytest.fixture
def mock_telegram_message():
    """Create a mock Telegram message for testing."""
    message = Mock()
    message.message_id = 12345
    message.text = "Test message content"
    message.chat_id = 67890
    message.chat.title = "Test Chat"
    message.from_user.id = 11111
    message.from_user.username = "testuser"
    message.from_user.first_name = "Test"
    message.from_user.last_name = "User"
    message.date = 1234567890
    
    # Mock async methods
    message.delete = Mock()
    message.reply_text = Mock()
    
    return message


@pytest.fixture
def mock_telegram_update(mock_telegram_message):
    """Create a mock Telegram update for testing."""
    update = Mock()
    update.update_id = 123456
    update.message = mock_telegram_message
    return update


@pytest.fixture
def sample_violation_data():
    """Provide sample violation data for testing."""
    return {
        'timestamp': '2024-01-01T12:00:00',
        'chat_id': 12345,
        'chat_title': 'Test Group',
        'user_id': 67890,
        'username': 'testuser',
        'content_type': 'text',
        'violation_type': 'spam',
        'confidence': 0.85,
        'reason': 'Detected promotional content',
        'action_taken': 'deleted'
    }


@pytest.fixture
def sample_custom_rules():
    """Provide sample custom rules for testing."""
    return [
        {
            'type': 'keyword',
            'keywords': ['spam', 'scam', 'phishing'],
            'action': 'delete',
            'reason': 'Blocked keyword detected',
            'confidence': 0.9,
            'category': 'security'
        },
        {
            'type': 'url',
            'pattern': r'.*suspicious-site\.com.*',
            'action': 'warn',
            'reason': 'Suspicious domain detected',
            'confidence': 0.8,
            'category': 'security'
        },
        {
            'type': 'length',
            'max_length': 500,
            'action': 'warn',
            'reason': 'Message too long',
            'confidence': 0.6,
            'category': 'policy'
        }
    ]


# Mock AI models to avoid downloading during tests
@pytest.fixture(autouse=True)
def mock_ai_models():
    """Automatically mock AI model loading for all tests."""
    with patch('src.moderation.HAS_TRANSFORMERS', True), \
         patch('src.model_manager.HAS_TRANSFORMERS', True), \
         patch('src.model_manager.snapshot_download') as mock_download, \
         patch('src.model_manager.pipeline') as mock_pipeline:
        
        # Mock successful download
        mock_download.return_value = None
        
        # Mock pipeline creation
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.return_value = [{'label': 'SAFE', 'score': 0.9}]
        mock_pipeline.return_value = mock_pipeline_instance
        
        yield {
            'download': mock_download,
            'pipeline': mock_pipeline,
            'pipeline_instance': mock_pipeline_instance
        }


# Performance testing helpers
@pytest.fixture
def performance_timer():
    """Fixture for measuring test performance."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0
    
    return Timer()


# Database/Storage mocking
@pytest.fixture
def mock_file_operations():
    """Mock file operations to avoid actual file I/O during tests."""
    with patch('builtins.open') as mock_open, \
         patch('json.dump') as mock_json_dump, \
         patch('json.load') as mock_json_load, \
         patch('pathlib.Path.exists') as mock_exists, \
         patch('pathlib.Path.mkdir') as mock_mkdir:
        
        # Configure mocks
        mock_exists.return_value = True
        mock_json_load.return_value = {}
        
        yield {
            'open': mock_open,
            'json_dump': mock_json_dump,
            'json_load': mock_json_load,
            'exists': mock_exists,
            'mkdir': mock_mkdir
        }


# Network mocking
@pytest.fixture
def mock_network():
    """Mock network operations."""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post:
        
        # Configure successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success'}
        mock_response.content = b'fake_content'
        
        mock_get.return_value = mock_response
        mock_post.return_value = mock_response
        
        yield {
            'get': mock_get,
            'post': mock_post,
            'response': mock_response
        }


# GUI testing helpers
@pytest.fixture
def mock_tkinter():
    """Mock tkinter for GUI testing without creating windows."""
    with patch('tkinter.Tk') as mock_tk, \
         patch('tkinter.ttk.Notebook') as mock_notebook, \
         patch('tkinter.ttk.Frame') as mock_frame, \
         patch('tkinter.ttk.Label') as mock_label, \
         patch('tkinter.ttk.Button') as mock_button, \
         patch('tkinter.scrolledtext.ScrolledText') as mock_text:
        
        # Configure mocks
        mock_root = Mock()
        mock_tk.return_value = mock_root
        
        yield {
            'root': mock_root,
            'notebook': mock_notebook,
            'frame': mock_frame,
            'label': mock_label,
            'button': mock_button,
            'text': mock_text
        }


# Error simulation helpers
@pytest.fixture
def error_simulator():
    """Helper for simulating various error conditions."""
    class ErrorSimulator:
        @staticmethod
        def network_error():
            return ConnectionError("Network unreachable")
        
        @staticmethod
        def file_not_found():
            return FileNotFoundError("File not found")
        
        @staticmethod
        def permission_error():
            return PermissionError("Permission denied")
        
        @staticmethod
        def ai_model_error():
            return RuntimeError("Model loading failed")
        
        @staticmethod
        def telegram_api_error():
            return Exception("Telegram API error")
    
    return ErrorSimulator()


# Test data generators
@pytest.fixture
def test_data_generator():
    """Generate test data for various scenarios."""
    class TestDataGenerator:
        @staticmethod
        def spam_messages(count=10):
            templates = [
                "Buy {} now for limited time!",
                "Get rich quick with {}!",
                "Free {} - click here!",
                "Make money fast with {}!",
                "Guaranteed {} profits!"
            ]
            products = ["crypto", "stocks", "courses", "software", "pills"]
            
            messages = []
            for i in range(count):
                template = templates[i % len(templates)]
                product = products[i % len(products)]
                messages.append(template.format(product))
            
            return messages
        
        @staticmethod
        def clean_messages(count=10):
            messages = [
                "Hello everyone, how are you today?",
                "Thanks for sharing that article!",
                "Looking forward to our meeting tomorrow.",
                "Great work on the project!",
                "Happy birthday! Hope you have a wonderful day.",
                "Did anyone see the game last night?",
                "The weather is beautiful today.",
                "I really enjoyed that movie.",
                "Can you help me with this question?",
                "Have a great weekend everyone!"
            ]
            return messages[:count] * ((count // 10) + 1)
        
        @staticmethod
        def harassment_messages(count=5):
            # Mild examples suitable for testing
            return [
                "You're so annoying, just shut up",
                "Nobody likes you here, go away",
                "You're completely worthless at this",
                "Stop being such an idiot all the time",
                "You should just give up already"
            ][:count]
    
    return TestDataGenerator()


# Cleanup helpers
@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Automatically cleanup test files after each test."""
    yield  # Run the test
    
    # Cleanup after test
    test_files = [
        "test_config.json",
        "test_rules.json", 
        "test_log.txt",
        "gui_settings.json"
    ]
    
    for filename in test_files:
        try:
            Path(filename).unlink()
        except FileNotFoundError:
            pass


# Environment setup
@pytest.fixture(autouse=True)
def test_environment():
    """Set up test environment variables."""
    import os
    
    original_env = os.environ.copy()
    
    # Set test environment variables
    os.environ['TESTING'] = 'true'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)