# Contributing to fce-enhanced

First off, thank you for even considering contributing!

I created this project as a way to stay active, keep my brain busy, and explore the world of Python and Flet. I've only been using Git for a few weeks, so if we’re both learning, that's even better!

### A Note on Response Times

I'm retired and code for the pure fun of it. While I’m excited to see your ideas, I may not respond immediately to Issues or Pull Requests. Sometimes I’m deep in a new feature, and sometimes I’m just enjoying life away from the screen. Thank you for your patience!

---

### How You Can Help

You don't have to be a "pro" to contribute. Here are a few ways to help:

1. **Report Bugs:** If something crashes or looks weird, open an [Issue](https://github.com/oktl/flet-fce-enhanced/issues).
2. **Suggest Features:** Have an idea for a cool shortcut or a theme? Let me know!
3. **Improve Documentation:** If my instructions are confusing, help me make them clearer.
4. **Code Tweaks:** If you see a way to make the Python code cleaner or faster, feel free to submit a Pull Request.

---

### Development Setup

Since this project uses `uv`, getting started is fairly simple:

1. **Fork** the repository to your own account.
2. **Clone** your fork to your machine.
3. Run `uv sync` to set up the environment and dependencies.
4. Run `source .venv/bin/activate` to activate the virtual environment.
5. (Optional) Run `pre-commit install` to enable the automatic code formatting.

---

### Submitting a Change

Since I'm still getting the hang of Git myself, let's keep the process simple:

1. Create a new **branch** for your change (e.g., `git checkout -b fix-my-bug`).
2. Make your changes and test them.
3. Run `uv run ruff check .` to make sure the code style looks good.
4. Test: Run `uv run pytest`. This runs the automated tests to make sure everything still works as expected.

    >_**Note**: If a test fails and you aren't sure why, feel free to ask! We're all learning here._

5. **Commit** your changes and **Push** them to your GitHub.
6. Open a **Pull Request** and tell me a bit about what you changed!

### Code of Conduct

Please be kind. I’m doing this for fun and learning, and I hope you are too!
