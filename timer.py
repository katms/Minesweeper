import tkinter
import time

class Timer(tkinter.Label):
    def __init__(self, master, label="", **options):
        super().__init__(master, **options)
        self.seconds = tkinter.DoubleVar()

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
            if self._cancel is not None:
                self.after_cancel(self._cancel)
                self._cancel = None
            self._offset = self._calculate_time()

    def flip_state(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def reset(self):
        if self.running:
            self._startpoint = time.time()

        else:
            self._startpoint = None
        self._offset = 0
        self.seconds.set(0)

    def _run(self):
        self.seconds.set(self._calculate_time())
        self._cancel = self.after(100, self._run)

    def _calculate_time(self):
        return time.time() - self._startpoint + self._offset


if __name__ == '__main__':
    root = tkinter.Tk()
    timer = Timer(root, "Seconds passed: ")
    timer.grid()


    timer.bind("<Button-1>", lambda e: timer.flip_state())
    timer.bind("<Button-3>", lambda e: timer.reset())
    root.mainloop()