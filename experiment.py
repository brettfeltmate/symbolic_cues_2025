# -*- coding: utf-8 -*-

__author__ = "Brett Feltmate"

import klibs
from klibs import P
from klibs.KLGraphics import KLDraw as kld

GRAY = (128, 128, 128, 255)


class symbolic_cues_2025(klibs.Experiment):

    def setup(self):
        """
        Size & Positions:
            - Start point = 3^2 cm, bottom-centre
            - Fixation cross = 4^2 cm, placed 21 cm above start
            - Placeholders: 3^2 cm, placed 7.5 cm to the left and right of fixation
            - Symbolic cues: ~4 x 3.5 cm, replacing fixation
        """

        self.px_cm = P.ppi / 2.54

        self.box = kld.Rectangle(width=3 * self.px_cm, fill=GRAY)
        self.fix = kld.FixationCross(
            size=4 * self.px_cm, thickness=self.px_cm // 2, fill=GRAY
        )

        self.locs = {
            "start": (P.screen_x // 2, P.screen_y - 3 * self.px_cm),  # type: ignore[operator]
            "left": (P.screen_x // 2 - (7.5 * self.px_cm), P.screen_y - (21 * self.px_cm)),  # type: ignore[operator]
            "center": (P.screen_x // 2, P.screen_y - (21 * self.px_cm)),  # type: ignore[operator]
            "right": (P.screen_x // 4 + (7.5 * self.px_cm), P.screen_y - (21 * self.px_cm)),  # type: ignore[operator]
        }


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
