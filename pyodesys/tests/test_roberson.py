# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)

import numpy as np

import sympy

from .. import OdeSys
from ..symbolic import SymbolicSys, PartiallySolvedSystem, symmetricsys
from ._robertson import run_integration, get_ode_exprs

_yref_1e11 = (0.2083340149701255e-7, 0.8333360770334713e-13, 0.9999999791665050)


def test_run_integration():
    xout, yout, info = run_integration(integrator='odeint')
    assert info['success'] is True


def _test_get_ode_exprs(symbolic=False, reduced=0, extra_forgive=1, logc=False,
                        logt=False, zero_conc=0, zero_time=0, atol=1e-14, rtol=1e-10):
    ny, nk = 3, 3
    k = (.04, 1e4, 3e7)
    y0 = (1, zero_conc, zero_conc)
    tot0 = np.sum(y0)
    nsteps_cvode_1e11 = int(6000)
    kwargs = dict(integrator='cvode', atol=atol, rtol=rtol, nsteps=nsteps_cvode_1e11)

    atol_forgive = {
        0: 5,
        1: 15000,
        2: 7,
        3: 4
    }

    if symbolic:
        _s = SymbolicSys.from_callback(get_ode_exprs(logc=False, logt=False)[0], ny, nk)
        logexp = (sympy.log, sympy.exp)
        if logc:
            SS = symmetricsys(logexp)
            _s = SS.from_other(_s)
        if logt:
            raise NotImplementedError("will do this soon...")
        if reduced:
            other1, other2 = [_ for _ in range(3) if _ != (reduced-1)]
            s = PartiallySolvedSystem(_s, lambda x0, y0, p0: {
                _s.dep[reduced-1]: y0[0] + y0[1] + y0[2] - _s.dep[other1] - _s.dep[other2]
            })
        else:
            s = _s
    else:
        f, j = get_ode_exprs(logc=logc, logt=logt, reduced=reduced)
        if reduced:
            ny -= 1
            k += y0
            y0 = [y0[idx] for idx in range(3) if idx != reduced - 1]

        s = OdeSys(f, j, autonomous=True)

        if logc:
            y0 = np.log(y0)

    x, y, i = s.integrate((zero_time, 1e11), y0, k, **kwargs)
    assert i['success'] is True
    if reduced and not symbolic:
        y = np.insert(y, reduced-1, tot0 - np.sum(y, axis=1), axis=1)
    if logc and not symbolic:
        y = np.exp(y)
    assert np.allclose(_yref_1e11, y[-1, :],
                       atol=kwargs['atol']*atol_forgive[reduced]*extra_forgive,
                       rtol=kwargs['rtol'])


def test_get_ode_exprs_symbolic():
    _test_get_ode_exprs(symbolic=True, logc=True, zero_conc=1e-20, atol=1e-8, rtol=1e-10, extra_forgive=2)
    for reduced in range(4):
        _test_get_ode_exprs(symbolic=True, reduced=reduced)


def test_get_ode_exprs_OdeSys():
    for reduced in range(4):
        _test_get_ode_exprs(symbolic=False, reduced=reduced, extra_forgive=3)
    _test_get_ode_exprs(symbolic=False, logc=True, zero_conc=1e-20, atol=1e-8, rtol=1e-10, extra_forgive=2)
