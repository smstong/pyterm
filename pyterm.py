#!/usr/bin/env python3
import tkinter as tk
import pty
import sys,os
from select import select
import threading

class Term(tk.Text):
    """
    Super simplified Terminal Emulator in Python.

    ToDo:
        - Updating UI should NOT be done by non-UI thread
        - More control code to be implemented

    """
    def __init__(self, parent=None, **options):
        tk.Text.__init__(self, parent, **options)
        self.configure(bg='black', fg='white', font=('Arial', 16, 'bold'))
        self.pack(expand=tk.YES, fill=tk.BOTH)
        self.focus()

        self.masterPty = None
        self.masterRecvBuf = bytes()
        self.inEscape = False

        self.bind('<Key>', self.onKey)
        self.startShell()

    def onKey(self, event):
        key = event.char
        data = key.encode('utf-8')
        print(f'master write: {data}')
        os.write(self.masterPty, data)

        return "break" # stop further event handling

    def readMaster(self):
        while True:
            readables, writables, exceptions = select(
                    [self.masterPty], 
                    [], 
                    [self.masterPty])

            for fd in readables:
                try:
                    byte = os.read(fd, 1)
                except:
                    print("shell exited.")
                    os._exit(0)
                    return

                self.ttyProtocol(byte)

            for fd in exceptions:
                print("exception")
                return

    def ttyEscape(self):
        """
        CSI Escape handling. Only implemented 'clear screen' here.
        """
        # control sequences handling
        if self.masterRecvBuf == b'\x1b[H':
            self.delete('1.0', tk.END)
            return True

        elif self.masterRecvBuf == b'\x1b[J':
            self.delete('1.0', tk.END)
            return True

        # unrecognized control sequence
        if len(self.masterRecvBuf) > 5:
            return True

        return False

    def ttyNormalByte(self, byte):
        """
        Non Escape handling. Have NOT implmented C0 control code at all!!
        """
        if byte == b'\r':
            pass
        else:
            self.insert(tk.END, byte.decode('utf-8'))

    def ttyProtocol(self, byte):
        """
        handle input to master pty. Many inputs come from the master itself
        (echo mode), others from apps printing
        """
        print(f"master recv: {byte}, inEscape: {self.inEscape}")

        if byte in b'\x1b':
            self.inEscape = True

        if self.inEscape:
            self.masterRecvBuf += byte
            if self.ttyEscape():
                self.masterRecvBuf = bytes()
                self.inEscape = False
        else:
            self.ttyNormalByte(byte)

    def startShell(self):
        pid, self.masterPty = pty.fork()

        if pid == 0:
            os.execvp('/bin/sh', ("/bin/sh",))

        else:
            threading.Thread(target=(lambda: self.readMaster())).start()

def test_me():
    root = tk.Tk()
    root.title('PyTerm')
    Term(root)
    tk.mainloop()

if __name__ == '__main__':
    test_me()
