# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.2] - 2026-03-12

### Added

- Gutter toggle — show/hide the line-number gutter via toolbar button, keyboard shortcut (⇧⌘G / Ctrl+Shift+G), or command palette
- `show_gutter` constructor parameter for `EnhancedCodeEditor`

### Changed

- Increase standalone app window height for better default experience

## [0.1.1] - 2026-03-10

### Added

- Python 3.14 support

### Fixed

- File open scrolling to bottom when language unchanged
- Search Enter key skipping first match
- Inconsistencies between SearchReplaceBar and DiffPane APIs
- SearchReplaceBar.recompute() now calls _safe_update() internally

## [0.1.0] - 2026-03-06

### Added

- Reusable `EnhancedCodeEditor` control (`ft.Column` subclass) with file toolbar, syntax highlighting, and status bar
- File operations: Open, Save, Save As, Close with unsaved-changes confirmation
- Native AppleScript file dialogs on macOS, Flet FilePicker fallback elsewhere
- Search and Replace bar with match counting, case sensitivity toggle, whole word toggle, and prev/next navigation
- Command Palette with searchable list of all actions (Cmd+Shift+P / Ctrl+Shift+P)
- Theme selector dialog with 89 built-in syntax highlighting themes
- Language selector with common/full list toggle and auto-detection for 40+ file extensions
- Go to Line dialog (Cmd+G / Ctrl+G)
- Read-only mode toggle (Cmd+L / Ctrl+L)
- Font size controls (Cmd+= / Cmd+-)
- Toggleable unified diff pane showing changes since last save
- Ruff-on-save toggle: auto-runs `ruff check --fix` and `ruff format` on Python files
- Help dialog with keyboard shortcut reference
- Dirty-file tracking with visual indicator
- Keyboard shortcuts for all major operations
- Standalone entry point via `fce-enhanced` CLI command
