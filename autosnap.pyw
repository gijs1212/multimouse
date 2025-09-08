import multimouse as mm


def main():
    # separate AutoSnap launcher using MultiMouse components
    app = mm.MultiMouseApp()
    app.root.withdraw()
    win = mm.AutoSnapWindow(
        app.root,
        lambda: app.lang_var.get(),
        app._switch_lang,
        app.save_combined_settings,
        app.load_combined_settings,
    )
    mm.set_window_icon(win, mm.APP_ICON_SNAP)
    app._apply_theme(mark_dirty=False)
    # ensure the AutoSnap window becomes visible when launched standalone
    win.after(0, lambda: (win.deiconify(), win.lift(), win.focus_force()))
    app.root.mainloop()


if __name__ == "__main__":
    main()
