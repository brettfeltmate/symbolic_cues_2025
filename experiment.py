# -*- coding: utf-8 -*-

__author__ = 'Brett Feltmate'


import os
from copy import deepcopy
from random import shuffle, sample

import klibs
from klibs import P
from klibs.KLBoundary import BoundarySet, CircleBoundary
from klibs.KLCommunication import message
from klibs.KLGraphics import KLDraw as kld
from klibs.KLGraphics import KLNumpySurface as kln
from klibs.KLGraphics import blit, fill, flip, clear
from klibs.KLUserInterface import any_key, mouse_pos, ui_request, get_clicks
from klibs.KLUtilities import smart_sleep, pump

from klibs.KLExceptions import TrialException

from Optitracker.optitracker.OptiTracker import Optitracker  # type: ignore

BLACK = (0, 0, 0, 255)
ORANGE = (255, 165, 0, 255)
HIGH = 'HIGH'
LOW = 'LOW'
LEFT = 'LEFT'
RIGHT = 'RIGHT'
START = 'START'
CENTER = 'CENTER'
EARLY_START = 'early_start'
EARLY_STOP = 'early_stop'
MOVEMENT_TIMEOUT = 'movement_timeout'


class symbolic_cues_2025(klibs.Experiment):
    def setup(self):

        self.err_msgs = {
            EARLY_START: 'Wait for go-signal before reaching!',
            MOVEMENT_TIMEOUT: 'Timed out! Please move faster!',
            EARLY_STOP: 'Do not pause whilst reaching!',
        }

        # init optitracker
        self.opti = Optitracker(
            marker_count=10,
            window_size=P.window_size,  # type: ignore
            rescale_by=P.rescale_by,  # type: ignore
            primary_axis=P.primary_axis,  # type: ignore
            use_mouse=P.condition == 'mouse',  # type: ignore
            display_ppi=int(P.ppi),  # type: ignore
        )

        if not os.path.exists('OptiData'):
            os.mkdir('OptiData')

        self.opti_path = f'OptiData/{P.p_id}'

        if os.path.exists(self.opti_path):
            raise RuntimeError(
                f'Participant ID {P.p_id} already exists!\nYou likely ran `klibs hard-reset`, but did not re/move existing optidata.'
            )

        os.mkdir(self.opti_path)

        # get base unit for sizings & positionings
        self.px_cm = P.ppi // 2.54

        # spawn basic stimuli
        self.placeholder = kld.Annulus(
            diameter=self.px_cm * P.circ_size,  # type: ignore
            thickness=self.px_cm * P.line_width,  # type: ignore
            fill=BLACK,
        )
        self.fix = kld.FixationCross(
            size=P.fix_size * self.px_cm,  # type: ignore
            thickness=self.px_cm * P.line_width,  # type: ignore
            fill=BLACK,
        )
        self.target = kld.Annulus(
            diameter=self.px_cm * P.target_size,  # type: ignore
            thickness=self.px_cm * (P.target_size / 2),  # type: ignore
            fill=BLACK,
        )

        # define necessary locations
        self.locs = {
            START: (
                P.screen_x // 2,  # type: ignore
                P.screen_y - 3 * self.px_cm,  # type: ignore
            ),
            LEFT: (
                P.screen_x // 2 - (P.h_offset * self.px_cm),  # type: ignore
                P.screen_y - (P.v_offset * self.px_cm),  # type: ignore
            ),
            CENTER: (
                P.screen_x // 2,  # type: ignore
                P.screen_y - (P.v_offset * self.px_cm),  # type: ignore
            ),
            RIGHT: (
                P.screen_x // 2 + (P.h_offset * self.px_cm),  # type: ignore
                P.screen_y - (P.v_offset * self.px_cm),  # type: ignore
            ),
        }

        # define boundary checkers
        self.bounds = BoundarySet(
            [
                CircleBoundary(
                    label=LEFT,
                    center=self.locs[LEFT],
                    radius=P.circ_size * self.px_cm / 2,  # type: ignore
                ),
                CircleBoundary(
                    label=RIGHT,
                    center=self.locs[RIGHT],
                    radius=P.circ_size * self.px_cm / 2,  # type: ignore
                ),
                CircleBoundary(
                    label=START,
                    center=self.locs[START],
                    radius=P.circ_size * self.px_cm / 2,  # type: ignore
                ),
            ]
        )

        if P.development_mode:
            self.cursor = kld.Annulus(
                diameter=P.circ_size * self.px_cm,  # type: ignore
                thickness=P.line_width * self.px_cm,  # type: ignore
                fill=ORANGE,
            )

        # randomize image names before associating with cue types
        cue_image_names = ['bowtie', 'laos', 'legoman', 'barbell']
        shuffle(cue_image_names)

        # generate cue stimuli
        self.cue = {}
        for reliability in [HIGH, LOW]:
            self.cue[reliability] = {}
            for laterality in [RIGHT, LEFT]:
                # load images and make presentable
                image_path = (
                    f'ExpAssets/Resources/image/{cue_image_names.pop()}.jpg'
                )
                self.cue[reliability][laterality] = kln.NumpySurface(
                    content=image_path,
                    width=int(P.image_width * self.px_cm),  # type: ignore
                )

        # make copy of "default" list defined in _params.py
        self.trial_list = deepcopy(P.trial_list)  # type: ignore

        shuffle(self.trial_list)
        
        if P.run_practice_blocks:
            self.practice_trial_list = sample(self.trial_list, P.practice_trials_per_block)  # type: ignore[attr-defined]

    def block(self):
        self.opti_path += f'/Block_{P.block_number}'
        fill()
        instrux = (
            'Task Instructions:\n\n'
            'Your task is to reach out and tap on a target circle quickly and accurately.\n'
            '\tNOTE: the target will not appear until AFTER you start your reach.\n\n'
            'In each trial, you will first see three (unfilled) circles, and a crosshair.\n'
            'To start a trial, tap the start (nearest) circle with your finger.\n'
            'Then, WAIT until the go-signal (image) replaces the crosshair.\n'
            '\tNOTE: Moving prior to the go-signal will terminate the trial.\n\n'
            'When you see the signal, start reaching towards the far circles.\n'
            "Once you start reaching, one of them will 'fill-in'. That is your target.\n"
            '\tNOTE: Once your reach is in motion, you cannot stop or otherwise hesitate.\n\n'
            'When you are ready, press any key to start the experiment.'
        )

        if P.practicing:
            instrux += '\n\n(PRACTICE ROUND)'

        fill()
        message(instrux, location=P.screen_c, registration=5, blit_txt=True)
        flip()

        any_key()

    def trial_prep(self):
        # ensure mouse isn't lingering within any monitored space
        mouse_pos(position=[0, 0])

        (  # get params for trial
            self.cue_reliability,
            self.cue_laterality,
            self.cue_validity,
        ) = self.trial_list.pop() if not P.practicing else self.practice_trial_list.pop()

        # set target pos as function of cue validity
        if self.cue_laterality == LEFT:
            self.target_side = LEFT if self.cue_validity else RIGHT
        else:
            self.target_side = RIGHT if self.cue_validity else LEFT

        self.trial_path = self.opti_path
        self.trial_path += f'_Trial_{P.trial_number}_{self.cue_reliability}_{self.cue_laterality}_{self.cue_validity}.csv'

        self.opti.data_dir = self.trial_path

        self.draw_display(phase='pre_cue')

        # trial started by touching start position
        at_start = False
        _ = pump()
        while not at_start:
            if not self.opti.is_listening():
                self.opti.start_listening()
            q = pump()
            ui_request(queue = q)
            lift_offs = get_clicks(released = True)
            if lift_offs:
                # if mouse is at start position, set at_start to True
                if self.bounds.within_boundary(START, lift_offs[0]):
                    at_start = True

        # plug into NatNet stream
        # self.opti.start_listening()

        # give opti a 10 frame lead
        # smart_sleep(1e3 / 120 * 10)

        # Ensure opti is listening
        if not self.opti.is_listening():
            raise RuntimeError('Failed to connect to OptiTrack system')

    def trial(self):  # type: ignore[override]
        # control flags
        bad_behaviour = False
        trial_time_limit = None
        trial_phase = 'pre_cue'

        # ancilliary values
        movement_start = None

        # returned value
        item_touched = None
        reaction_time = None
        movement_time = None

        # Proceed through trial until successful or erroneous behaviour
        while not bad_behaviour and item_touched is None:

            _ = ui_request()

            # draw display for current phase
            self.draw_display(phase=trial_phase)

            # state variables
            cursor = mouse_pos()
            t_now = self.evm.trial_time_ms
            velocity = self.opti.velocity(axis='all')

            if P.development_mode:
                print(f"\n\t   Trial: {P.trial_number}")
                print(f"\n\t   Phase: {trial_phase}")
                print(f"\n\tPosition: {cursor}")
                print(f"\n\t    Time: {int(t_now)} ms")
                print(f"\n\tVelocity: {int(velocity)} px/s")
                print(f"\n\t   Error: {bad_behaviour}")
            #
            # Determine what should happen on next redraw
            #

            # Prior to go-signal: abort if moving
            if trial_phase == 'pre_cue':
                if velocity >= P.velocity_threshold:  # type: ignore
                    bad_behaviour = EARLY_START
                else:
                    if t_now >= P.cue_onset:  # type: ignore
                        trial_phase = 'pre_target'
                        cue_on_at = t_now

            # Following go-signal, reveal target on movement start
            elif trial_phase == 'pre_target':
                if velocity >= P.velocity_threshold:  # type: ignore
                    trial_phase = 'responding'
                    # log start time
                    movement_start = t_now
                    reaction_time = movement_start - cue_on_at  # type: ignore
                    # calculate timelimit
                    trial_time_limit = movement_start + P.movement_time_limit  # type: ignore

            # Abort if pauses made during reaching, otherwise log which/when item touched
            elif trial_phase == 'responding':

                if velocity <= P.velocity_threshold:  # type: ignore
                    bad_behaviour = EARLY_STOP

                if t_now >= trial_time_limit:  # type: ignore
                    bad_behaviour = MOVEMENT_TIMEOUT

                if not bad_behaviour:
                    which_bound = self.bounds.which_boundary(cursor)
                    if which_bound in [LEFT, RIGHT]:
                        item_touched = which_bound
                        movement_time = t_now - movement_start  # type: ignore

        if bad_behaviour:

            fill()

            message(
                self.err_msgs[bad_behaviour],
                location=P.screen_c,
                registration=5,
                blit_txt=True,
            )

            flip()

            smart_sleep(1000)

            abort_info = {
                'participant_id': P.p_id,
                'practicing': P.practicing,
                'block_num': P.block_number,
                'trial_num': P.trial_number,
                'cue_reliability': self.cue_validity,
                'cue_laterality': self.cue_laterality,
                'cue_validity': self.cue_validity,
                'reaction_time': reaction_time if not None else 'NA',
                'movement_time': movement_time if not None else 'NA',
                'touched_target': item_touched == self.target_side
                if item_touched is not None
                else 'NA',
                'reason': bad_behaviour,
                'recycled': bad_behaviour
                == EARLY_START,  # only recycle early-starts
            }

            self.db.insert(data=abort_info, table='aborts')  # type: ignore

            # for early starts, toss opti data and recycle trial
            if bad_behaviour == EARLY_START:
                # Ensure OptiTracker has stopped listening before removing the file
                if self.opti.is_listening():
                    self.opti.stop_listening()

                # Sometimes this is called whilst file is being written
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        if os.path.exists(self.opti.data_dir):
                            os.remove(self.opti.data_dir)
                        break  # Successfully removed or file doesn't exist
                    except (PermissionError, OSError) as e:
                        if attempt == max_attempts - 1:  # Last attempt
                            print(f"Warning: Could not remove file {self.opti.data_dir}: {e}")
                        else:
                            smart_sleep(50)  # Give writer time to finish

                self.trial_list.append(
                    (
                        self.cue_reliability,
                        self.cue_laterality,
                        self.cue_validity,
                    )
                )
                shuffle(self.trial_list)

                raise TrialException(bad_behaviour)

        return {
            'practicing': P.practicing,
            'block_num': P.block_number,
            'trial_num': P.trial_number,
            'cue_reliability': self.cue_validity,
            'cue_laterality': self.cue_laterality,
            'cue_validity': self.cue_validity,
            'reaction_time': reaction_time if not None else 'NA',
            'movement_time': movement_time if not None else 'NA',
            'touched_target': item_touched == self.target_side
            if item_touched is not None
            else 'NA',
        }

    def trial_clean_up(self):
        mouse_pos(position=[0, 0])
        clear()
        if self.opti.is_listening():
            self.opti.stop_listening()

    def clean_up(self):
        pass

    def draw_display(self, phase: str, msg: str = '') -> None:
        fill()

        blit(self.placeholder, location=self.locs[LEFT], registration=5)
        blit(self.placeholder, location=self.locs[RIGHT], registration=5)
        blit(self.placeholder, location=self.locs[START], registration=5)

        # if msg:
        #     message(msg, location=P.screen_c, registration=5, blit_txt=True)

        if phase == 'pre_cue':
            blit(self.fix, location=self.locs[CENTER], registration=5)

        elif phase == 'pre_target':
            blit(self.fix, location=self.locs[CENTER], registration=5)
            blit(
                self.cue[self.cue_reliability][self.cue_laterality],
                location=self.locs[CENTER],
                registration=5,
            )

        if phase == 'responding':
            blit(
                self.cue[self.cue_reliability][self.cue_laterality],
                location=self.locs[CENTER],
                registration=5,
            )
            blit(
                self.target,
                location=self.locs[self.target_side],
                registration=5,
            )

        # draw cursor when debugging
        if P.development_mode:
            blit(self.cursor, location=mouse_pos(), registration=5)

        flip()
