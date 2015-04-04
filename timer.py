import tkinter
import time

class Timer(tkinter.Label):
    def __init__(self, master, label):
        super().__init__(master)
        self.seconds = tkinter.IntVar()

        def update(*args):
            self["text"] = label+str(self.seconds.get())

        self.seconds.trace('w', update)
        self.seconds.set(0)

        self._startpoint = 0
        self._offset = 0
        self.running = False
        self._cancel = None

    def start(self):
        if not self.running:
            self.running = True
            self._startpoint = time.time()
            self._run()

    def stop(self):
        if self.running:
            self.running = False
            self.after_cancel(self._cancel)
            self._offset = self.seconds.get()


    def _run(self):
        self.seconds.set(time.time() - self._startpoint + self._offset)
        self._cancel = self.after(100, self._run)

if __name__ == '__main__':
    root = tkinter.Tk()
    timer = Timer(root, "Seconds passed: ")
    timer.grid()


    timer.bind("<Button-1>", lambda e: timer.start())
    timer.bind("<Button-3>", lambda e: timer.stop())
    root.mainloop()