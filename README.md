# What is this?
An elegant (cursed) rewrite of Rhino Linux's [rhino-system](https://github.com/rhino-linux/rhino-system) utility in [flet.](flet.dev)

# Why?
The original application is not responsive to different screen sizes, the window doesn't even scale, my rewrite addresses these responsiveness issues.

# Works?
Yes, it's a complete, fully-functional rewrite.

# Building 
#### Using flet's built-in compiler is not recommended for this usage case.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/IMYdev/rhino-system-ng
    cd rhino-system-ng
    ```

2.  **Set up a virtual environment (recommended):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip3 install -r requirements.txt
    pip3 install pyinstaller
    ```
4.  **To build the application:**
    ```bash
    pyinstaller -n "rhino-system-ng" src/main.py
    ```

# Contributing

Contributions are welcome! bug fixes, and/or improvements are truly appreciated.

# Credits
- Rhino Linux [developers](https://discord.gg/jJxAh9Dt) for [Rhino Linux](https://rhinolinux.org/).

## 📄 License

This project is open-source and available under the GPLv3 copyleft.