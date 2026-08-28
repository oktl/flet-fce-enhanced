# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.6] - 2026-03-17

### Fix

Flet 0.80+ API violations: async handlers and dialog/snackbar management

Replace pre-0.80 patterns with correct Flet 0.81 APIs:

- Add sync click wrappers using page.run_task() for all async on_click/on_keyboard_event handlers
- Migrate page.overlay.append/remove to page.show_dialog()/page.pop_dialog()
- Migrate dialog.open = True/False to show_dialog/pop_dialog
- Fix async on_tap_link handler in help dialog to sync wrapper
- Update test mocks and assertions for new API

## [0.1.5] - 2026-03-15

### Changed

- Ruff on Save now auto-enables when opening or saving-as a Python file, and auto-disables for non-Python files and on close
- Error snackbars are now dismissed automatically on successful save
- New snackbars close any existing snackbar before appearing

## [0.1.4] - 2026-03-13

### Fixed

- Revert to Saved now resets cursor and scroll position to the top of the file (previously jumped to end)

### Changed

- Add Revert to Saved to README features and keyboard shortcuts table

## [0.1.3] - 2026-03-12

### Changed

- Fix `language` constructor default from `PYTHON` to `PLAINTEXT` in README
- Document all public exports from `fce_enhanced` package
- Expand `on_title_change` callback documentation
- Add Ruff on Save behavior details (silent skip, snackbar warnings, auto-reload)
- Add platform notes for native file dialogs
- Improve Search & Replace docs (whole word, Enter navigation, Replace All)
- Note that Command Palette, Theme Selector, and Language Selector are searchable
- Change theme count to "80+" to avoid maintenance

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
