# 3-Point Shooting Game

A fast, simple basketball shooting game inspired by the original Scratch project.
You have 60 seconds to make as many three-point shots as possible. Every basket
is worth exactly 3 points.

## Run locally

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python game.py
```

## Controls

- **Left / Right arrows:** Adjust the shooting angle.
- **Hold Space, then release:** Charge power and shoot.
- **R** or the **RESTART** button: Start a new 60-second round.
- Close the game window to quit.

The game uses only Pygame-drawn shapes, so no additional images or downloads are
needed.