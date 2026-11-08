# Human Perception & Performance Tester

An offline Tkinter application for an ambiguous-figure identification activity and a target-hitting activity.

## Requirements and launch

- Windows with Python 3.9 or later and Tkinter available.
- No third-party Python packages or internet connection are required.
- From this project folder, run:

```powershell
python main.py
```

Task-specific figure rendering and target-condition scheduling live in `screens\`; shared visual palettes and brightness simulation live in `main_settings.py`; CSV persistence is handled by `data_logger.py`.

The application content scrolls with the mouse wheel or the vertical scrollbar. Use Shift+mouse wheel or the horizontal scrollbar for wide content.

The application creates `data\performance_results.csv` relative to the project files. It writes the agreed header on first launch and appends records; existing rows are not replaced. Do not edit the header. If it does not match the current schema, the application stops instead of risking existing data.

## Use

1. Select **Start experiment** and enter an anonymous participant ID. Reusing an ID prompts for confirmation and creates a separate session.
2. Select an activity. Visual settings apply to the experimental stimulus only, can be changed between trials, and are captured in each attempt.
3. In the identification activity, select **Show figure and start trial**, choose an interpretation, and rate its ease.
4. In the target activity, place the pointer inside the start circle and press **Space**. Click the target; misses are counted and the timer continues. Rate completed attempts.
5. Press **Escape** to abort an active trial. Target trials time out after 30 seconds. Aborted and timed-out attempts are recorded with their outcome and excluded from performance summaries.
6. The target activity includes one unscored practice trial followed by 27 measured trials: three repetitions of each size-distance combination, in a shuffled order.

## Visual condition definitions

- Contrast palettes (work area only): High `#f7f7f7` / `#111111`; Medium `#dedede` / `#555555`; Low `#bcbcbc` / `#858585` (background / foreground).
- Brightness scales each RGB channel by `0.35 + 0.65 × brightness / 100`; even at zero, work-area colors retain at least 35% of their base value. This simulates application color changes, not physical monitor luminance.
- Interface font size options are Small 10 pt, Medium 13 pt, and Large 16 pt. Target diameters are separately controlled by the trial condition: 15, 30, and 50 canvas pixels.
- Target distance is center-to-center: 100, 250, or 400 canvas pixels. The start point is at `(150, 300)`; targets are placed to its right.

## Data

`data\performance_results.csv` starts with its column header and is populated with actual participant responses as the application is used; no sample or fabricated results are included. Each row represents a completed, aborted, or timed-out attempt. It contains unique session and trial IDs, the target-order random seed, trial order, practice status, task outcome, visual settings, task response/timing, elapsed attempt time for interrupted attempts, target geometry where applicable, incorrect clicks, and ease rating. `click_time_seconds` is reserved for successfully acquired targets; `attempt_elapsed_seconds` records elapsed time for aborted and timed-out attempts. Fields that do not apply are blank. Completed-trial summaries exclude practice, aborted, and timed-out attempts.

If a save fails because the file is unavailable (for example, open in a spreadsheet application), the row is retained in the running application. Close the file and select **Retry unsaved results** before exiting.

## Tests

Run the standard-library data logger tests with:

```powershell
python -m unittest -v
```
