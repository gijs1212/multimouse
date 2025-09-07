import multimouse as mm


def main():
    root = mm.ctk.CTk()
    root.withdraw()
    get_lang = lambda: mm.CURRENT_LANG
    set_lang = lambda lang: setattr(mm, "CURRENT_LANG", lang)
    win = mm.AutoSnapWindow(root, get_lang, set_lang, lambda: None)
    mm.set_window_icon(win, mm.APP_ICON_SNAP)
    # start combi immediately
    root.after(0, win._start_combi)
    root.mainloop()


if __name__ == "__main__":
    main()
