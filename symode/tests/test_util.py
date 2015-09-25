from __future__ import absolute_import

from .. import OdeSystem
from ..util import banded_jacobian
from .test_symode import decay_dydt_factory


def test_banded_jacobian():
    # Decay chain of 3 species (2 decays)
    # A --[k0=4]--> B --[k1=3]--> C
    tend, k, y0 = 2, [4, 3], (5, 4, 2)
    odesys = OdeSystem.from_callback(decay_dydt_factory(k), len(k)+1)
    bj = banded_jacobian(odesys.exprs, odesys.dep, 1, 0)
    assert bj.tolist() == [
        [-k[0], -k[1], 0],
        [k[0], k[1], 0],
    ]