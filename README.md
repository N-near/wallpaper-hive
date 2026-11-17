# 🖼️ Hexagonal Wallpaper Gallery

![Hexagonal Wallpaper Gallery Screenshot](assets/screenshot.png)

A fast and interactive hexagonal (honeycomb) wallpaper gallery for Linux, designed to make choosing your desktop background a visual and fun experience.

*(Note: This is the initial Python implementation. A Rust rewrite is currently in development for blazingly fast performance!)*

## ✨ Features
*   Displays wallpapers in an irregular honeycomb (hexagonal) layout.
*   Click on any hexagon to instantly apply the wallpaper to your desktop using `swaybg`.
*   Transparent, borderless window that integrates with Wayland compositors (like Niri).
*   Smooth image scaling and cropping to fit the hexagons.

## 🛠️ Technologies Used
*   **Python 3**
*   **GTK 3** (Graphical User Interface)
*   **Cairo** (2D vector graphics for drawing the hexagons)
*   **Linux / Wayland**

## 🚀 How to Run
Make sure you have the required dependencies installed (GTK 3, PyGObject, Cairo, and Swaybg for Wayland users).

    python3 gallery.py

