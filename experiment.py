# -*- coding: utf-8 -*-

__author__ = "Brett Feltmate"

import klibs
from klibs import P
from klibs.KLGraphics import KLDraw as kld
from klibs.KLGraphics import KLNumpySurface as kln
from klibs.KLBoundary import BoundarySet, CircleBoundary

from natnetclient_rough import NatNetClient  # type: ignore[import]
from OptiTracker import OptiTracker  # type: ignore[import]

from random import shuffle

GRAY = (128, 128, 128, 255)
WHITE = (255, 255, 255, 255)

V_OFFSET = 21
H_OFFSET = 7.5
CIRC_SIZE = 3
FIX_SIZE = 4
LINE_WIDTH = 0.2
IMAGE_WIDTH = 4  # cms

HIGH_LEFT = "HIGH_LEFT"
HIGH_RIGHT = "HIGH_RIGHT"
LOW_LEFT = "LOW_LEFT"
LOW_RIGHT = "LOW_RIGHT"

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

            Cue breakdown
                - High % Left: 78.5 / 21.5
                - High % Right: 21.5 / 78.5
                - Low % Left: 53.5 / 46.5
                - Low % Right: 46.5 / 53.5

            Image/cue mappings counter-balanced
        """

        self.ot = OptiTracker()
        self.nnc = NatNetClient()

        self.px_cm = P.ppi / 2.54

        self.images = {
            "bowtie": kln.NumpySurface(
                "ExpAssets/Resources/image/bowtie.jpg", width=IMAGE_WIDTH * self.px_cm
            ),
            "laos": kln.NumpySurface(
                "ExpAssets/Resources/image/laos.jpg", width=IMAGE_WIDTH * self.px_cm
            ),
            "legoman": kln.NumpySurface(
                "ExpAssets/Resources/image/legoman.jpg", width=IMAGE_WIDTH * self.px_cm
            ),
            "barbell": kln.NumpySurface(
                "ExpAssets/Resources/image/bowtie.jpg", width=IMAGE_WIDTH * self.px_cm
            ),
        }

        cue_validities = [HIGH_LEFT, HIGH_RIGHT, LOW_LEFT, LOW_RIGHT]

        shuffle(cue_validities)

        self.cues = {
            cue_validities[0]: self.images["bowtie"],
            cue_validities[1]: self.images["laos"],
            cue_validities[2]: self.images["legoman"],
            cue_validities[3]: self.images["barbell"],
        }

        self.box = kld.Annulus(
            diameter=self.px_cm * CIRC_SIZE,
            thickness=self.px_cm * LINE_WIDTH,
            fill=GRAY,
        )
        self.fix = kld.FixationCross(
            size=FIX_SIZE * self.px_cm, thickness=self.px_cm * LINE_WIDTH, fill=GRAY
        )

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

    def block(self):
        pass

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
        pass

    def trial(self):  # type: ignore[override]

        return {"block_num": P.block_number, "trial_num": P.trial_number}

    def trial_clean_up(self):
        pass

    def clean_up(self):
        pass

    def make_cue(self, cue_type: str):
        """
        - barbell: 320 total length, bells 115 diam, bar 60 thick
        - bowtie: 300 long & 240 tall iso triangles (angle unknown), apexes inwards
        - legoman: body (cross) 200x200 & 70 thick, feet (bar) 200 long & 70 thick
        - laos: top/bot bar 300 long & 70 thick, dot 130 diam

        """
        cue = None

        if cue_type == "barbell":
            pass
        elif cue_type == "bowtie":
            pass
        elif cue_type == "legoman":
            pass
        elif cue_type == "laos":
            pass
        else:
            raise ValueError(
                "Invalid cue type. Must be one of 'barbell', 'bowtie', 'legoman', or 'laos'."
            )

        return cue
