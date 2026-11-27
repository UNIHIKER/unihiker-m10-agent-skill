#!/usr/bin/env python3
"""Time-limited 240×320 Tk preview on the board, with optional test-only input feedback."""
import argparse
import tkinter as tk


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=int, default=10, choices=range(3, 31), metavar='3..30')
    parser.add_argument('--input-demo', action='store_true', help='Give this test window focus and report clicks and the a key only.')
    args = parser.parse_args()
    root = tk.Tk()
    root.title('M10 preview')
    root.geometry('240x320+0+0')
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.configure(bg='#143449')
    tk.Label(root, text='UNIHIKER M10\n240 x 320', bg='#143449', fg='white', font=('Sans', 20)).pack(pady=65)
    status = tk.Label(root, text='Temporary screen preview', bg='#143449', fg='#99ddff')
    status.pack()

    def feedback(message):
        status.configure(text=message)
        print(message, flush=True)

    def ready():
        if args.input_demo:
            root.focus_force()
        print('preview-ready', flush=True)

    if args.input_demo:
        root.bind('<Button-1>', lambda event: feedback('click {} {}'.format(event.x_root, event.y_root)))
        root.bind('<KeyPress-a>', lambda _event: feedback('key a'))
    root.after(200, ready)
    root.after(args.seconds * 1000, root.destroy)
    root.mainloop()


if __name__ == '__main__':
    main()
