# -*- coding: utf-8 -*-

__author__ = "Brett Feltmate"

import os

import klibs
from klibs import P
from klibs.KLGraphics import KLDraw as kld
from klibs.KLGraphics import KLNumpySurface as kln
from klibs.KLGraphics import fill, flip, blit
from klibs.KLCommunication import message
from klibs.KLBoundary import BoundarySet, CircleBoundary
from klibs.KLUtilities import pump
from klibs.KLExceptions import TrialException
from klibs.KLUserInterface import any_key, ui_request, mouse_clicked, mouse_pos

from natnetclient_rough import NatNetClient  # type: ignore[import]
from OptiTracker import OptiTracker  # type: ignore[import]

from random import shuffle
from copy import deepcopy

GRAY = (128, 128, 128, 255)
WHITE = (255, 255, 255, 255)
ORANGE = (255, 165, 0, 255)

V_OFFSET = 21
H_OFFSET = 7.5
CIRC_SIZE = 3
TARGET_SIZE = CIRC_SIZE * 0.8
FIX_SIZE = 4
LINE_WIDTH = 0.2
IMAGE_WIDTH = 4  # cms

HIGH = "HIGH"
LOW = "LOW"
LEFT = "LEFT"
RIGHT = "RIGHT"
START = "START"
CENTER = "CENTER"

# NOTE: This is a GBYK task
# Implement a minimum movement speed of 0.556 m/s
# Implement a maximum movement time of 450ms (OG was 350; confirm)


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

        # init natnet client #
        # self.nnc = NatNetClient()
        # self.nnc.markers_listener = self.markers_listener
        
        # init optitracker #
        # self.ot = OptiTracker(marker_count=10)
        
        # # set up initial data directories for mocap recordings #
        # if not os.path.exists("OptiData"):
        #     os.mkdir("OptiData")
        
        # if not os.path.exists("OptiData"):
        #     os.mkdir("OptiData")
        
        # os.mkdir(f"OptiData/{P.p_id}")
        # os.mkdir(f"OptiData/{P.p_id}/testing")
        
        # if P.run_practice_blocks:
        #     os.mkdir(f"OptiData/{P.p_id}/practice")
        
        # get base unit for sizings & positionings #
        self.px_cm = P.ppi / 2.54

        # spawn basic shapes #
        self.placeholder = kld.Annulus(
            diameter=self.px_cm * CIRC_SIZE,
            thickness=self.px_cm * LINE_WIDTH,
            fill=GRAY,
        )
        self.fix = kld.FixationCross(
            size=FIX_SIZE * self.px_cm, thickness=self.px_cm * LINE_WIDTH, fill=GRAY
        )
        self.dot = kld.Annulus(
            diameter=self.px_cm * TARGET_SIZE,
            thickness=self.px_cm * LINE_WIDTH,
            fill=ORANGE,
        )

        # define necessary locations #
        self.locs = {
            START: (
                P.screen_x // 2,  # type: ignore[operator]
                P.screen_y - 3 * self.px_cm,  # type: ignore[operator]
            ),
            LEFT: (
                P.screen_x // 2 - (H_OFFSET * self.px_cm),  # type: ignore[operator]
                P.screen_y - (V_OFFSET * self.px_cm),  # type: ignore[operator]
            ),
            CENTER: (
                P.screen_x // 2,  # type: ignore[operator]
                P.screen_y - (V_OFFSET * self.px_cm),  # type: ignore[operator]
            ),
            RIGHT: (
                P.screen_x // 4 + (H_OFFSET * self.px_cm),  # type: ignore[operator]
                P.screen_y - (V_OFFSET * self.px_cm),  # type: ignore[operator]
            ),
        }

        # define boundaries #
        self.bounds = BoundarySet(
            [
                CircleBoundary(
                    label="left",
                    center=self.locs["left"],
                    radius=CIRC_SIZE * self.px_cm / 2,
                ),
                CircleBoundary(
                    label="right",
                    center=self.locs["right"],
                    radius=CIRC_SIZE * self.px_cm / 2,
                ),
                CircleBoundary(
                    label="start",
                    center=self.locs["start"],
                    radius=CIRC_SIZE * self.px_cm / 2,
                ),
            ]
        )

        # randomly associate cue images with cue types
        cue_image_names = ["bowtie", "laos", "legoman", "barbell"]
        shuffle(cue_image_names)

        self.cues = {}
        for likelihood in [HIGH, LOW]:
            self.cues[likelihood] = {}
            for laterality in [RIGHT, LEFT]:
                self.cues[likelihood][laterality] = kln.NumpySurface(
                    f"ExpAssets/Resources/image/{cue_image_names.pop()}",
                    width=IMAGE_WIDTH * self.px_cm,
                )

        # make copy of "default" list defined in _params.py
        self.trial_list = deepcopy(P.trial_list)  # type: ignore[attr-defined]

        # shuffle to randomize trial sequence
        shuffle(self.trial_list)

    def block(self):
        fill()
        message(
            "instructions go here\n\nany key to start block",
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
        self.cue_likelihood, self.cue_laterality, self.cue_valid = self.trial_list.pop()

        if self.cue_valid:
            self.target_side = LEFT if self.cue_laterality == LEFT else RIGHT
        else:
            self.target_side = LEFT if self.cue_laterality == RIGHT else LEFT

        self.evm.add_event("cue_onset", 500)
        self.evm.add_event("target_off", 1500, after="cue_onset")

        if P.development_mode:
            self.evm.add_event("target_onset", 200, after="cue_onset")

        self.draw_display()

        while True:
            q = pump(True)
            _ = ui_request(queue=q)

            if mouse_clicked(within=self.bounds.boundaries[START], queue=q):
                break

        self.draw_display(fix=True)

        # boot up nnc

    def trial(self):  # type: ignore[override]
        while self.evm.before("cue_onset"):
            q = pump(True)
            _ = ui_request(queue=q)

        self.draw_display(cue=True)

        if P.development_mode:
            while self.evm.before("target_onset"):
                q = pump(True)
                _ = ui_request(queue=q)

                if not self.bounds.within_boundary(START, p=mouse_pos()):
                    raise TrialException("Moved before target onset")

        self.draw_display(target=True)

        reached_to = None

        while reached_to is None:
            q = pump(True)
            _ = ui_request(queue=q)

        return {"block_num": P.block_number, "trial_num": P.trial_number}

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
                    self.cues[self.cue_likelihood][self.cue_laterality],
                    location=self.locs[self.cue_laterality],
                    registration=5,
                )
            if target:
                blit(self.dot, location=self.locs[self.target_side], registration=5)

        flip()

    def markers_listener(self, markers: dict) -> None:
        pass
