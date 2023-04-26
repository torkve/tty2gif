# tty2gif

It is a simple script to convert ttyrec files into gifs. It is based on some ancient [work](https://gist.github.com/yangchenyun/17c616d05ee0fbbe27700156d77df729) for OS X, and was adapted to linux with Gtk3.

Note, that it probably can give not the best result on desktops with settings other than mine ones. I tested it in my KDE environment with X server, single display, and no window decorations for my Konsole terminal.

## System requirements

- python3
- python gtk3.0 bindings
- ffmpeg

## Running

Run it as `python3 tty2gif.py [--output tty.gif] [--factor N] output /path/to/ttyrec`.
For example:

    python3 tty2gif.py --factor 2 output ./ttyrec
