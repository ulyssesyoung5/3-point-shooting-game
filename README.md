# 3-Point Shooting Game

A fast, simple basketball shooting game inspired by the original Scratch project.
You have 60 seconds to make as many three-point shots as possible. Every basket
is worth exactly 3 points. It runs as a native Pygame app and directly in a
browser through [Pygbag](https://pygame-web.github.io/).

## Run locally

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python game.py
```

## Play in a browser

The project is published automatically to GitHub Pages from the `main` branch.
Open the repository's **Settings → Pages** page to see the deployed URL, or use
the workflow's deployment summary after a push.

To build the browser version locally:

```bash
python -m pip install pygbag
python -m pygbag --build game.py
```

Pygbag writes the static site to `build/web/`. Serve that directory with a local
HTTP server (rather than opening `index.html` directly) to test it:

```bash
python -m http.server 8000 --directory build/web
```

Then open <http://localhost:8000/>.

## Controls

- **Left / Right arrows:** Adjust the shooting angle.
- **Hold Space, then release:** Charge power and shoot.
- **R** or the **RESTART** button: Start a new 60-second round.
- Close the game window to quit.

The game uses only Pygame-drawn shapes, so no additional images or downloads are
needed. The browser build uses the same controls and 60-second game loop as the
desktop version.