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
- Use the **Personen** button to record up to eight recipients for snap sending.
- Calibrate the red badges once; AutoSnap reacts when red appears at those positions.
- The combi tab offers a **Kleur scanner** button to capture a specific badge color; disable it to match any red badge.
 - Enable **Snap verzenden op start** to send a snap to selected recipients before combi begins; choose them via the checkboxes under the option.
- You can choose to restart Snapchat after a set number of snaps or minutes; leave the fields empty to disable.
 - When sending a snap (not replying), AutoSnap closes and reopens Snapchat, taps **Foto 1**, waits 2 s, taps **Foto 2**, waits 1 s, taps **Send to** and pauses 1 s, selects each configured person with 0.5 s between, then taps **Verzend**.
