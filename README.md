# EECS581-Project-3

Bug Game is a desktop game with one player swarm and one AI swarm. Use WASD or
the arrow keys to move. Your swarm attacks automatically when the AI gets close.
Stay just outside its attack range and press R after a round to play again.

## Run the game

Use Python 3.11 through 3.14 and run the commands from the project folder.
The examples use 3.14. Replace it with your installed version if needed.
The game needs a graphical desktop and a keyboard.

**Windows (PowerShell)**

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src/main.py
```

**macOS or Linux**

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python src/main.py
```

The [Raylib package](https://pypi.org/project/raylib/6.2.0.0/) lists the available
desktop binaries and system requirements. On Ubuntu, install `libgl1` and
`libx11-6` if Raylib reports that those libraries are missing.

## Run the tests

On macOS or Linux, run `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v`.
On Windows, set `$env:PYTHONPATH = 'src'` in PowerShell and run
`.\.venv\Scripts\python.exe -m unittest discover -s tests -v`.

The [project submission documents](/docs) are also in this repository.
