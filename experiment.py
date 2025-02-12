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
from klibs.KLUtilities import pump
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
        # get params for trial
        self.cue_odds, self.cued_side, self.cue_valid = self.trial_list.pop()

        # use cue validity to set target position
        if self.cued_side == LEFT:
            self.target_side = LEFT if self.cue_valid else RIGHT
        else:
            self.target_side = RIGHT if self.cue_valid else LEFT

        # trial event timings
        self.evm.add_event('cue_onset', 1500)
        self.evm.add_event('target_off', 1500, after='cue_onset')

        if P.development_mode:
            self.evm.add_event('target_onset', 500, after='cue_onset')

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
                log_locals=True,
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

        if not self.opti.is_running:
            raise RuntimeError('Failed to start optitrack')

    def trial(self):  # type: ignore[override]
        # do nothing for now
        while self.evm.before('cue_onset'):
            # but also don't lock up computer
            q = pump(True)
            _ = ui_request(queue=q)

        self.draw_display(cue=True)

        if P.development_mode:
            while self.evm.before('target_onset'):
                q = pump(True)
                _ = ui_request(queue=q)

                if not self.bounds.within_boundary(START, p=mouse_pos()):
                    raise TrialException('Moved before target onset')

        self.draw_display(target=True)

        # reached_to = None

        # while reached_to is None:
        any_key()

        return {'block_num': P.block_number, 'trial_num': P.trial_number}

    def trial_clean_up(self):
        pass

    def clean_up(self):
        pass

    def draw_display(
        self, fix: bool = False, cue: bool = False, target: bool = False
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

        flip()
