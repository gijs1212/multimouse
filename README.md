# multimouse
multimouse is an tinytask alternative (now called remouse) it records mouse movement/clicks/scrolls and keyboard clicks. this is not paid, but it still needs work. feel free to publish better versions
make sure the .ico files are in the same folder as the .pyw file

## Standalone launchers
- `autosnap.pyw` – open the AutoSnap menu directly without the main MultiMouse window
- `autosnap_combi.pyw` – start the AutoSnap combi automation immediately; it launches Snapchat via the shortcut you selected in AutoSnap's settings (falls back to `%USERPROFILE%\\Desktop\\Snapchat.lnk`) and then begins the workflow. Press `Esc` to stop.

## Startup script
- `autosnap_startup.py` waits five seconds, opens Snapchat via the shortcut path stored in AutoSnap's settings (or the Windows zoekbalk if none is set), clears unread snaps, sends one to all eight configured recipients and then runs AutoSnap combi using your saved settings.

## Settings
- In the AutoSnap menu you can save or load a configuration file. Enable **Instellingen automatisch laden bij start** and choose a **Startup settings file** in the settings wheel to load that file automatically when the program starts.
- In AutoSnap combi, calibrate **Foto 1 (sender)**, **Foto 2 (sender)** and **Foto (reply)**.
- Optional **Snap sluiten** lets the responder close a snap before replying when calibrated and enabled.
- You can choose to restart Snapchat after a set number of snaps or minutes; leave the fields empty to disable.
