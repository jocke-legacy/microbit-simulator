from abc import ABCMeta, abstractmethod

import numpy as np


class AbstractRenderer(metaclass=ABCMeta):
    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def render_display(self, buffer: np.ndarray) -> None:
        pass
