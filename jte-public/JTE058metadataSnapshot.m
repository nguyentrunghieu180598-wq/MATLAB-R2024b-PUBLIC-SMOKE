function meta=JTE058metadataSnapshot(out)
% Public API -> plain structs, avoiding opaque MCOS-only independent evidence.
assert(isa(out,'Simulink.SimulationOutput'),'JTE058:SimulationOutput','Synthetic/staging contract assertion failed.');
s=out.SimulationMetadata;
meta=struct('modelInfo',s.ModelInfo,'executionInfo',s.ExecutionInfo, ...
 'timingInfo',s.TimingInfo,'matlabVersion',version,'matlabRelease',version('-release'));
assert(isstruct(meta.modelInfo)&&isstruct(meta.modelInfo.SolverInfo),'JTE058:ModelInfo','Synthetic/staging contract assertion failed.');
assert(meta.modelInfo.StopTime>meta.modelInfo.StartTime,'JTE058:EffectiveHorizon','Synthetic/staging contract assertion failed.');
end
