# -*- coding: utf-8 -*-

__author__ = "Brett Feltmate"

import os

import klibs
from klibs import P
from klibs.KLGraphics import KLDraw as kld
from klibs.KLGraphics import KLNumpySurface as kln
from klibs.KLGraphics import fill, flip
from klibs.KLUserInterface import any_key
from klibs.KLCommunication import message
from klibs.KLBoundary import BoundarySet, CircleBoundary

from natnetclient_rough import NatNetClient  # type: ignore[import]
from OptiTracker import OptiTracker  # type: ignore[import]

from random import shuffle
from copy import deepcopy

GRAY = (128, 128, 128, 255)
WHITE = (255, 255, 255, 255)

V_OFFSET = 21
H_OFFSET = 7.5
CIRC_SIZE = 3
FIX_SIZE = 4
LINE_WIDTH = 0.2
IMAGE_WIDTH = 4  # cms

HIGH = "HIGH"
LOW = "LOW"
LEFT = "LEFT"
RIGHT = "RIGHT"

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
        self.nnc = NatNetClient()
        self.nnc.markers_listener = self.markers_listener

        # init optitracker #
        self.ot = OptiTracker(marker_count=10)

        # set up initial data directories for mocap recordings #
        if not os.path.exists("OptiData"):
            os.mkdir("OptiData")

        if not os.path.exists("OptiData"):
            os.mkdir("OptiData")

        os.mkdir(f"OptiData/{P.p_id}")
        os.mkdir(f"OptiData/{P.p_id}/testing")

        if P.run_practice_blocks:
            os.mkdir(f"OptiData/{P.p_id}/practice")

        # get base unit for sizings & positionings #
        self.px_cm = P.ppi / 2.54

        # spawn basic shapes #
        self.box = kld.Annulus(
            diameter=self.px_cm * CIRC_SIZE,
            thickness=self.px_cm * LINE_WIDTH,
            fill=GRAY,
        )
        self.fix = kld.FixationCross(
            size=FIX_SIZE * self.px_cm, thickness=self.px_cm * LINE_WIDTH, fill=GRAY
        )

        # define necessary locations #
        self.locs = {
            "start": (
                P.screen_x // 2,  # type: ignore[operator]
                P.screen_y - 3 * self.px_cm,  # type: ignore[operator]
            ),
            "left": (
                P.screen_x // 2 - (H_OFFSET * self.px_cm),  # type: ignore[operator]
                P.screen_y - (V_OFFSET * self.px_cm),  # type: ignore[operator]
            ),
            "center": (
                P.screen_x // 2,  # type: ignore[operator]
                P.screen_y - (V_OFFSET * self.px_cm),  # type: ignore[operator]
            ),
            "right": (
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

        # make copy of "template" list defined in _params.py
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
            - After CTOA (1, 1.4, 1.8, or 2.2 s), target
            - Reach begins
            - Target removed after <= 1,500 ms
                - (is this a timeout?)
        """
        self.validity, self.cue_laterality = self.trial_list.pop()

    def trial(self):  # type: ignore[override]

        return {"block_num": P.block_number, "trial_num": P.trial_number}

    def trial_clean_up(self):
        pass

    def clean_up(self):
        pass

    def markers_listener(self, markers: dict) -> None:
        pass
