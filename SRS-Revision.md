# Human Perception & Performance Tester
## SRS Revision and Clarifications

This document provides implementation-ready replacements and additions to the supplied SRS. Apply these clauses in place of conflicting or ambiguous requirements in the original; retain the original requirements where this document makes no change.

## 1. Study procedure and terminology

### 1.1 Definitions

- **Experiment**: the overall study procedure.
- **Session**: one participant's visit to the application, identified by a unique `session_id`.
- **Trial**: one presentation and response for one task, identified by a unique `trial_id`.
- **Completed trial**: a trial with a valid task response and required ease rating.
- **Attempt outcome**: `completed`, `timed_out`, or `aborted`.
- **Visual condition**: the contrast mode, interface size, and brightness value captured when a trial begins.

The application shall not treat a participant ID as a unique session identifier. Reusing an ID shall be permitted for a returning participant. Starting a new session with an existing ID shall display a warning and require confirmation. Resuming an existing session shall be a distinct, explicit action; the application shall not silently combine separate visits.

### 1.2 Condition assignment

Before each trial, the experimenter or participant shall select the visual settings and task condition required by the study protocol. The application shall capture those settings when the trial begins and shall not permit them to change during a timed trial. Settings may be changed between trials.

The application shall record condition values for every attempt. It shall not claim that a setting caused a performance difference unless the experiment protocol controls other conditions and the report describes that protocol. Trial order shall be recorded. Target-condition order shall be randomized within each participant's session, with the random seed stored for reproducibility.

### 1.3 Participant safeguards

The instructions shall state that participation is voluntary and may be stopped at any time. Escape shall abort an active trial without marking it completed. The application shall request only an anonymous participant ID and shall not collect names or other direct identifiers. The experimenter is responsible for any consent, course, or institutional approval required for the study.

## 2. Visual conditions and accessibility

### 2.1 Controls during trials

Visual settings shall be adjustable between trials, not during timed trials. The selected values shall be displayed before the trial starts and captured in that trial's data row.

### 2.2 Contrast

The implementation shall define and document exact foreground/background color pairs for High, Medium, and Low contrast. These modes shall affect the experimental stimulus and task work area. Navigation, instructions, rating controls, and error messages shall retain readable contrast and shall not be hidden or made unusable by an experimental setting.

### 2.3 Interface size

The implementation shall document the font sizes and other dimensions used for Small, Medium, and Large. Size scaling shall apply to the designated interface elements, not the target diameter used as an experimental variable. The actual configured sizes shall be logged where they differ from the predefined labels.

### 2.4 Brightness simulation

Brightness is a simulated application color adjustment, not physical monitor luminance. The implementation shall document the transformation used for each slider value. It shall apply only to the experimental work area and stimulus, leaving essential controls and instructions legible. The integer slider value from 0 through 100 shall be recorded. The label “brightness” shall not imply a calibrated luminance measurement.

### 2.5 Accessibility

Experimental contrast or size conditions shall not override the accessibility of essential controls. All actions shall be available by keyboard, controls shall have text labels, keyboard focus shall be visible, and color alone shall not indicate task state or errors. Participants shall be able to stop a trial and return to task selection without losing earlier saved records.

## 3. Identification task procedure

The same documented Rubin vase-style figure shall be used for every identification trial. The trial timer shall start immediately before the figure is made visible and stop on the first valid answer submission. Time spent reading instructions or selecting a rating shall not be included.

Responses shall be selected from “A vase,” “Two faces,” “Both interpretations,” or “Something else.” Selecting the last option shall require non-empty descriptive text. The response and response time shall be saved with the trial. A missing response shall not be accepted.

An identification trial shall be completed only after a valid answer and ease rating are supplied. Repeated trials shall receive distinct trial IDs and preserve the original response. Any scheduled practice trial shall be identified with `is_practice=true`; it shall not be included in the participant performance summary.

## 4. Target-hitting task procedure

### 4.1 Geometry

The target diameter shall be 15, 30, or 50 canvas pixels for Small, Medium, and Large. The requested center-to-center distance shall be 100, 250, or 400 canvas pixels for Near, Medium, and Far. The implementation shall use a documented minimum working-area size of 900 by 550 canvas pixels, or a larger area if required by the platform. It shall preserve the requested distance and keep both start point and target fully visible; it shall not silently clamp a distance or target size.

The start and target centers, actual target diameter, actual center-to-center distance, and canvas dimensions shall be recorded for each attempt. The target shall be placed in a consistent, documented direction from the start point. If direction is randomized, it shall be recorded and generated from the session's recorded random seed.

### 4.2 Trial start and timing

The participant shall move the pointer to the visible start point and press Space to begin. The application shall verify that the pointer is within the documented start-point tolerance before starting; otherwise it shall provide a clear instruction and leave the trial unstarted. This avoids moving the pointer away from the start point to click a separate Start Trial button.

Immediately before revealing the target, the application shall capture `time.perf_counter()`. The target acquisition timer shall stop on a successful click inside the target. Missed clicks shall increment `incorrect_clicks` and shall not stop or reset the timer. The participant shall then provide an ease rating.

### 4.3 Timeout, cancellation, and practice

The maximum target acquisition time shall be 30 seconds. On timeout, the attempt shall end with outcome `timed_out`; it shall not be presented as a completed trial and shall not require an ease rating. Escape shall end an active attempt with outcome `aborted`. In either case, the attempt shall be logged with its status and any applicable elapsed time; an unavailable ease rating and response shall be empty.

The target schedule shall contain three measured repetitions for each of the nine target-size-by-distance combinations (27 measured trials). The order shall be shuffled per session. The application shall provide one unscored practice trial before measured target trials. Practice shall be marked with `is_practice=true` and excluded from summaries. Identification-trial counts shall be stated in the configured protocol; each repetition shall be a separate trial.

## 5. CSV data contract

### 5.1 File and schema

The file shall be `data/performance_results.csv`, resolved relative to the application/project location rather than the process's current working directory. The application shall create the directory and file as needed, write the header once, and append records without replacing existing rows.

The following fixed columns shall be used in this order:

| Column | Meaning |
|---|---|
| `session_id` | Unique identifier for one application session |
| `random_seed` | Seed used to generate the session's shuffled target-trial order |
| `trial_id` | Unique identifier for one attempt; created once and reused for any save retry |
| `participant_id` | Anonymous participant identifier |
| `timestamp_utc` | ISO 8601 UTC timestamp at trial completion or attempt termination |
| `trial_order` | One-based order of the attempt within the session |
| `is_practice` | `true` or `false` |
| `outcome` | `completed`, `timed_out`, or `aborted` |
| `task_type` | `identification` or `target_hitting` |
| `contrast_level` | `high`, `medium`, or `low` |
| `interface_size` | `small`, `medium`, or `large` |
| `brightness` | Integer from 0 to 100 |
| `response` | Identification choice; empty for target-hitting attempts |
| `response_detail` | “Something else” description; otherwise empty |
| `response_time_seconds` | Identification response time; otherwise empty |
| `attempt_elapsed_seconds` | Elapsed time for an aborted or timed-out attempt; otherwise empty |
| `target_size` | `small`, `medium`, or `large`; empty for identification |
| `target_diameter_pixels` | Actual rendered target diameter; empty for identification |
| `target_distance` | `near`, `medium`, or `far`; empty for identification |
| `target_distance_pixels` | Actual center-to-center distance; empty for identification |
| `target_direction` | Documented direction from start point; empty for identification |
| `canvas_width_pixels` | Working-area width for target-hitting; empty for identification |
| `canvas_height_pixels` | Working-area height for target-hitting; empty for identification |
| `click_time_seconds` | Successful target acquisition time; empty if not acquired or not applicable |
| `incorrect_clicks` | Number of clicks outside the target; zero when none |
| `ease_rating` | Integer 1–5 for completed trials; empty for timed-out or aborted attempts |

Fields that do not apply shall be empty, not zero or a placeholder. A completed trial shall include all task-specific required values and an ease rating. An incomplete attempt shall have a non-completed outcome and shall never be counted as a completed trial.

### 5.2 Reliability and errors

Each attempt shall be appended immediately after it is completed and rated, or immediately after it is aborted or times out. The logger shall validate the row against the fixed schema before writing. It shall prevent duplicate rows by checking `trial_id` before retrying a save. If writing fails, the application shall clearly report the failure and retain the unsaved row for an explicit retry; it shall not display a success confirmation.

If an existing file has a different header, the application shall stop writing and explain that the file must be backed up or explicitly migrated. It shall not silently overwrite, reorder, or reinterpret existing data. File access errors, including a file locked by a spreadsheet application, shall be reported with a corrective action.

The distributed results file shall contain the header only until genuine participant trials are collected. Do not insert fabricated participant results into the experimental dataset. Example rows, if needed in documentation, shall be clearly labeled as synthetic and stored separately from the results file.

## 6. Results and analysis

The results screen shall summarize the current participant and current session only. It shall count completed, non-practice trials separately by task, and calculate averages using completed, non-practice trials only. Identification response-time averages shall use identification rows; target acquisition averages shall use successful target-hitting rows. Ease-rating averages shall use completed, rated trials only.

The screen shall distinguish “no completed trials” from an average of zero. It shall not include timed-out, aborted, or practice attempts in performance averages. Detailed results remain available in the CSV.

## 7. Acceptance criteria additions and clarifications

Add these tests to the original acceptance criteria:

| ID | Test | Expected result |
|---|---|---|
| TC25 | Reuse an existing participant ID for a new session | A warning appears; continuing creates a new `session_id` and does not merge sessions |
| TC26 | Change a visual setting during an active timed trial | The setting cannot change until the trial ends |
| TC27 | Start a target trial with the pointer outside the start tolerance | The target remains hidden and the participant receives a clear instruction |
| TC28 | Click outside the target | `incorrect_clicks` increments; the timer continues |
| TC29 | Allow a target attempt to reach 30 seconds | It ends as `timed_out`, is not counted as completed, and has no ease rating |
| TC30 | Press Escape during an active trial | It ends as `aborted`, is not counted as completed, and prior records remain |
| TC31 | Complete repeated trials | Every attempt has distinct session/trial IDs and the configured order |
| TC32 | Complete all target conditions | There are 27 measured trials plus one practice trial; each combination has three measured repetitions |
| TC33 | Resize the window or use a smaller display | The required target geometry remains visible, or the application explains how to restore a supported size |
| TC34 | Run the application with a different current working directory | Results still go to the documented project-relative CSV path |
| TC35 | Open the CSV in another application and cause a write failure | A clear error is shown; the row remains available for retry and no success is reported |
| TC36 | Start with a CSV containing an unexpected header | Writing stops with an explicit compatibility error; existing data is unchanged |
| TC37 | Open the results screen with no completed trials | A clear empty state appears; no misleading zero averages are shown |
| TC38 | Use keyboard-only navigation | All essential screens, controls, task start, ratings, and cancellation are operable |

Existing criteria TC18 and TC19 shall be interpreted as requiring misses to continue timing until a successful hit, timeout, or abort. TC20–TC21 shall require a completed-and-rated record; timeout and abort records shall be stored only with their explicit non-completed outcome.

## 8. Deliverables and report wording

The application deliverables are the Python source, generated CSV data, and README. The course/report deliverable is separate from application behavior. The report shall discuss actual collected observations and limitations; it shall not claim results before a participant study is conducted. The README shall explain the data path, CSV columns, how to start and stop trials, condition scheduling, and how incomplete attempts are represented.
