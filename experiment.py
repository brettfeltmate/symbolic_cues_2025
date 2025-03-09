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
from klibs.KLUserInterface import (
    any_key,
    mouse_pos,
    ui_request,
    show_cursor,
    hide_cursor,
)
from klibs.KLUtilities import pump,smart_sleep
from Optitracker.optitracker.OptiTracker import Optitracker  # type: ignore[import]
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
        if P.development_mode:
            self.console = Console()

        # init optitracker
        self.opti = Optitracker(
            marker_count=10,
            window_size=P.window_size,  # type: ignore[attr-defined]
            rescale_by=P.rescale_by,  # type: ignore[attr-defined]
            primary_axis=P.primary_axis,  # type: ignore[attr-defined]
            use_mouse=P.condition == 'mouse',  # type: ignore[attr-defined]
            display_ppi=P.ppi,  # type: ignore[attr-defined]
        )

        self.data_dir = "OptiData"

        if P.condition != 'mouse':
            # set up initial data directories for mocap recordings
            if not os.path.exists('OptiData'):
                os.mkdir('OptiData')

            if not os.path.exists('OptiData/testing'):
                os.mkdir('OptiData/testing')

            os.mkdir(f'OptiData/testing/{P.p_id}')

            if P.run_practice_blocks:
                if not os.path.exists('OptiData/practice'):
                    os.mkdir('OptiData/practice')
                os.mkdir(f'OptiData/practice/{P.p_id}')

        else:
            P.movement_time_limit = 1000  # type: ignore[attr-defined]

        # if P.development_mode:
        if os.path.exists('OptiData/velocity_log.txt'):
            os.remove('OptiData/velocity_log.txt')

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
        if P.practicing:
            self.block_dir = f'OptiData/practice/{P.p_id}/Block_{P.block_number}'
            if not os.path.exists(self.block_dir):
                os.mkdir(self.block_dir)

        else:
            self.block_dir = f'OptiData/testing/{P.p_id}/Block_{P.block_number}'
            if not os.path.exists(self.block_dir):
                os.mkdir(self.block_dir)

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
        self.opti.data_dir = self.block_dir + f'/Trial_{P.trial_number}.csv'

        # superstitiously ensure mouse does not start within any boundaries
        mouse_pos(position=P.screen_c)

        self.trial_rt = None
        self.trial_mt = None
        self.trial_mt_max = None
        self.trial_selected = None

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

        # trial event timings
        self.evm.add_event('cue_onset', P.cue_onset)  # type: ignore[attr-defined]

        self.evm.add_event('trial_timeout', P.trial_time_max, after='cue_onset')  # type: ignore[attr-defined]

        # draw base display (starting position only)
        self.draw_display()

        if P.development_mode:
            self.console.log(
                self.cue_reliability,
                self.cue_laterality,
                self.cue_validity,
                self.target_side,
            )

        # trial started by touching start position
        while not self.bounds.which_boundary(mouse_pos()) == START:
            q = pump(True)
            _ = ui_request(queue=q)

        self.draw_display(fix=True)

        # plug into NatNet stream
        self.opti.start_listening()

        # give opti 5 frames of lead time
        smart_sleep(P.query_stagger)  # type: ignore[attr-defined]

        # Ensure opti is listening
        if not self.opti.is_listening() and not P.development_mode:
            raise RuntimeError('Failed to connect to OptiTrack system')

    def trial(self):  # type: ignore[override]

        if P.condition == 'mouse':
            show_cursor()
        else:
            hide_cursor()

        while self.evm.before('trial_timeout'):

            #############
            # cue phase #
            #############

            while self.evm.before('cue_onset'):
                q = pump(True)
                _ = ui_request(queue=q)

                velocity = self.opti.velocity()

                print(int(velocity))

                # admonish any sizable pre-cue movement
                if velocity > P.velocity_threshold:  # type: ignore[attr-defined]
                    self.opti.stop_listening()
                    self.evm.stop_clock()

                    self.draw_display(
                        msg='Please keep still until the cue appears'
                    )

                    raise TrialException('Pre-emptive movement')

            self.draw_display(cue=True)
            cue_on_at = self.evm.trial_time_ms
            ########################

            ################
            # target phase #
            ################

            n_times_at_thresh = 0

            # Trigger target onset if-and-only-if velocity criteria are met
            while n_times_at_thresh < P.velocity_threshold_run:  # type: ignore[attr-defined]

                velocity = self.opti.velocity()

                # self.draw_display(cue=True, msg = f"{int(velocity)}")

                # if P.development_mode:
                # with open('OptiData/velocity_log.txt', 'a') as f:
                #     f.write(str(velocity) + '\n')

                if velocity >= P.velocity_threshold:  # type: ignore[attr-defined]
                    n_times_at_thresh += 1

                # HACK: stagger queries to prevent overlapping frames (this could be problematic...)
                # smart_sleep(P.query_stagger)  # type: ignore[attr-defined]

            # rt = delay between cue onset and meeting movement criteria
            self.trial_rt = self.evm.trial_time_ms - cue_on_at

            # max mt = rt + movement_time_limit
            self.trial_mt_max = self.evm.trial_time_ms + P.movement_time_limit  # type: ignore[attr-defined]

            # draw target
            self.draw_display(target=True)
            ########################

            ##################
            # response phase #
            ##################

            # Monitor reach kinematics until movement complete or timeout
            times_below_thresh = 0
            while self.evm.trial_time_ms < self.trial_mt_max:  # type: ignore[operator]

                velocity = self.opti.velocity()

                # self.draw_display(target=True, msg = f"{int(velocity)}")

                # Admoinish any hesitations
                if (
                    velocity < P.velocity_threshold  # type: ignore[attr-defined]
                ):
                    times_below_thresh += 1
                    if times_below_thresh == P.velocity_threshold_run:  # type: ignore[attr-defined]
                        self.opti.stop_listening()
                        self.evm.stop_clock()

                        self.draw_display(
                            msg="Please don't pause or pull back until reach is completed"
                        )

                        raise TrialException('Early reach termination')

                #smart_sleep(P.query_stagger)  # type: ignore[attr-defined]

                # NOTE: targets are selected via touchscreen
                which_bound = self.bounds.which_boundary(mouse_pos())

                # If target touched, log selection & mt, break out of trial loop
                if which_bound in [LEFT, RIGHT]:
                    self.trial_selected = which_bound
                    self.trial_mt = self.evm.trial_time_ms - self.trial_rt - cue_on_at  # type: ignore[operator]
                    break
            break

        self.opti.stop_listening()

        if self.trial_selected is None:
            self.draw_display(
                msg='Movement timed out! Please try to be quicker.'
            )
            raise TrialException('Movement timed out')

        # TODO: organize returned values
        return {
            'practicing': P.practicing,
            'block_num': P.block_number,
            'trial_num': P.trial_number,
            'cue_reliability': self.cue_validity,
            'cue_laterality': self.cue_laterality,
            'cue_validity': self.cue_validity,
            'reaction_time': self.trial_rt if not None else 'NA',
            'movement_time': self.trial_mt if not None else 'NA',
            'touched_target': self.trial_selected == self.target_side
            if self.trial_selected is not None
            else 'NA',
        }

    def trial_clean_up(self):
        # TODO: on TrialException, move opti file and log reason
        if self.opti.is_listening():
            self.opti.stop_listening()

    def clean_up(self):
        if self.opti.is_listening():
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

        else:
            if msg:
                message(
                    msg,
                    location=[0, 0],
                    registration=7,
                    blit_txt=True,
                )

        flip()

        if msg:
            smart_sleep(1000)
