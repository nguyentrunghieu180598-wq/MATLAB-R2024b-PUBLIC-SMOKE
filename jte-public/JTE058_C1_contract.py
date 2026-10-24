"""C1 within-case identity only. No C0 comparison, MAT I/O or simulation."""
import numpy as np
from JTE058_native_math import _native

def validate_c1(t_true, true_K, t_meas, measured_K, channel_1based, bias_K):
    if isinstance(channel_1based, (bool,np.bool_)) or not isinstance(channel_1based,(int,np.integer)):
        raise ValueError('C1 channel must be integer, 1-based')
    if not 1 <= channel_1based <= 312:
        raise ValueError('C1 channel outside physical312 mapping')
    if isinstance(bias_K,(bool,np.bool_)) or not np.isscalar(bias_K) or not np.isrealobj(bias_K) or bias_K != -2:
        raise ValueError('C1 protocol requires bias=-2 K')
    tt,T=_native(t_true,true_K,'C1_true');tm,M=_native(t_meas,measured_K,'C1_measured')
    if T.shape[1]!=312 or M.shape!=T.shape:
        raise ValueError('C1 requires full312 same-case sensor vectors')
    if not np.array_equal(tt,tm):
        raise ValueError('C1 true/measured clocks must match exactly, including duplicates')
    j=int(channel_1based)-1
    expected=T.copy();expected[:,j]=T[:,j]+bias_K
    if not np.array_equal(M,expected):
        raise ValueError('C1 must change exactly the selected element in each same-case row')
    return {'scope':'C1_WITHIN_CASE_ONLY','rows':len(tt),'channels':312,'channel_1based':int(channel_1based),'bias_K':-2,'identity':'Tmeas=Ttrue; Tmeas(:,j)=Ttrue(:,j)-2; other channels unchanged','scientific_acceptance':False}

def command_area_qualified(t_a,u_a,t_b,u_b,*,signal_name,semantics,evidence_id):
    # A source label is necessary, never sufficient to certify missing events.
    # Caller must supply independently reviewed provenance; this is no token.
    if signal_name!='jteUcore' or semantics!='verified_right_continuous_zoh' or not isinstance(evidence_id,str) or not evidence_id.strip():
        raise ValueError('ZOH area needs verified core-command event semantics; never jteFlwR')
    from JTE058_native_math import command_integral
    for u in (u_a,u_b):
        x=np.asarray(u)
        if x.dtype.kind not in 'fiu' or not np.all(np.isfinite(x)) or np.any(x<0) or np.any(x>1):
            raise ValueError('Expected finite normalized core command 0..1')
    return command_integral(t_a,u_a,t_b,u_b)
