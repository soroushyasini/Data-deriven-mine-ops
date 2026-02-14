# Contributing to Gold Mining Operations Data Platform

Thank you for your interest in contributing to this project! This guide will help you get started.

## 🚀 Quick Start for Developers

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Data-deriven-mine-ops.git
   cd Data-deriven-mine-ops
   ```

2. **Set up development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install pytest pytest-cov
   ```

3. **Run tests**:
   ```bash
   pytest tests/ -v
   ```

## 📝 Development Guidelines

### Code Style

- Follow PEP 8 style guide
- Use type hints for function parameters and returns
- Write docstrings for all public functions and classes
- Keep functions focused and modular

### Testing

- Write tests for all new features
- Maintain >80% code coverage
- Test with sample data that includes edge cases
- Include Persian/Farsi text in test data

### Commit Messages

Use clear, descriptive commit messages:
- `feat: Add finance summary report`
- `fix: Correct cost calculation for kg-based tonnage`
- `docs: Update README with new alert rules`
- `test: Add tests for sample code parsing`

## 🔧 Adding New Features

### Adding a New Data Source

1. Create converter in `src/converters/`:
   ```python
   from src.core.base_converter import BaseConverter
   
   class MyNewConverter(BaseConverter):
       def convert(self, input_data):
           # Your conversion logic
           pass
   ```

2. Add database model in `src/database/models.py`:
   ```python
   class MyNewData(Base):
       __tablename__ = 'my_new_data'
       # Define columns
   ```

3. Update ingestion in `src/database/ingestion.py`:
   ```python
   def ingest_my_new_data(self, data_list):
       # Ingestion logic
   ```

4. Update `scripts/ingest.py` to include your new data source

### Adding a New Report

1. Create report class in `src/reports/`:
   ```python
   from src.reports.base_report import BaseReport
   
   class MyNewReport(BaseReport):
       def generate_data(self, **kwargs):
           # Generate report data
           pass
       
       def format_markdown(self, data):
           # Format as Markdown
           pass
   ```

2. Add to `scripts/generate_report.py`

### Adding a New Alert Rule

1. Update `config/validation_rules.json`:
   ```json
   {
     "my_new_check": {
       "threshold": 10.0,
       "description": "Check description"
     }
   }
   ```

2. Add validation logic in `src/core/validator.py`:
   ```python
   def validate_my_new_check(self, data):
       # Validation logic
       pass
   ```

## 🧪 Testing Your Changes

### Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_converters.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Integration Testing

1. Generate sample data:
   ```bash
   python scripts/create_sample_data.py
   ```

2. Test full pipeline:
   ```bash
   # Copy sample data to incoming
   cp data/samples/*.json data/incoming/
   
   # Run ingestion
   python scripts/ingest.py
   
   # Generate reports
   python scripts/generate_report.py all
   ```

### Docker Testing

```bash
# Build and test
docker-compose up --build

# Run tests in container
docker-compose exec pipeline pytest tests/ -v
```

## 📚 Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions and classes
- Update configuration documentation when adding new settings
- Include examples for new features

## 🐛 Bug Reports

When reporting bugs, please include:

1. Description of the issue
2. Steps to reproduce
3. Expected vs actual behavior
4. Sample data (if applicable)
5. System information (OS, Python version, etc.)

## 💡 Feature Requests

Feature requests are welcome! Please:

1. Check if the feature already exists
2. Describe the use case
3. Explain how it fits into the mining operations workflow
4. Consider if it can be implemented as a plugin/extension

## 🌍 Internationalization

This project supports Persian/Farsi text:

- Always use UTF-8 encoding
- Test with Persian sample data
- Support Jalali calendar dates
- Handle bidirectional text properly

## 🔒 Security

- Don't commit credentials or secrets
- Use environment variables for sensitive data
- Follow secure coding practices
- Report security issues privately

## 📋 Pull Request Process

1. Create a feature branch:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "feat: Add my new feature"
   ```

3. Push to your fork:
   ```bash
   git push origin feature/my-new-feature
   ```

4. Create a Pull Request with:
   - Clear description of changes
   - Reference to any related issues
   - Test results
   - Screenshots (if UI changes)

5. Wait for review and address feedback

## 📞 Getting Help

- Open an issue for questions
- Check existing documentation
- Review sample code in `tests/` directory
- Look at existing converters/reports for examples

## 🙏 Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Provide constructive feedback
- Focus on the mining operations use case

Thank you for contributing! 🎉
