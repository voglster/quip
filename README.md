# Quip

A frictionless thought capture tool designed to interrupt your workflow as little as possible.

## Vision

Press hotkey → capture thought → back to work.

Quip is built for those moments when an idea pops into your head and you need to capture it *instantly* without breaking your flow. No windows to manage, no apps to switch to - just pure, instant thought capture.

## Current Features

- **Instant capture**: Global hotkey spawns a minimal overlay
- **AI-powered improvement**: Ctrl+I improves text with local or cloud LLMs
- **Undo support**: Ctrl+Z restores original text after AI improvements
- **Dark theme**: Easy on the eyes during late-night inspiration
- **Automatic save**: Notes go to `~/notes/5. Inbox/Inbox.md`
- **Zero friction**: Escape to dismiss, Ctrl+Enter to save

## Quick Start

```bash
# Quick install (coming soon)
curl -sSL https://raw.githubusercontent.com/voglster/quip/main/install.sh | bash

# Manual install
git clone https://github.com/voglster/quip.git
cd quip/desktop
uv sync
uv run quip
```

## Components

- **[desktop/](desktop/)** - Python tkinter app for instant thought capture
- **[mobile/](mobile/)** - Expo/React Native mobile companion (planned)
- **[web/](web/)** - Web interface for note review and management (planned)  
- **[server/](server/)** - Backend API for sync and processing (planned)
- **[shared/](shared/)** - Common utilities and types (planned)

## Usage

1. Press your configured hotkey (default: `Win+Space`)
2. Type your thought
3. Press `Ctrl+I` to improve with AI (optional)
4. Press `Ctrl+Z` to undo improvements if needed
5. Press `Ctrl+Enter` to save, or `Escape` to dismiss
6. Continue with what you were doing

## LLM Configuration

Quip supports AI-powered note improvement with various providers. Configure in `~/.config/quip/config.toml`:

### OpenAI (GPT-4, GPT-3.5)
```toml
[llm]
enabled = true
base_url = "https://api.openai.com/v1"
model = "gpt-4o-mini"
api_key = "sk-your-openai-api-key"
timeout_seconds = 30
max_tokens = 1000
temperature = 0.7
improve_prompt = "Fix spelling, grammar, and clarity while preserving meaning. Return only the improved text:"
```

### Google Gemini
```toml
[llm]
enabled = true
base_url = "https://generativelanguage.googleapis.com/v1beta"
model = "gemini-1.5-flash"
api_key = "your-gemini-api-key"
timeout_seconds = 30
max_tokens = 1000
temperature = 0.7
improve_prompt = "Fix spelling, grammar, and clarity while preserving meaning. Return only the improved text:"
```

### Local Ollama
```toml
[llm]
enabled = true
base_url = "http://localhost:11434/v1"
model = "llama3.2:3b"
api_key = ""
timeout_seconds = 30
max_tokens = 1000
temperature = 0.7
improve_prompt = "Fix spelling, grammar, and clarity while preserving meaning. Return only the improved text:"
```

**Hotkeys:**
- `Ctrl+I` - Improve note with AI
- `Ctrl+Z` - Undo last improvement
- `Ctrl+S` - Open settings file

## Planned Improvements

### Core Enhancements
- **Borderless overlay UI** - Remove window decorations for true overlay experience
- **Global hotkey system** - Spawn from anywhere, regardless of current app
- **LLM cleanup** - Optional AI-powered note clarification (integrates with local Ollama)
- **Voice recording** - Speak your thoughts, get them transcribed

### Philosophy
This tool is intentionally minimal. It does one thing well: captures errant thoughts without breaking your concentration. 

- 90% of the time: type → save → continue
- 10% of the time: type → cleanup with AI → save → continue

No complex organization, no sync, no themes. Just instant, reliable thought capture.

## Technical Details

- **Built with**: Python + tkinter (for now)
- **Storage**: Plain text markdown files
- **Requirements**: Python 3.8+, managed with `uv`
- **Target platforms**: Linux (primary), macOS (secondary)

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for the complete roadmap and implementation plan.

### Setup
```bash
# Desktop development
cd desktop
uv sync --group dev
uv run pre-commit install
```

### Development Workflow
```bash
# Run the app
uv run quip

# Code quality (run before committing)
uv run ruff check desktop/ --fix
uv run ruff format desktop/
uv run pre-commit run --all-files

# Commit changes
git add .
git commit -m "feat: add new feature"
```

### Commit Style
Use [Conventional Commits](https://www.conventionalcommits.org/) for clean history:

- `feat:` - New features
- `fix:` - Bug fixes  
- `refactor:` - Code refactoring
- `docs:` - Documentation changes
- `style:` - Code style/formatting
- `test:` - Adding tests
- `chore:` - Maintenance tasks

Keep commits small, focused, and incremental. Run pre-commit hooks before every commit.

## Contributing

We welcome contributions to Quip! By submitting code to this repository, you agree to the following:

### Contributor License Agreement

**By contributing code to this repository, you:**

1. **Grant full rights**: You assign all rights, title, and interest in your contributions to this repository
2. **License compatibility**: Your contributions will be licensed under the same SSPL license as the project
3. **Legal immunity**: You waive any claims against the project maintainers and users regarding your contributions
4. **Code ownership**: The repository gains full ownership and usage rights to your contributed code
5. **No revocation**: You cannot later revoke these rights or remove your contributions

### What this means:

- ✅ Your contributions help make Quip better for everyone
- ✅ The project can evolve freely without legal complications  
- ✅ All code remains open source under SSPL
- ❌ You cannot later claim ownership or demand removal of your contributions
- ❌ You cannot sue the project or users over your contributed code

**By submitting a pull request, you acknowledge that you have read and agree to these terms.**

### How to Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes following our coding standards
4. Run tests and pre-commit hooks: `uv run pre-commit run --all-files`
5. Commit with conventional commit format: `git commit -m "feat: add amazing feature"`
6. Push to your fork: `git push origin feature/amazing-feature`
7. Open a pull request

## License

This project is licensed under the **Server Side Public License (SSPL) v1** - see the [LICENSE](LICENSE) file for details.

**What this means:**
- ✅ Free to use, modify, and distribute
- ✅ Must share your modifications under the same license
- ❌ Cannot host as a commercial service without open-sourcing your entire hosting infrastructure

## Why Quip?

Because good ideas don't wait for you to open the right app, find the right document, or switch contexts. They appear in the shower, during meetings, while debugging, at 2 AM.

Quip is there for those moments.

---

*Currently in active development - expect rapid iteration as we perfect the capture experience.*