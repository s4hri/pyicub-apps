# PyiCub Apps Collection

This repository contains a curated collection of independent PyiCub applications. Each application resides in its own folder within the `apps/` directory, complete with its own dependencies.

## Repository Structure

```
python-apps-collection/
├── apps/
│   ├── app1/
│   │   ├── main.py
│   │   ├── requirements.txt    # Python packages
│   │   └── packages.apt        # Ubuntu packages
│   ├── app2/
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── packages.apt
│   └── ...
├── Makefile
└── README.md
```

---

## Installation

Ensure you're using a Debian/Ubuntu-based system and have PyiCub installed.

### Install all apps

```bash
make all
```

### Install specific apps

To install selected apps (for example, `app1` and `app2`):

```bash
make app1 app2
```

### List available apps

```bash
make list
```

### Clean Python caches

```bash
make clean
```

---

## Adding a New App

To add a new Python application:

1. Create a new folder under `apps/` (e.g., `apps/my_app`).
2. Add your main Python file (`main.py` or similar).
3. Include a `requirements.txt` file with Python dependencies (one per line).
4. Optionally include a `packages.apt` file for Ubuntu packages (one per line).

Example:

```
apps/my_app/
├── main.py
├── requirements.txt
└── packages.apt
```

---

## Contributing

Feel free to contribute new apps or improvements. Fork this repo and submit a pull request!

---

Enjoy!

