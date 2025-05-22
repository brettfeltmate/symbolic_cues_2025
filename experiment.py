# -*- coding: utf-8 -*-

__author__ = 'Brett Feltmate'


import os
from copy import deepcopy
from random import shuffle, sample


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
    key_pressed,
    mouse_pos,
    ui_request,
    show_cursor,
    hide_cursor,
)
from klibs.KLUtilities import pump, smart_sleep
from Optitracker.optitracker.OptiTracker import Optitracker  # type: ignore[import]
from get_key_state import get_key_state  # type: ignore[import]

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

        self.data_dir = 'OptiData'

        if P.condition != 'mouse':
            # set up initial data directories for mocap recordings
            if not os.path.exists('OptiData'):
                os.mkdir('OptiData')

            if not os.path.exists('OptiData/testing'):
                os.mkdir('OptiData/testing')

            os.mkdir(f'OptiData/testing/{P.p_id}')

            os.mkdir(f'OptiData/aborted/{P.p_id}')

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

        if P.run_practice_blocks:
            self.practice_trials = sample(self.trial_list, P.trials_per_practice_block)  # type: ignore[attr-defined]

    def block(self):
        if P.practicing:
            self.block_dir = (
                f'OptiData/practice/{P.p_id}/Block_{P.block_number}'
            )
            if not os.path.exists(self.block_dir):
                os.mkdir(self.block_dir)

        else:
            self.block_dir = (
                f'OptiData/testing/{P.p_id}/Block_{P.block_number}'
            )
            if not os.path.exists(self.block_dir):
                os.mkdir(self.block_dir)

        fill()

        block_msg = (
            'Tap enter to start the block.'
            '\n'
            'To start each trial, press and HOLD space until the cue appears.'
        )

        if P.practicing:
            block_msg += '\n\n(This is a practice block.)'

        message(
            block_msg,
            location=P.screen_c,
            registration=5,
            blit_txt=True,
        )
        flip()

        any_key()

    def trial_prep(self):
        self.opti.data_dir = self.block_dir + f'/Trial_{P.trial_number}.csv'

        self.trial_rt = None
        self.trial_mt = None
        self.trial_mt_max = None
        self.trial_selected = None

        (  # get params for trial
            self.cue_reliability,
            self.cue_laterality,
            self.cue_validity,
        ) = (
            self.trial_list.pop()
            if not P.practicing
            else self.practice_trials.pop()
        )

        # set target pos as function of cue validity
        if self.cue_laterality == LEFT:
            self.target_side = LEFT if self.cue_validity else RIGHT
        else:
            self.target_side = RIGHT if self.cue_validity else LEFT

        # trial event timings
        self.evm.add_event('cue_onset', P.cue_onset)  # type: ignore[attr-defined]

        self.evm.add_event('trial_timeout', P.trial_time_max, after='cue_onset')  # type: ignore[attr-defined]

        # Remind user how to start trials
        fill()
        message(
            'Press and HOLD space until the cue appears.',
            location=P.screen_c,
            registration=5,
            blit_txt=True,
        )
        flip()

        # trial started by touching start position
        while True:
            q = pump(True)
            if key_pressed(key='space', queue=q):
                break

        self.draw_display(fix=True)

        # plug into NatNet stream
        self.opti.start_listening()

        # give opti a few frames of lead time
        smart_sleep((self.opti.sample_rate * 3) // 1000)

        # Ensure opti is listening
        if not self.opti.is_listening():
            raise RuntimeError('Failed to connect to OptiTrack system')

    def trial(self):  # type: ignore[override]

        show_cursor() if P.condition == 'mouse' else hide_cursor()

        while self.evm.before('trial_timeout') and self.trial_mt is None:

            #############
            # cue phase #
            #############

            while self.evm.before('cue_onset'):
                _ = ui_request()
                if get_key_state('space') == 0:
                    self.abort_trial(EARLY)

            self.draw_display(cue=True)
            cue_on_at = self.evm.trial_time_ms

            while get_key_state('space') == 1:
                _ = ui_request()

            self.trial_rt = self.evm.trial_time_ms - cue_on_at
            self.trial_mt_max = self.evm.trial_time_ms + P.movement_time_limit  # type: ignore[attr-defined]
            ########################

            ################
            # target phase #
            ################

            # Hang tight until velocity threshold is met
            while self.opti.velocity() < P.velocity_threshold:  # type: ignore[attr-defined]
                _ = ui_request()

            # draw target
            self.draw_display(target=True)
            ########################

            ##################
            # response phase #
            ##################

            # Monitor reach kinematics until movement complete or timeout
            while self.trial_mt is None and (
                self.evm.trial_time_ms < self.trial_mt_max
            ):
                _ = ui_request()

                # Admoinish any hesitations
                if self.opti.velocity() < P.velocity_threshold:  # type: ignore
                    self.abort_trial(SLOW)

                which_bound = self.bounds.which_boundary(mouse_pos())

                # If target touched, log selection & mt, break out of trial loop
                if which_bound in [LEFT, RIGHT]:
                    self.trial_selected = which_bound
                    self.trial_mt = self.evm.trial_time_ms - self.trial_rt - cue_on_at  # type: ignore[operator]

        self.opti.stop_listening()

        if self.trial_selected is None:
            self.abort_trial(TIMEOUT)

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
        if self.opti.is_listening():
            self.opti.stop_listening()

        if os.path.exists(self.opti.data_dir):
            with open(self.opti.data_dir, 'r') as f:
                data = f.read()

            markup = (
                f'# Participant ID: {P.p_id}',
                f'# Block {P.block_number}',
                f'# Trial {P.trial_number}',
                f'# Cue reliability: {self.cue_reliability}',
                f'# Cue laterality: {self.cue_laterality}',
                f'# Cue validity: {self.cue_validity}',
                f'# Target side: {self.target_side}',
            )

            with open(self.opti.data_dir, 'w') as f:
                f.write('\n'.join(markup) + '\n' + data)

    def clean_up(self):
        if self.opti.is_listening():
            self.opti.stop_listening()

    def abort_trial(self, err=''):
        msgs = {
            EARLY: "Please don't release space until the cue appears",
            SLOW: "Please don't pause or pull back until reach is completed",
            TIMEOUT: 'Timed out! Please try to be quicker.',
        }
        self.evm.stop_clock()
        if self.opti.is_listening():
            self.opti.stop_listening()

        # move data file to aborted folder then cleanup original
        move_to = f'OptiData/aborted/{P.p_id}/Trial_{P.trial_number}_Block_{P.block_number}'
        move_to += '_practice.csv' if P.practicing else '.csv'
        os.rename(self.opti.data_dir, move_to)
        os.remove(self.opti.data_dir)

        # log reason for aborting
        abort_info = {
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
            'abort_reason': err,
        }

        self.db.insert(data=abort_info, table='aborted_trials')  # type: ignore

        if P.practicing:
            self.practice_trials.append(
                (self.cue_reliability, self.cue_laterality, self.cue_validity)
            )
            shuffle(self.practice_trials)
        else:
            self.trial_list.append(
                (self.cue_reliability, self.cue_laterality, self.cue_validity)
            )
            shuffle(self.trial_list)

        fill()
        message(msgs[err], location=P.screen_c, registration=5, blit_txt=True)
        flip()

        smart_sleep(1000)

        raise TrialException(err)

    def draw_display(
        self,
        fix: bool = False,
        cue: bool = False,
        target: bool = False,
        msg: str = '',
    ) -> None:
        fill()

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
