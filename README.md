![Version](https://img.shields.io/badge/Version-Beta%200.0.1-orange?style=for-the-badge) ![License](https://img.shields.io/badge/License-GPL%20v3-blue?style=for-the-badge) ![Platform](https://img.shields.io/badge/Platform-Linux-yellow?style=for-the-badge&logo=linux)

# Petra

<img src="icons/petra.png" width="100" height="100">

A different clipboard for Linux, my way.

## Features

- Allows copying and pasting text, images, links, console commands, and emojis
- Filter by copied item type
- General search, by type or emoji
- Open links directly in the browser
- Keyboard navigation (q, w, ctrl+f, esc, and arrow keys)
- Preview copied image
- Pin window
- Wide variety of themes and colors
- Start on system boot
- Save items and manually delete them or clear all
- Open on the left or right of the screen or at mouse position
- Choose keyboard shortcut

## Screenshots

![Screenshot 1](screenshots/screenshot_1.png)
![Screenshot 2](screenshots/screenshot_2.png)
![Screenshot 3](screenshots/screenshot_3.png)
![Screenshot 4](screenshots/screenshot_4.png)
![Screenshot 5](screenshots/screenshot_5.png)
![Screenshot 6](screenshots/screenshot_6.png)

## Installation

You can install Petra or generate distributable packages by running the included build script in the project folder:

```bash
./install.sh
```

This will launch an interactive menu with the following options:
1. **Build & Install Locally** (Directly installs a development Flatpak)
2. **Create Flatpak Bundle & Install** (Generates a `.flatpak` and installs it)
3. **Create Flatpak Bundle Only** (Generates a `.flatpak` for distribution)
4. **Create Debian Package** (Generates a `.deb` package)
5. **Create AppImage** (Generates a fully standalone `.AppImage` portable executable)

All generated bundles are saved in the `output/` directory.

## License

GPL-3.0

## Credits

Icons by [ProCode](https://github.com/ProCode-Software/proicons)

---

<p align="center">
  <a href="https://paypal.me/gessendarien" target="_blank">
    <img src="https://img.shields.io/badge/Donate-PayPal-blue.svg?style=flat-square&logo=paypal" alt="Donate with PayPal" />
  </a>
</p>

<p align="center">
  <sub>Made with 💚</sub>
</p>
