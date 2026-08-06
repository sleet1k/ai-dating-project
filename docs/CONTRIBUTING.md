# CONTRIBUTING

We welcome contributions! Follow these steps to get started:

1. **Fork the repository** and clone it locally.
2. **Create a virtual environment** and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Run the tests** (if any) to ensure everything works:
   ```bash
   pytest
   ```
   (The project currently does not have a full test suite; feel free to add one.)
4. **Make your changes** – keep the code style consistent (PEP‑8, type hints where appropriate).
5. **Update documentation** if you add new features or change existing behavior.
6. **Commit with a clear message** and push to your fork.
7. **Open a Pull Request** targeting the `main` branch.  Include a description of what you changed and why.

### Code Style
- Use 4‑space indentation.
- Keep line length ≤ 120 characters.
- Add type hints for public functions.
- Write docstrings for new functions/classes.

### Reporting Issues
If you encounter a bug or have a feature request, open an issue with:
- A short title.
- A detailed description.
- Steps to reproduce (for bugs).
- Expected vs. actual behavior.

Thank you for helping improve the AI Dating Project! 🎉
