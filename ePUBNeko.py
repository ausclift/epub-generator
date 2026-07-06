import tkinter as tk

from neko_model.model import Model
from neko_view.view import View


def main():
    root = tk.Tk()

    model = Model()
    View(root, model)

    root.mainloop()


if __name__ == "__main__":
    main()
