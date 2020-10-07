from dataclasses import dataclass

from earnmi.model.Dimension import Dimension


@dataclass
class QuantData(object):
    """
    维度值
    """
    dimen: Dimension

    def __post_init__(self):
        pass