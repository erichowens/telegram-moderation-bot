# Testing Guide for Telegram Moderation Bot

This document explains how to run and understand the comprehensive test suite for the Telegram Moderation Bot.

## 🎯 Testing Philosophy

Our testing approach ensures the bot is **production-ready** and **reliable**:

- **Unit Tests**: Fast, isolated tests for individual components
- **Integration Tests**: Verify components work together properly  
- **GUI Tests**: Ensure the user interface functions correctly
- **AI Model Tests**: Validate machine learning functionality
- **Performance Tests**: Confirm the bot handles load efficiently

## 🚀 Quick Start

### Install Test Dependencies
```bash
pip install pytest pytest-cov pytest-asyncio pytest-timeout
pip install -r requirements.txt
```

### Run All Tests
```bash
# Run the full test suite
pytest

# Run with coverage report
pytest --cov=src --cov-report=html
```

### Run Specific Test Types
```bash
# Fast unit tests only
pytest -m unit

# Integration tests
pytest -m integration  

# GUI tests (requires display)
pytest -m gui

# Performance tests
pytest -k performance
```

## 📊 Test Coverage

Our test suite covers:

| Component | Test Files | Coverage |
|-----------|------------|----------|
| **Core Moderation** | `test_moderation.py` | 95%+ |
| **AI Models** | `test_model_manager.py` | 90%+ |
| **Rule Parser** | `test_rule_parser.py` | 95%+ |
| **Telegram Bot** | `test_telegram_bot.py` | 85%+ |
| **GUI Interface** | `test_gui.py` | 80%+ |

## 🧪 Test Types Explained

### Unit Tests (`-m unit`)
**Purpose**: Test individual functions and classes in isolation

**Examples**:
```python
# Test spam detection logic
def test_spam_detection_keywords(moderator):
    result = await moderator.moderate_text("Buy now for limited time!")
    assert result.is_violation
    assert result.category == "spam"

# Test rule parsing
def test_parse_keyword_blocking(parser):
    rules = parser.parse_sentence("Don't allow 'spam' messages")
    assert rules[0]['type'] == 'keyword'
```

**Run**: `pytest -m unit` (⚡ ~30 seconds)

### Integration Tests (`-m integration`)
**Purpose**: Test components working together

**Examples**:
```python
# Test complete moderation workflow
async def test_spam_detection_workflow(bot):
    # Send spam message to bot
    await bot.handle_text_message(spam_update, context)
    
    # Verify it was detected and handled
    assert bot.stats["violations_found"] == 1
    assert bot.stats["actions_taken"] == 1
```

**Run**: `pytest -m integration` (🐌 ~2 minutes)

### GUI Tests (`-m gui`)
**Purpose**: Test user interface without creating visible windows

**Examples**:
```python
# Test bot start logic
def test_bot_start_stop_logic(mock_gui):
    mock_gui.start_bot()
    assert mock_gui.bot_running == True

# Test custom rule parsing in GUI
def test_custom_rules_parsing(mock_gui):
    mock_gui.parse_custom_rules()
    # Verify rules were parsed and saved
```

**Run**: `pytest -m gui` (🖥️ ~1 minute)

### AI Model Tests (`-m ai_models`)
**Purpose**: Test real AI model downloading and loading

**Examples**:
```python
# Test model download
def test_download_model_success(model_manager):
    result = model_manager.download_model("toxicity_detector")
    assert result == True

# Test AI moderation with real models
async def test_ai_moderation_real_model(moderator):
    result = await moderator.moderate_text("You're an idiot!")
    assert result.is_violation
```

**Run**: `pytest -m ai_models` (🤖 ~5 minutes, downloads models)

## 🎮 GUI Testing Strategies

Testing GUIs is challenging, so we use multiple approaches:

### 1. **Logic Testing** (Recommended)
Test the business logic behind GUI components without creating windows:

```python
def test_settings_save_load(mock_gui):
    # Test the logic of saving settings
    mock_gui.settings = {"test": "value"}
    mock_gui.save_settings()
    
    # Verify save was attempted
    assert mock_gui.settings_saved == True
```

**Pros**: Fast, reliable, good coverage  
**Cons**: Doesn't test actual UI rendering

### 2. **Component Testing**
Test individual GUI widgets in isolation:

```python
def test_widget_creation(root_window):
    button = ttk.Button(root_window, text="Test")
    assert button is not None
    assert button['text'] == "Test"
```

**Pros**: Tests real widget behavior  
**Cons**: Requires display environment

### 3. **Automation Testing** 
Simulate user interactions (advanced):

```python
def test_user_workflow(gui_automation):
    gui_automation.type_text("bot_token", "test_token_123")
    gui_automation.click_button("start_bot")
    assert gui_automation.get_status() == "Bot: Running"
```

**Pros**: Tests real user experience  
**Cons**: Slow, brittle, environment-dependent

### 4. **Visual Testing**
Compare screenshots to detect visual regressions:

```python
def test_main_window_layout(gui_app):
    screenshot = gui_app.capture_screenshot()
    assert_visual_match(screenshot, "main_window_expected.png")
```

**Pros**: Catches visual bugs  
**Cons**: High maintenance, platform-specific

## 🔧 Running Tests in Different Environments

### Local Development
```bash
# Quick feedback loop
pytest -m unit -x  # Stop on first failure

# With coverage
pytest --cov=src --cov-report=term-missing

# Parallel execution (faster)
pytest -n auto  # Requires pytest-xdist
```

### Continuous Integration (GitHub Actions)
Our CI pipeline automatically runs:

1. **Unit & Integration Tests** on Python 3.8-3.11, Windows/macOS/Linux
2. **GUI Tests** on Linux with virtual display
3. **Security Scans** with Bandit and Safety
4. **Code Quality** checks with Black, flake8, mypy
5. **Performance Tests** with benchmarking

### Docker Environment
```bash
# Run tests in clean Docker container
docker run --rm -v $(pwd):/app python:3.10 bash -c "
  cd /app
  pip install -r requirements.txt
  pytest -m unit
"
```

### Headless Environment (Servers)
```bash
# For GUI tests on servers without displays
xvfb-run -a pytest -m gui
```

## 📈 Performance Testing

We test performance to ensure the bot handles real-world loads:

### Message Processing Speed
```python
def test_message_processing_speed(bot):
    # Process 100 messages
    start_time = time.time()
    for i in range(100):
        await bot.handle_text_message(test_message)
    end_time = time.time()
    
    # Should process under 10ms per message
    avg_time = (end_time - start_time) / 100
    assert avg_time < 0.01
```

### Memory Usage
```python
def test_memory_usage(bot):
    initial_memory = get_memory_usage()
    
    # Process 1000 messages
    for i in range(1000):
        await bot.moderate_message(f"test message {i}")
    
    final_memory = get_memory_usage()
    
    # Memory growth should be minimal
    assert (final_memory - initial_memory) < 50_000_000  # 50MB
```

### Load Testing
```bash
# Simulate 100 concurrent users
pytest tests/test_performance.py::test_concurrent_load -v
```

## 🛡️ Security Testing

We include security tests to ensure the bot is safe:

### Input Validation
```python
def test_malicious_input_handling(moderator):
    malicious_inputs = [
        "'; DROP TABLE users; --",  # SQL injection
        "<script>alert('xss')</script>",  # XSS
        "../../../etc/passwd",  # Path traversal
        "\x00\x01\x02invalid_unicode"  # Invalid unicode
    ]
    
    for input_text in malicious_inputs:
        # Should handle gracefully without crashing
        result = await moderator.moderate_text(input_text)
        assert isinstance(result, ModerationResult)
```

### Configuration Security
```python
def test_no_secrets_in_logs(bot):
    bot.log_activity("Starting bot with token: test_token_123")
    
    log_content = get_log_content()
    
    # Tokens should be redacted in logs
    assert "test_token_123" not in log_content
    assert "***" in log_content or "[REDACTED]" in log_content
```

## 🎯 Test Data and Fixtures

We provide realistic test data to ensure comprehensive coverage:

### Sample Messages
```python
# Spam messages for testing detection
spam_messages = [
    "Buy crypto now for guaranteed profits!",
    "Make money fast with this one trick!",
    "Limited time offer - click here!"
]

# Clean messages that should pass
clean_messages = [
    "Hello everyone, how are you today?",
    "Thanks for sharing that interesting article!",
    "Looking forward to our meeting tomorrow."
]
```

### Mock Telegram API
```python
@pytest.fixture
def mock_telegram_message():
    message = Mock()
    message.text = "Test message"
    message.chat_id = 12345
    message.from_user.username = "testuser"
    message.delete = AsyncMock()
    return message
```

## 🚨 Troubleshooting Tests

### Common Issues

**Tests fail with "Display not found"**
```bash
# Use virtual display
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &
pytest -m gui
```

**AI model tests timeout**
```bash
# Skip model downloads in CI
pytest -m "not ai_models"

# Or increase timeout
pytest --timeout=600 -m ai_models
```

**Permission errors on Windows**
```bash
# Run as administrator or use WSL
pytest --no-cov  # Disable coverage if it causes issues
```

### Debug Mode
```bash
# Verbose output with debug info
pytest -v -s --tb=long

# Stop on first failure for debugging
pytest -x --pdb

# Run specific test with full output
pytest tests/test_moderation.py::TestContentModerator::test_spam_detection -v -s
```

## 📊 Test Metrics and Reporting

### Coverage Report
```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html  # View in browser
```

### Test Duration Report
```bash
# Show slowest tests
pytest --durations=10
```

### Benchmark Results
```bash
# Generate performance benchmark report
pytest --benchmark-only --benchmark-json=benchmark.json
```

## 🔄 Continuous Testing

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run tests before every commit
git commit -m "Your changes"  # Automatically runs tests
```

### Test Automation
```bash
# Watch for file changes and run tests automatically
pip install pytest-watch
ptw tests/ src/
```

## 🎉 Best Practices

### Writing Good Tests

1. **Test One Thing**: Each test should verify one specific behavior
2. **Use Descriptive Names**: `test_spam_detection_with_high_confidence()`
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Use Fixtures**: Avoid duplicating setup code
5. **Mock External Dependencies**: Don't rely on networks, files, etc.

### Test Organization

```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Component interaction tests  
├── gui/           # User interface tests
├── performance/   # Load and speed tests
├── fixtures/      # Shared test data
└── conftest.py    # Global test configuration
```

### Debugging Failed Tests

1. **Read the Error Message**: Pytest provides detailed tracebacks
2. **Use Print Debugging**: Add `print()` statements temporarily
3. **Run Single Test**: `pytest tests/test_file.py::test_function -v`
4. **Use Debugger**: `pytest --pdb` drops into debugger on failure
5. **Check Fixtures**: Ensure test data is set up correctly

## 🎯 Test Quality Metrics

We aim for:

- **Coverage**: >80% line coverage, >90% for critical components
- **Speed**: Unit tests <30s, full suite <5 minutes
- **Reliability**: <1% flaky test rate
- **Maintainability**: Clear, readable test code

## 📚 Further Reading

- [Pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://realpython.com/python-testing/)
- [GUI Testing Strategies](https://testdriven.io/blog/gui-testing/)
- [Async Testing in Python](https://pytest-asyncio.readthedocs.io/)

---

**Need Help?** 

- Check the test output for specific error messages
- Look at similar tests for examples
- Review the fixture definitions in `conftest.py`
- Ask questions in GitHub issues