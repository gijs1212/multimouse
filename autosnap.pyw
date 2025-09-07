import multimouse as mm


def main():
    # separate AutoSnap launcher using MultiMouse components
    root = mm.ctk.CTk()
    root.withdraw()
    get_lang = lambda: mm.CURRENT_LANG
    set_lang = lambda lang: setattr(mm, "CURRENT_LANG", lang)
    win = mm.AutoSnapWindow(root, get_lang, set_lang, lambda: None)
    mm.set_window_icon(win, mm.APP_ICON_SNAP)
    root.mainloop()


if __name__ == "__main__":
    main()
