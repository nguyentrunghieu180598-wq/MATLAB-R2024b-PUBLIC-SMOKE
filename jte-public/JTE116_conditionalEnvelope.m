function e=JTE116_conditionalEnvelope(t,y,y0)
t=t(:);y=y(:);a=-expm1(-t/.001);
lo=y0+(.25-y0)*a;hi=y0+(.75-y0)*a;
margin=32*eps(max([ones(size(t)),abs(y),abs(lo),abs(hi),abs(y0)*ones(size(t))],[],2));
e=struct('time',t,'y0',y0,'lower',lo,'upper',hi,'margin32ULP',margin,...
 'excess',max([lo-y,y-hi,zeros(size(t))],[],2),'flag',y<lo-margin|y>hi+margin,...
 'scope','Conditional bounded-input/reset-free LTI envelope;32ULP is interval roundoff localization only, not thermal or plant convergence tolerance.');
end
