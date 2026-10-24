function receipt=JTE058validateC1(t,T,tm,M,j,biasK)
% Within-case measurement identity ONLY. No C0 or other physical case input.
validateattributes(t,{'double'},{'real','vector','finite','nonempty'});
validateattributes(tm,{'double'},{'real','vector','finite','nonempty'});
validateattributes(T,{'double'},{'real','2d','finite','nonempty'});
validateattributes(M,{'double'},{'real','2d','finite','nonempty'});
validateattributes(j,{'double'},{'real','scalar','integer','>=',1,'<=',312});
assert(isequal(biasK,-2),'JTE058:C1Bias','C1 protocol requires -2 K.');
t=t(:);tm=tm(:);
assert(numel(t)>=2&&all(diff(t)>=0)&&t(end)>t(1),'JTE058:C1Clock');
assert(isequal(t,tm),'JTE058:C1Clock','Same-case clocks including duplicates must match.');
assert(size(T,1)==numel(t)&&size(T,2)==312&&isequal(size(M),size(T)),'JTE058:C1Shape');
expected=T;expected(:,j)=T(:,j)+biasK;
assert(isequal(M,expected),'JTE058:C1Identity','Exactly one selected channel must carry bias in each row.');
receipt=struct('schema','JTE058_C1_WITHIN_CASE_VALIDATION','rows',numel(t), ...
 'channels',312,'channel_1based',j,'biasK',biasK,'scientificAcceptance',false);
end
