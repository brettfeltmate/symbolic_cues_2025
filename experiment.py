# -*- coding: utf-8 -*-

__author__ = 'Brett Feltmate'


import os
from copy import deepcopy
from random import shuffle
import numpy as np

import klibs
from klibs import P
from klibs.KLBoundary import BoundarySet, CircleBoundary
from klibs.KLCommunication import message
from klibs.KLExceptions import TrialException
from klibs.KLGraphics import KLDraw as kld
from klibs.KLGraphics import KLNumpySurface as kln
from klibs.KLGraphics import blit, fill, flip, clear
from klibs.KLUserInterface import any_key, mouse_pos, ui_request, hide_cursor
from klibs.KLUtilities import smart_sleep
from Optitracker.optitracker.OptiTracker import Optitracker  # type: ignore[import]

# from get_key_state import get_key_state  # type: ignore[import]

BLACK = (0, 0, 0, 255)
HIGH = 'HIGH'
LOW = 'LOW'
LEFT = 'LEFT'
RIGHT = 'RIGHT'
START = 'START'
CENTER = 'CENTER'
TIMEOUT = 'timed_out'
EARLY = 'early_movement'
SLOW = 'stopped_early'


class symbolic_cues_2025(klibs.Experiment):
    def setup(self):

        # init optitracker
        self.opti = Optitracker(
            marker_count=10,
            window_size=P.window_size,  # type: ignore[attr-defined]
            rescale_by=P.rescale_by,  # type: ignore[attr-defined]
            primary_axis=P.primary_axis,  # type: ignore[attr-defined]
            use_mouse=P.condition == 'mouse',  # type: ignore[attr-defined]
            display_ppi=P.ppi,  # type: ignore[attr-defined]
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
        self.px_cm = P.ppi / 2.54

        # spawn basic stimuli
        self.placeholder = kld.Annulus(
            diameter=self.px_cm * P.circ_size,  # type: ignore[attr-defined]
            thickness=self.px_cm * P.line_width,  # type: ignore[attr-defined]
            fill=BLACK,
        )
        self.fix = kld.FixationCross(
            size=P.fix_size * self.px_cm,  # type: ignore[attr-defined]
            thickness=self.px_cm * P.line_width,  # type: ignore[attr-defined]
            fill=BLACK,
        )
        self.target = kld.Annulus(
            diameter=self.px_cm * P.target_size,  # type: ignore[attr-defined]
            thickness=self.px_cm * (P.target_size / 2),  # type: ignore[attr-defined]
            fill=BLACK,
        )

        # define necessary locations
        self.locs = {
            START: (
                P.screen_x // 2,  # type: ignore[operator]
                P.screen_y - 3 * self.px_cm,  # type: ignore[operator]
            ),
            LEFT: (
                P.screen_x // 2 - (P.h_offset * self.px_cm),  # type: ignore[operator]
                P.screen_y - (P.v_offset * self.px_cm),  # type: ignore[operator]
            ),
            CENTER: (
                P.screen_x // 2,  # type: ignore[operator]
                P.screen_y - (P.v_offset * self.px_cm),  # type: ignore[operator]
            ),
            RIGHT: (
                P.screen_x // 2 + (P.h_offset * self.px_cm),  # type: ignore[operator]
                P.screen_y - (P.v_offset * self.px_cm),  # type: ignore[operator]
            ),
        }

        # define boundary checkers
        self.bounds = BoundarySet(
            [
                CircleBoundary(
                    label=LEFT,
                    center=self.locs[LEFT],
                    radius=P.circ_size * self.px_cm / 2,  # type: ignore[attr-defined]
                ),
                CircleBoundary(
                    label=RIGHT,
                    center=self.locs[RIGHT],
                    radius=P.circ_size * self.px_cm / 2,  # type: ignore[attr-defined]
                ),
                CircleBoundary(
                    label=START,
                    center=self.locs[START],
                    radius=P.circ_size * self.px_cm / 2,  # type: ignore[attr-defined]
                ),
            ]
        )

        # randomize image names before associating with cue types
        cue_image_names = ['bowtie', 'laos', 'legoman', 'barbell']
        shuffle(cue_image_names)

        # generate cue stimuli
        self.cues = {}
        for reliability in [HIGH, LOW]:
            self.cues[reliability] = {}
            for laterality in [RIGHT, LEFT]:
                # load images and make presentable
                image_path = (
                    f'ExpAssets/Resources/image/{cue_image_names.pop()}.jpg'
                )
                self.cues[reliability][laterality] = kln.NumpySurface(
                    content=image_path,
                    width=int(P.image_width * self.px_cm),  # type: ignore[attr-defined]
                )

        # make copy of "default" list defined in _params.py
        self.trial_list = deepcopy(P.trial_list)  # type: ignore[attr-defined]

        shuffle(self.trial_list)

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

        fill()
        message(instrux[0], location=P.screen_c, registration=5, blit_txt=True)
        flip()

        any_key()

    def trial_prep(self):
        # ensure mouse isn't lingering within any monitored space
        mouse_pos(position=[0, 0])

        self.trial_rt = None
        self.trial_movement_time = None
        self.trial_movement_timeout = None
        self.trial_selected_item = None

        (  # get params for trial
            self.cue_reliability,
            self.cue_laterality,
            self.cue_validity,
        ) = self.trial_list.pop()

        # set target pos as function of cue validity
        if self.cue_laterality == LEFT:
            self.target_side = LEFT if self.cue_validity else RIGHT
        else:
            self.target_side = RIGHT if self.cue_validity else LEFT

        self.opti_path += f'_Trial_{P.trial_number}_{self.cue_reliability}_{self.cue_laterality}_{self.cue_validity}.csv'

        # trial event timings
        self.evm.add_event('cue_onset', P.cue_onset)  # type: ignore[attr-defined]

        self.evm.add_event('trial_timeout', P.trial_time_max, after='cue_onset')  # type: ignore[attr-defined]

        # Instruct user on how to start
        instrux = (
            'Tap the start (nearest) circle to begin the trial.\nThen keep still until the go-signal appears.',
        )

        self.draw_display(msg=instrux[0])

        # trial started by touching start position
        while not self.bounds.within_boundary(START, mouse_pos()):
            _ = ui_request()

        # plug into NatNet stream
        self.opti.start_listening()

        # give opti a 10 frame lead
        smart_sleep(1.0 / 120 * 10)

        # Ensure opti is listening
        if not self.opti.is_listening():
            raise RuntimeError('Failed to connect to OptiTrack system')

    def trial(self):  # type: ignore[override]
        self.draw_display(fix=True)

        hide_cursor()

        hand_pos_initial = self.opti.position()

        while self.evm.before('trial_timeout'):

            #############
            # cue phase #
            #############

            while self.evm.before('cue_onset'):
                _ = ui_request()

                hand_velocity_current = self.opti.velocity(axis='all')

                if hand_velocity_current > P.velocity_threshold:  # type: ignore[attr-defined]
                    print(
                        f'\nEarly movement detected!\nReported velocity: {hand_velocity_current:.1f} mm/s\n'
                    )
                    self.abort_trial(EARLY)

                hand_pos_current = self.opti.position()
                wavered = self.euclidean(hand_pos_initial, hand_pos_current)
                if wavered > P.early_start_boundary:  # type: ignore[attr-defined]
                    print(
                        f'\nEarly movement detected!\nReported distance from initial touch-point: {wavered} mm'
                    )
                    self.abort_trial(EARLY)

            self.draw_display(cue=True)
            cue_on_at = self.evm.trial_time_ms
            ########################

            ################
            # target phase #
            ################

            while True:
                _ = ui_request()

                hand_velocity_current = self.opti.velocity(axis='all')

                if (
                    hand_velocity_current > P.velocity_threshold  # type: ignore[attr-defined]
                ):
                    print(
                        f'Velocity threshold met:\n\tVel: {hand_velocity_current:.1f} mm/s @ {self.evm.trial_time_ms} ms'
                    )
                    break

            movement_start = self.evm.trial_time_ms
            self.trial_rt = movement_start - cue_on_at
            self.trial_movement_timeout = self.evm.trial_time_ms + P.movement_time_limit  # type: ignore[attr-defined]

            # reveal target
            self.draw_display(cue=True, target=True)
            ########################

            ##################
            # response phase #
            ##################

            # Monitor reach kinematics until movement complete or timeout
            while self.evm.trial_time_ms < self.trial_movement_timeout:
                while self.trial_selected_item is None:
                    _ = ui_request()

                    hand_velocity_current = self.opti.velocity(axis='all')

                    # Admoinish any hesitations
                    if hand_velocity_current < P.velocity_threshold:  # type: ignore[attr-defined]
                        print(
                            f'\nEarly stop detected!\nReported velocity: {hand_velocity_current:.1f} mm/s @ {self.evm.trial_time_ms} ms\n'
                        )
                        self.abort_trial(SLOW)

                    which_bound = self.bounds.which_boundary(mouse_pos())

                    # If target touched, log selection & mt, break out of trial loop
                    if which_bound in [LEFT, RIGHT]:
                        self.trial_selected_item = which_bound
                        self.trial_movement_time = (
                            self.evm.trial_time_ms - movement_start
                        )

        self.opti.stop_listening()

        if self.trial_selected_item is None:
            self.abort_trial(TIMEOUT)

        return {
            'practicing': P.practicing,
            'block_num': P.block_number,
            'trial_num': P.trial_number,
            'cue_reliability': self.cue_validity,
            'cue_laterality': self.cue_laterality,
            'cue_validity': self.cue_validity,
            'reaction_time': self.trial_rt if not None else 'NA',
            'movement_time': self.trial_movement_time if not None else 'NA',
            'touched_target': self.trial_selected_item == self.target_side
            if self.trial_selected_item is not None
            else 'NA',
        }

    def trial_clean_up(self):
        clear()
        if self.opti.is_listening():
            self.opti.stop_listening()

    def clean_up(self):
        if self.opti.is_listening():
            self.opti.stop_listening()

    def abort_trial(self, err=''):
        self.evm.stop_clock()
        if self.opti.is_listening():
            self.opti.stop_listening()

        msgs = {
            EARLY: 'Wait for go-signal before reaching!',
            SLOW: 'Do not pause whilst reaching!',
            TIMEOUT: 'Timed out! Please reach faster!',
        }

        # log abort details
        abort_info = {
            'practicing': P.practicing,
            'block_num': P.block_number,
            'trial_num': P.trial_number,
            'cue_reliability': self.cue_validity,
            'cue_laterality': self.cue_laterality,
            'cue_validity': self.cue_validity,
            'reaction_time': self.trial_rt if not None else 'NA',
            'movement_time': self.trial_movement_time if not None else 'NA',
            'touched_target': self.trial_selected_item == self.target_side
            if self.trial_selected_item is not None
            else 'NA',
            'reason': err,
            'recycled': err == EARLY,  # only recycle early-starts
        }

        self.db.insert(data=abort_info, table='aborts')  # type: ignore

        fill()
        message(msgs[err], location=P.screen_c, registration=5, blit_txt=True)
        flip()

        smart_sleep(1000)

        # if pre-go-signal, reshuffle trial into deck
        if err == EARLY:
            os.remove(self.opti_path)

            self.trial_list.append(
                (self.cue_reliability, self.cue_laterality, self.cue_validity)
            )
            shuffle(self.trial_list)

            raise TrialException(err)

    def draw_display(
        self,
        fix: bool = False,
        cue: bool = False,
        target: bool = False,
        msg: str = '',
    ) -> None:
        fill()

        blit(self.placeholder, location=self.locs[LEFT], registration=5)
        blit(self.placeholder, location=self.locs[RIGHT], registration=5)
        blit(self.placeholder, location=self.locs[START], registration=5)

        if msg:
            message(msg, location=P.screen_c, registration=5, blit_txt=True)

        if fix:
            blit(self.fix, location=self.locs[CENTER], registration=5)

        if cue:
            blit(
                self.cues[self.cue_reliability][self.cue_laterality],
                location=self.locs[CENTER],
                registration=5,
            )

        if target:
            blit(
                self.target,
                location=self.locs[self.target_side],
                registration=5,
            )

        flip()

    def euclidean(self, p0: np.ndarray, p1: np.ndarray) -> int:

        """
        Calculate the Euclidean distance between two points.
        Args:
            p0 (np.ndarray): Tuple of xyz coordinates denoting starting point.
            p1 (np.ndarray): Tuple of xyz coordinates denoting ending point.
        Returns:
            int: The Euclidean distance between the two points, truncated to an integer.
        """

        return int(np.linalg.norm(p0 - p1))
