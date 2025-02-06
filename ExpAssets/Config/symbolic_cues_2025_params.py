### Klibs Parameter overrides ###

#########################################
# Runtime Settings
#########################################
collect_demographics = True
manual_demographics_collection = False
manual_trial_generation = False
run_practice_blocks = True
multi_user = False
view_distance = 57  # in centimeters, 57cm = 1 deg of visual angle per cm of screen
allow_hidpi = True

#########################################
# Available Hardware
#########################################
eye_tracker_available = False
eye_tracking = False

#########################################
# Environment Aesthetic Defaults
#########################################
default_fill_color = (45, 45, 45, 255)
default_color = (255, 255, 255, 255)
default_font_size = 23
default_font_unit = "px"
default_font_name = "Hind-Medium"

#########################################
# EyeLink Settings
#########################################
manual_eyelink_setup = False
manual_eyelink_recording = False

saccadic_velocity_threshold = 20
saccadic_acceleration_threshold = 5000
saccadic_motion_threshold = 0.15

#########################################
# Experiment Structure
#########################################
multi_session_project = False
blocks_per_experiment = 1
trials_per_cue = 40
trials_per_block = 40 * 4
conditions = []
default_condition = None

#########################################
# Development Mode Settings
#########################################
dm_auto_threshold = True
dm_trial_show_mouse = True
dm_ignore_local_overrides = False
dm_show_gaze_dot = True

#########################################
# Data Export Settings
#########################################
primary_table = "trials"
unique_identifier = "userhash"
exclude_data_cols = ["created"]
append_info_cols = ["random_seed"]
datafile_ext = ".txt"
append_hostname = False

#########################################
# PROJECT-SPECIFIC VARS
#########################################
cue_ratios = {
    "HIGH": {"LEFT": [0.80, 0.20], "RIGHT": [0.20, 0.80]},
    "LOW": {"LEFT": [0.525, 0.475], "RIGHT": [0.475, 0.525]},
}

trial_list = []

for likelihood in cue_ratios.keys():
    for laterality in cue_ratios[likelihood].keys():
        for _ in range(int(cue_ratios[likelihood][laterality][0] * trials_per_cue)):
            trial_list.append(
                {"likelihood": likelihood, "laterality": laterality, "valid": True}
            )

        for _ in range(int(cue_ratios[likelihood][laterality][1] * trials_per_cue)):
            trial_list.append(
                {"likelihood": likelihood, "laterality": laterality, "valid": False}
            )
