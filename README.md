![Version](https://img.shields.io/badge/Version-Beta%200.0.1-orange?style=for-the-badge) ![License](https://img.shields.io/badge/License-GPL%20v3-blue?style=for-the-badge) ![Platform](https://img.shields.io/badge/Platform-Linux-yellow?style=for-the-badge&logo=linux)

# Petra

Clipboard manager for Linux.

## Features

- Allows copying and pasting text, images, links, console commands, and emojis.
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

This application is currently in the testing phase to be uploaded to Flathub. Meanwhile, you can test it by running the following commands in your terminal, depending on what you want to do.

First of all, verify that you have the necessary dependencies:
```bash
./check-dependencies.sh
```

To build the Flatpak (for testing and direct installation):
```bash
./build-flatpak.sh
```

To create a distributable .flatpak file:
```bash
./make-flatpak.sh
```

To install the newly created Flatpak:
```bash
./install-flatpak.sh
```

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
