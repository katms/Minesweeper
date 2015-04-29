import tkinter
import tkinter.messagebox
import random
import timer


class Minesweeper(tkinter.Frame):
    COLUMNS = range(8, 41)
    ROWS = range(8, 21)
    MIN_MINES = 10

    TIMER_WIDTH = 3
    COUNT_WIDTH = 4

    # difficulties
    EASY = (10,10,10)
    MEDIUM = (16,16,40)
    HARD = (30,15,90)

    @staticmethod
    def max_mines(columns, rows):
        return int(columns * rows * 0.9)

    def __init__(self, master, columns, rows, mines):
        super().__init__(master)

        # these are flipped once and then never again for rest of the game
        self.__first_move = True
        self.__game_over = False

        # Safe handles incrementing this
        self.safe_tiles_left = 0

        # [(x,y)] = Tile at (x, y)
        self.tiles = dict()

        # for recursively uncovering many tiles at once
        # not really a queue
        self.__queue = set()

        self.__columns = 0
        self.__rows = 0
        self.__mines = 0

        # count unflagged mines
        self.mines_left = tkinter.IntVar()
        self.count = tkinter.Label(self)
        self.mines_left.trace("w",
                              lambda *args: self.count.config(text="Mines left: {}".format(self.mines_left.get())))
        self.mines_left.set(self.__mines)

        self.timer = timer.Timer(self, lambda n: "Time: {}".format(int(n)))

        self.custom  = Custom(self)

        # create menu
        self.menu = tkinter.Menu(master, tearoff=False)
        self.menu.add_command(label="New Game", command=self.new_game)
        self.menu.add_command(label="Restart", command=self.reset_board)
        self.menu.add_separator()
        self.menu.add_command(label="Easy", command=lambda: self.set_dimensions(*Minesweeper.EASY))
        self.menu.add_command(label="Medium", command=lambda: self.set_dimensions(*Minesweeper.MEDIUM))
        self.menu.add_command(label="Hard", command=lambda: self.set_dimensions(*Minesweeper.HARD))
        self.menu.add_command(label="Custom", command=lambda: self.custom.grid())
        self.menu.add_separator()
        self.menu.add_command(label="Exit", command=self.quit)

        self.menu.invoke(3) # easy

        self.grid()

    def reset_board(self):
        """reset tiles in place"""
        if self.safe_tiles_left == 0:
            tkinter.messagebox.showwarning("You already won!", "You cannot restart this game.")
            return

        self.pre_game_setup()

        for tile in self.tiles.values():
            tile.reset()  # Safe handles incrementing

    def new_game(self):
        """
        Sets up a completely new game
        """
        for tile in self.tiles.values():
            tile.destroy()
        self.tiles.clear()

        self.pre_game_setup()

        self.__first_move = True

        self.place_mines()

    def pre_game_setup(self):
        """
        for steps common to reset() and new_game()
        """
        self.safe_tiles_left = 0
        self.__game_over = False
        self.mines_left.set(self.mines)
        self.timer.stop()
        self.timer.reset()

    def set_dimensions(self, columns, rows, mines):
        if columns in Minesweeper.COLUMNS:
            self.__columns = columns
            # keep timer on the right
            self.timer.grid(column=columns-Minesweeper.TIMER_WIDTH, columnspan=Minesweeper.TIMER_WIDTH)
        else:
            raise ValueError("Cannot set columns as "+str(columns))

        if rows in Minesweeper.ROWS:
            self.__rows = rows
            self.count.grid(row=rows, columnspan=Minesweeper.COUNT_WIDTH)
            self.timer.grid(row=rows)
        else:
            raise ValueError("Cannot set rows as "+str(rows))

        if mines < Minesweeper.MIN_MINES:
            raise ValueError("Not enough mines.")
        elif Minesweeper.max_mines(self.columns, self.rows) < mines:
            raise ValueError("Too many mines for this board size.")
        else:
            self.__mines = mines
            self.mines_left.set(self.mines)

        self.new_game()

    @property
    def columns(self):
        return self.__columns

    @property
    def rows(self):
        return self.__rows

    @property
    def mines(self):
        return self.__mines

    def set_game_over(self):
        self.timer.stop()
        self.__game_over = True

    @property
    def game_over(self):
        return self.__game_over

    def clear_first_move(self):
        self.__first_move = False

    @property
    def first_move(self):
        return self.__first_move

    def count_surrounding(self, column, row):
        counter = 0
        for n in self.neighbors(column, row):
            if type(self.tiles[n]) == Mine:
                counter += 1
        return counter

    def neighbors(self, column, row):
        xs = (x for x in range(column-1, column+2) if x in range(self.columns))
        for x in xs:
            ys = (y for y in range(row-1, row+2) if y in range(self.rows))
            for y in ys:
                yield (x, y)

    def queue_neighbors(self, column, row):
        """Clear every tile surrounding a Safe with a count of 0 one at a time"""

        # if queue is not empty then it's already in the process of being cleared
        being_cleared = bool(self.__queue)

        for n in self.neighbors(column, row):
            self.__queue.add(n)

        if not being_cleared:
            while self.__queue:
                item = self.__queue.pop()
                self.tiles[item].invoke()
                # this may call queue_neighbors() and add to the queue but that won't call clear_queue
                # cases of this while loop getting called more than once
                # are rare enough that it shouldn't ever crash as a result

    def make_safe(self, clicked):
        safe_tiles = filter(lambda x: type(x[1]) == Safe, self.tiles.items())
        other, tile = random.choice(list(safe_tiles))

        # switch tile locations
        self.tiles[clicked], self.tiles[other] = self.tiles[other], self.tiles[clicked]
        self.tiles[clicked].grid(column=clicked[0], row=clicked[1])
        self.tiles[other].grid(column=other[0], row=other[1])

        if tile.flagged:
            # switch flag so it stays in the same place
            # hypothetically every safe tile could be flagged which is why I'm not just ignoring those that are
            tile.flag()
            self.tiles[other].flag()

        self.tiles[other].reset()
        self.tiles[clicked].invoke()

    def place_mines(self):
        indices = [(x, y) for x in range(self.columns) for y in range(self.rows)]

        random.shuffle(indices)
        mine_indices = indices[:self.mines]

        for index in indices:
            if index in mine_indices:
                self.tiles[index] = Mine(self)
            else:
                self.tiles[index] = Safe(self)
            self.tiles[index].grid(column=index[0], row=index[1])

    def explode(self):
        if self.__game_over:
            return

        self.set_game_over()
        for tile in self.tiles.values():
            if type(tile) == Mine:
                tile.invoke()
            else:  # Safe
                if tile.flagged:
                    tile.flag()
                    tile.config(text="?", disabledforeground="gray")  # also a placeholder
                tile["state"] = tkinter.DISABLED
        self.play_again_or_quit("Game over", "You lose! ")

    def endgame(self):
        # if multiple tiles are cleared in the last move all of them call endgame()
        if self.__game_over or self.safe_tiles_left > 0:
            return

        self.set_game_over()

        # disable unflagged mines:
        # all Safe tiles are revealed and therefore can't be flagged
        for m in filter(lambda t: type(t) == Mine and not t.flagged, self.tiles.values()):
            m.mark()

        self.play_again_or_quit("Congratulations", "You win! ")

    def play_again_or_quit(self, title, message):
        if tkinter.messagebox.askquestion(title, message+"Play again?") == tkinter.messagebox.YES:
            self.new_game()


class Flaggable(tkinter.Button):
    """
    Superclass of Safe and Mine, handles construction, flagging, and most of reveal().
    """
    HEIGHT = 1
    WIDTH = 2*HEIGHT
    ACTIVE_BACKGROUND = "#" + "e0"*6
    DISABLED_BACKGROUND = '#'+'c'*12
    FLAG_COLOR = "#B82828"
    DEFAULT_DISABLED_FOREGROUND = "#737A6F"

    def __init__(self, master):
        super().__init__(master, command=self.reveal, height=Flaggable.HEIGHT, width=Flaggable.WIDTH, bd=2,
                         bg=Flaggable.ACTIVE_BACKGROUND, disabledforeground=Flaggable.DEFAULT_DISABLED_FOREGROUND)
        self.bind("<Button-3>", lambda e: self.flag())
        self.__flagged = False

    @property
    def flagged(self):
        return self.__flagged

    def flag(self):
        self.master.timer.start()

        # ignore if the tile was revealed or the game ended (the other reasons it would be disabled)
        if tkinter.DISABLED == self["state"] and not self.flagged:
            return

        self.__flagged = not self.flagged

        if self.flagged:
            self.config(text='F', disabledforeground=Flaggable.FLAG_COLOR, state=tkinter.DISABLED)
            self.master.mines_left.set(self.master.mines_left.get()-1)
        else:
            self.config(text='', fg="gray", state=tkinter.NORMAL)
            self.master.mines_left.set(self.master.mines_left.get()+1)

    def reveal(self):
        # disable self BEFORE calling a potentially recursive function that depends on tiles being disabled
        # SUNKEN instead of FLAT because it leaves borders
        self.config(state=tkinter.DISABLED, bg=Flaggable.DISABLED_BACKGROUND, relief=tkinter.SUNKEN)
        self._reveal()

    def reset(self):
        if self.flagged:
            self.flag()
        self.config(text="", state=tkinter.NORMAL, bg=Flaggable.ACTIVE_BACKGROUND, relief=tkinter.RAISED,
                    disabledforeground=Flaggable.DEFAULT_DISABLED_FOREGROUND)

    def _reveal(self):
        raise NotImplementedError("_reveal() is not implemented!")


class Mine(Flaggable):
    BLAST_COLOR = "#FF4000"

    def _reveal(self):
        if self.master.first_move:
            self.master.timer.start()
            location = (self.grid_info()['column'], self.grid_info()['row'])
            self.master.make_safe(location)
            self.master.clear_first_move()

        else:
            self.config(text='X', disabledforeground=Mine.BLAST_COLOR)
            self.master.explode()

    def mark(self):
        self.config(state=tkinter.DISABLED, text="M", disabledforeground=Flaggable.DEFAULT_DISABLED_FOREGROUND)


class Safe(Flaggable):
    COLORS = (None, "#0004FF", "#0F9111", "#000000", "#5b076b", "#999349", "#100076", "#6467CC", "#017615")

    def __init__(self, master):
        super().__init__(master)
        self.master.safe_tiles_left += 1

    def _reveal(self):
        self.master.timer.start()
        self.master.safe_tiles_left -= 1
        self.master.clear_first_move()

        info = self.grid_info()
        column = info["column"]
        row = info["row"]
        count = self.master.count_surrounding(column, row)

        if 0 != count:
            self.config(text=str(count), disabledforeground=Safe.COLORS[count])
        else:  # if 0 tile stays blank
            self.master.queue_neighbors(column, row)

        if 0 == self.master.safe_tiles_left:
            self.master.endgame()

    def reset(self):
        self.master.safe_tiles_left += 1
        super().reset()


class Custom(tkinter.Frame):
    def __init__(self, game, **options):
        super().__init__(game.master, **options)
        self.game = game

    def grid(self, **options):
        self['height'] = self.game.winfo_reqheight()
        self['width'] = self.game.winfo_reqwidth()

        self.game.grid_remove()
        super().grid(**options)


if __name__ == "__main__":
    root = tkinter.Tk()
    root.title("Minesweeper")
    root.resizable(False, False)
    minesweeper = Minesweeper(root, 10, 10, 10)

    top = tkinter.Menu(root)
    top.add_cascade(label="Game", menu=minesweeper.menu)
    root.config(menu=top)

    root.mainloop()