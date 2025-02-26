# -*- coding: utf-8 -*-

__author__ = 'Brett Feltmate'


import os
from copy import deepcopy
from random import shuffle

import klibs
from klibs import P
from klibs.KLBoundary import BoundarySet, CircleBoundary
from klibs.KLCommunication import message
from klibs.KLExceptions import TrialException
from klibs.KLGraphics import KLDraw as kld
from klibs.KLGraphics import KLNumpySurface as kln
from klibs.KLGraphics import blit, fill, flip
from klibs.KLUserInterface import any_key, mouse_clicked, mouse_pos, ui_request
from klibs.KLUtilities import pump, smart_sleep
from optitracker.Optitracker import Optitracker  # type: ignore[import]
from rich.console import Console

BLACK = (0, 0, 0, 255)
HIGH = 'HIGH'
LOW = 'LOW'
LEFT = 'LEFT'
RIGHT = 'RIGHT'
START = 'START'
CENTER = 'CENTER'


class symbolic_cues_2025(klibs.Experiment):
    def setup(self):
        """
        Size & Positions:
            - Start point = 3^2 cm, bottom-centre
            - Fixation cross = 4^2 cm, placed 21 cm above start
            - Placeholders: 3^2 cm, placed 7.5 cm to the left and right of fixation
            - Cues: images

            Image/cue mappings counter-balanced
        """
        if P.development_mode:
            self.console = Console()

        # init optitracker
        self.opti = Optitracker(marker_count=10)

        # set up initial data directories for mocap recordings
        if not os.path.exists('OptiData'):
            os.mkdir('OptiData')
            os.mkdir('OptiData/testing')
            os.mkdir(f'OptiData/testing/{P.p_id}')

        if P.run_practice_blocks:
            os.mkdir('OptiData/practice')
            os.mkdir(f'OptiData/practice/{P.p_id}')

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
        for likelihood in [HIGH, LOW]:
            self.cues[likelihood] = {}
            for laterality in [RIGHT, LEFT]:
                # load images and make presentable
                image_path = (
                    f'ExpAssets/Resources/image/{cue_image_names.pop()}.jpg'
                )
                self.cues[likelihood][laterality] = kln.NumpySurface(
                    content=image_path,
                    width=int(P.image_width * self.px_cm),  # type: ignore[attr-defined]
                )

        # make copy of "default" list defined in _params.py
        self.trial_list = deepcopy(P.trial_list)  # type: ignore[attr-defined]

        shuffle(self.trial_list)

        if P.development_mode:
            print('--------------------------------')
            print('\n\nsetup()\n\n')
            self.console.log(self.cues, self.trial_list, log_locals=True)

    def block(self):
        fill()
        message(
            'instructions go here\n\nany key to start block',
            location=P.screen_c,
            registration=5,
            blit_txt=True,
        )
        flip()

        any_key()

    def trial_prep(self):
        """
        Procedure:
            - Touch start
            - On touch, present fixation & placeholders
            - After 500 ms, cue
            - Reach begins
            - Target removed after <= 1,500 ms
                - (is this a timeout?)
        """
        self.trial_rt = None
        self.trial_mt = None
        self.trial_mt_max = None
        self.trial_selected = None

        # get params for trial
        self.cue_odds, self.cued_side, self.cue_valid = self.trial_list.pop()

        # use cue validity to set target position
        if self.cued_side == LEFT:
            self.target_side = LEFT if self.cue_valid else RIGHT
        else:
            self.target_side = RIGHT if self.cue_valid else LEFT

        # trial event timings
        self.evm.add_event(
            'cue_onset', P.cue_onset  # type: ignore[attr-defined]
        )

        if P.development_mode:
            self.evm.add_event('target_onset', 500, after='cue_onset')

        self.evm.add_event(
            'trial_timeout', P.trial_time_max, after='cue_onset'  # type: ignore[attr-defined]
        )

        # draw base display (starting position only)
        self.draw_display()

        if P.development_mode:
            print('----------------------------')
            print('\n\ntrial_prep()\n\n')
            self.console.log(
                self.cue_odds,
                self.cued_side,
                self.cue_valid,
                self.target_side,
            )

        # begin trial when user touches start
        while True:
            q = pump(True)
            _ = ui_request(queue=q)

            if mouse_clicked(within=self.bounds.boundaries[START], queue=q):
                break

        self.draw_display(fix=True)

        # boot up nnc
        self.opti.start_listening()

        # give opti 5 frames of lead time
        smart_sleep(P.query_stagger)  # type: ignore[attr-defined]

        if not self.opti.is_running:
            raise RuntimeError('Failed to start optitrack')

    def trial(self):  # type: ignore[override]

        while self.evm.before('trial_timeout'):

            # pre-cue #
            ###########
            while self.evm.before('cue_onset'):
                q = pump(True)
                _ = ui_request(queue=q)

                # admonish any movements made before cue onset
                if self.opti.velocity() > P.velocity_threshold:  # type: ignore[attr-defined]
                    self.evm.stop_clock()

                    self.draw_display(
                        msg='Please keep still until the cue appears'
                    )

                    raise TrialException('Pre-emptive movement')
            ###


            # cue #
            #######
            self.draw_display(cue=True)
            cue_on_at = self.evm.trial_time_ms
            ###


            # pre-target #
            ##############
            target_visible = False
            n_times_at_thresh = 0

            # Monitor velocity until target blit rules are satistfied
            while n_times_at_thresh < P.velocity_threshold_run:  # type: ignore[attr-defined]

                velocity = self.opti.velocity()

                if velocity >= P.velocity_threshold:  # type: ignore[attr-defined]
                    n_times_at_thresh += 1

                # HACK: stagger queries to prevent overlapping frames (this could be problematic...)
                smart_sleep(P.query_stagger)  # type: ignore[attr-defined]

            # Consider RT to be time from cue to movement onset
            self.trial_rt = self.evm.trial_time_ms - cue_on_at

            # Determine max movement time relative to RT
            self.trial_mt_max = self.evm.trial_time_ms + P.movement_time_limit  # type: ignore[attr-defined]
            ###

            # target/reach #
            ###############

            # Monitor reach progress until movement complete or timeout
            while self.evm.trial_time_ms < self.trial_mt_max:  # type: ignore[operator]

                velocity = self.opti.velocity()

                # Admoinish if participant "pulls back"
                if velocity < 0:
                    self.evm.stop_clock()
                    self.draw_display(
                        msg="Please don't pause or pull back until reach is completed"
                    )
                    raise TrialException('Early reach termination')

                # Draw target if not already visible
                if not target_visible:
                    self.draw_display(target=True)
                    target_visible = True

                # NOTE: targets are selected by making contact with a touchscreen
                cursor_pos = mouse_pos()
                which_bound = self.bounds.which_boundary(cursor_pos)

                # If target touched, log selection & mt, break out of trial loop
                if which_bound in [LEFT, RIGHT]:
                    self.trial_selected = which_bound
                    self.trial_mt = self.evm.trial_time_ms - self.trial_rt - cue_on_at  # type: ignore[operator]
                    break

            break

        if self.trial_selected is None:
            self.draw_display(msg='Movement timed out! Please try to be quicker.')
            raise TrialException('Movement timed out')


        # TODO: organize returned values
        return {'block_num': P.block_number, 'trial_num': P.trial_number}

    def trial_clean_up(self):
        # TODO: on TrialException, move opti file and log reason
        self.opti.stop_listening()

    def clean_up(self):
        self.opti.stop_listening()

    def draw_display(
        self,
        fix: bool = False,
        cue: bool = False,
        target: bool = False,
        msg: str = '',
    ) -> None:
        fill()

        blit(self.placeholder, location=self.locs[START], registration=5)

        if any([fix, cue, target]):
            blit(self.placeholder, location=self.locs[LEFT], registration=5)
            blit(self.placeholder, location=self.locs[RIGHT], registration=5)

            if fix:
                blit(self.fix, location=self.locs[CENTER], registration=5)

            if cue:
                blit(
                    self.cues[self.cue_odds][self.cued_side],
                    location=self.locs[CENTER],
                    registration=5,
                )

            if target:
                blit(
                    self.target,
                    location=self.locs[self.target_side],
                    registration=5,
                )

        else:
            if msg:
                message(
                    msg,
                    location=P.screen_c,
                    registration=5,
                    blit_txt=True,
                )

        flip()

        if msg:
            smart_sleep(1000)
