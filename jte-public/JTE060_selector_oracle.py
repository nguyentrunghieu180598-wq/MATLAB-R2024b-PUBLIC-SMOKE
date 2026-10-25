"""Source-matched, SAME-STATE algebraic oracle, synthetic validation only.

Pinned MathWorks reference (tag 24.2.1.5) controller output:
 q = clip(0.1*(Tmax - Tamb), 0.001, 0.95)
 u = max(0.25, q - mod(q,0.25))

This oracle diagnoses feedback selection; it does not compute physical C1-C0
thermal trajectory differences, exact solver switch times, coolant flow or W.
"""
import numpy as np


def _channels(true_K):
    t = np.asarray(true_K)
    if t.dtype.kind not in 'fi' or t.ndim != 2 or t.shape[1] != 312:
        raise ValueError('312 modeled real thermal-observation channels required')
    if not np.all(np.isfinite(t)):
        raise ValueError('Nonfinite thermal observations')
    return t.astype(np.float64)


def pinned_core_command(delta_K):
    x = np.asarray(delta_K)
    if x.dtype.kind not in 'fi' or not np.all(np.isfinite(x)):
        raise ValueError('Real finite delta-K required')
    q = np.minimum(0.95, np.maximum(0.001, 0.1*x))
    return np.maximum(0.25, q - np.mod(q,0.25))


def same_state_oracle(true_K, channel_1based, bias_K, ambient_K):
    """Algebraic counterfactual under SAME instantaneous physical vector.

    Loss identity: L_j=min(|bias|,max(0,T_j-max_{i!=j}T_i)).
    Never use the C0 physical temperature in place of true_K from C1.
    """
    T = _channels(true_K)
    if isinstance(channel_1based, (bool,np.bool_)) or not isinstance(channel_1based,(int,np.integer)) or not (1<=channel_1based<=312):
        raise ValueError('Channel index must be integer 1..312')
    if isinstance(bias_K, (bool,np.bool_)) or not np.isscalar(bias_K) or not np.isrealobj(bias_K) or not np.isfinite(bias_K) or bias_K>0:
        raise ValueError('Nonpositive finite real bias-K required')
    amb = np.asarray(ambient_K)
    if amb.dtype.kind not in 'fi' or not np.all(np.isfinite(amb)):
        raise ValueError('Finite real ambient-K required')
    if amb.ndim == 0:
        amb = np.full(T.shape[0], float(amb))
    else:
        if amb.ndim!=1 or len(amb)!=T.shape[0]:
            raise ValueError('Ambient must be scalar or aligned vector')
    j = int(channel_1based)-1
    Tmax = T.max(axis=1)
    unaffected = np.concatenate((T[:,:j],T[:,j+1:]),axis=1).max(axis=1)
    M = T.copy()
    M[:,j] += float(bias_K)
    measuredMax = M.max(axis=1)
    measuredLoss = Tmax-measuredMax
    analyticLoss = np.minimum(abs(float(bias_K)),np.maximum(0.,T[:,j]-unaffected))
    if not np.allclose(measuredLoss,analyticLoss,rtol=0.,atol=1e-10):
        raise ArithmeticError('Maximum-selector algebra identity violated')
    coreShadow=pinned_core_command(Tmax-amb)
    coreMeasured=pinned_core_command(measuredMax-amb)
    # For b = -2K, the two 2.5K-separated controller thresholds cannot both
    # be crossed by the SAME-state selector loss <= 2K.
    if float(bias_K)==-2.:
        discrepancy=coreMeasured-coreShadow
        if not np.all((np.abs(discrepancy)<1e-10)|(np.abs(discrepancy+.25)<1e-10)):
            raise ArithmeticError('Two-level command change violates -2K threshold spacing')
    return {
        'selector_loss_K': measuredLoss,
        'selector_oracle_K': analyticLoss,
        'reported_Tmax_K': measuredMax,
        'core_shadow': coreShadow,
        'core_biased_same_state':coreMeasured,
        'scope':'SAME_STATE_SELECTOR_CONTROL_ORACLE_NOT_CLOSED_LOOP_C1_C0',
        'result_is_study_data':False
    }
