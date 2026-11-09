# Slotcar Laptimer - Contributing

Thanks for your interest in contributing to the Slotcar Laptimer project!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/slotcar-laptimer.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Set up development environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
   On a laptop, `rpi-lgpio` is skipped automatically and the app runs without sensors. On a Raspberry Pi see the install notes in [README.md](README.md).
5. Run the app: `python SlotcarLapTimer.py` (http://localhost:5000)

## Making Changes

### Code Style

- Follow PEP 8 guidelines
- Use type hints where applicable
- Write docstrings for all functions and classes
- Keep methods focused; keep timing logic in `lap_timer/core.py` free of Flask and GPIO imports

### Testing

- Write tests for new features
- Ensure all tests pass: `python -m unittest discover -s tests -v` (`tests/test_core.py` for logic, `tests/test_app.py` for routes)
- Aim for high coverage of core logic

Example test:
```python
def test_my_new_feature(self):
    """Description of what this test verifies."""
    timer = LapTimer(num_lanes=2)
    # Arrange
    with patch('lap_timer.core.time.time', return_value=100.0):
        timer.start_timer()
    # Act
    with patch('lap_timer.core.time.time', return_value=105.0):
        result = timer.elapsed_timer()
    # Assert
    self.assertAlmostEqual(result, 5.0, places=3)
```

### Documentation

- Update relevant documentation files:
  - `README.md` for user-facing changes
  - `ARCHITECTURE.md` for design/code changes
  - `BUILDERS_GUIDE.md` for hardware/setup changes
  - Code comments for implementation details
- Use clear, concise language

## Commit Messages

- Use present tense: "Add feature" not "Added feature"
- Start with a capital letter
- Keep the first line under 50 characters
- Provide detailed description in the body if needed

Example:
```
Add lap statistics tracking

- Track average lap time
- Track min/max lap times
- Display in UI footer
```

## Pull Request Process

1. Update documentation and tests
2. Run `python -m unittest discover -s tests -v` to verify all tests pass
3. Push to your fork
4. Create a pull request with:
   - Clear description of changes
   - Reference to any related issues
   - Screenshots for UI changes (if applicable)
5. Ensure CI checks pass (GitHub Actions runs the unit tests)

## Areas for Contribution

We're especially interested in:

### Features
- [ ] Race statistics and history
- [ ] Leaderboard functionality
- [ ] Sound/audio notifications
- [ ] CSV export
- [ ] Advanced sensor calibration UI

### Improvements
- [ ] Performance optimizations
- [ ] Additional test coverage
- [ ] Better error handling
- [ ] Security enhancements
- [ ] Mobile app support

### Documentation
- [ ] More detailed API docs
- [ ] Video tutorials
- [ ] Troubleshooting guides
- [ ] Example builds

## Report Issues

Found a bug? Please open an issue with:

1. **Description**: What's the problem?
2. **Steps to reproduce**: How can we recreate it?
3. **Expected behavior**: What should happen?
4. **Actual behavior**: What actually happens?
5. **Environment**: 
   - Raspberry Pi model
   - Python version
   - Flask version
   - Operating system
6. **Logs**: Include any error messages

## Questions?

- Check [README.md](README.md) for quick start
- See [BUILDERS_GUIDE.md](BUILDERS_GUIDE.md) for hardware help
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for code organization
- Look at existing tests for usage examples

## Code of Conduct

- Be respectful and inclusive
- Welcome new contributors
- Provide constructive feedback
- Report inappropriate behavior

## License

By contributing, you agree that your contributions will be licensed under the same terms as the project.

---

Thank you for contributing! Happy coding! 🚀
