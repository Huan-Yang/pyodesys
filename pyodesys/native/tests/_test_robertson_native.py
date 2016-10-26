# -*- coding: utf-8 -*-

import numpy as np
import sympy as sp

from pyodesys.core import integrate_chained
from pyodesys.symbolic import PartiallySolvedSystem, symmetricsys, TransformedSys
from pyodesys.tests._robertson import get_ode_exprs


def _test_chained_multi_native(NativeSys, **kwargs):
    logc, logt, reduced = kwargs.pop('logc'), kwargs.pop('logt'), kwargs.pop('reduced')
    zero_time, zero_conc, nonnegative = kwargs.pop('zero_time'), kwargs.pop('zero_conc'), kwargs.pop('nonnegative')
    logexp = (sp.log, sp.exp)

    ny, nk = 3, 3
    k = (.04, 1e4, 3e7)
    init_conc = (1, zero_conc, zero_conc)
    t0, tend = zero_time, 1e11
    tot0 = np.sum(init_conc)
    _yref_1e11 = (0.2083340149701255e-7, 0.8333360770334713e-13, 0.9999999791665050)

    _s = NativeSys.from_callback(get_ode_exprs(logc=False, logt=False)[0], ny, nk,
                                 nonnegative=nonnegative)
    logexp = (sp.log, sp.exp)

    if reduced:
        class PartiallySolvedNativeSystem(PartiallySolvedSystem, NativeSys):
            pass

        other1, other2 = [_ for _ in range(3) if _ != (reduced-1)]
        s = PartiallySolvedNativeSystem(_s, lambda x0, y0, p0: {
            _s.dep[reduced-1]: y0[0] + y0[1] + y0[2] - _s.dep[other1] - _s.dep[other2]
        })
    else:
        s = _s

    if logc or logt:
        class TransformedNativeSys(TransformedSys, NativeSys):
            pass
        SS = symmetricsys(logexp if logc else None, logexp if logt else None, SuperClass=TransformedNativeSys)
        s = SS.from_other(s)

    for sys_iter, kw in [([s, _s], {'nsteps': [100, 1513*1.01], 'return_on_error': [True, False]}),
                         ([_s], {'nsteps': [1705*1.01]})]:
        _x, _y, _nfo = integrate_chained(
            sys_iter, kw, [(zero_time, 1e11)]*3,
            [init_conc]*3, [k]*3, integrator='cvode', atol=1e-10, rtol=1e-14)

        for x, y, nfo in zip(_x, _y, _nfo):
            assert np.allclose(_yref_1e11, y[-1, :], atol=1e-16, rtol=0.02)
            assert nfo['success'] is True
            assert nfo['nfev'] > 100
            assert nfo['njev'] > 10
            assert nfo['nsys'] in (1, 2)
