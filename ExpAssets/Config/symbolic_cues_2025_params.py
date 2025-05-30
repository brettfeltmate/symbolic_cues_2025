### Klibs Parameter overrides ###

#########################################
# Runtime Settings
#########################################
collect_demographics = True
manual_demographics_collection = False
manual_trial_generation = False
run_practice_blocks = True
multi_user = False
# in centimeters, 57cm = 1 deg of visual angle per cm of screen
view_distance = 57
allow_hidpi = True

#########################################
# Available Hardware
#########################################
eye_tracker_available = False
eye_tracking = False

#########################################
# Environment Aesthetic Defaults
#########################################
default_fill_color = (125, 125, 125, 255)
default_color = (0, 0, 0, 255)
default_font_size = 23
default_font_unit = 'px'
default_font_name = 'Hind-Medium'

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
trials_per_block = trials_per_cue * 4
conditions = ['opti', 'mouse']
default_condition = 'opti'
trials_per_practice_block = 8

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
primary_table = 'trials'
unique_identifier = 'userhash'
exclude_data_cols = ['created']
append_info_cols = ['random_seed']
datafile_ext = '.txt'
append_hostname = False

#########################################
# PROJECT-SPECIFIC VARS
#########################################

# Opti/movement params #
marker_count = 10
window_size = 3  # num frames considered when calculating velocity
rescale_by = 1000  # rescale values from m to mm
primary_axis = 'z'  # axis to consider for movement (for/back)
velocity_threshold = 20  # req vel (mm / s) to be considered in-flight
movement_time_limit = 450   # movetime bound (ms) before trial abort
early_start_boundary = 5  # cm
# Cue/exp params #
cue_types = {  # Proportion, by cue type, of in/validly cued trials
    'HIGH': {'LEFT': [0.80, 0.20], 'RIGHT': [0.20, 0.80]},
    'LOW': {'LEFT': [0.525, 0.475], 'RIGHT': [0.475, 0.525]},
}

# generate trial sequence, with 40 trials per cue
# for each cue, divy up trials such that cues' intended
# probability matches their actual probability (of cuing target)
trial_list = []

for reliability in cue_types.keys():
    for laterality in cue_types[reliability].keys():
        # first number in array represents % of correctly cued trials
        for _ in range(
            int(cue_types[reliability][laterality][0] * trials_per_cue)
        ):
            trial_list.append((reliability, laterality, True))

        # second num represents invalidly cued trials
        for _ in range(
            int(cue_types[reliability][laterality][1] * trials_per_cue)
        ):
            trial_list.append((reliability, laterality, False))

# visual params #
v_offset = 40
h_offset = 10
circ_size = 3
target_size = circ_size * 0.95
fix_size = 4
line_width = 0.2
image_width = 4  # cms

# timing params #
cue_onset = 500
trial_time_max = 1500
