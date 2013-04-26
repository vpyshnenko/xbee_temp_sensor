
clear all;
addpath(genpath('~/lib/matlab/UGM'));

dac_state = int32(csvread('dac_state.csv', 1));
dtemps = int32(csvread('dtemps.csv', 1));

y = [dac_state(:,1), dtemps(:,[4 5 7])] + 1;
clear dac_state;
clear dtemps;

[nInstances,nNodes] = size(y);
nStates = max(y);
adj = [0 1 0 1 ; 
       1 0 0 1 ; 
       0 0 0 1 ; 
       1 1 1 0 ];
edgeStruct = UGM_makeEdgeStruct(adj,nStates);

maxState = max(nStates);
nParams = 0;

nodeMap = zeros(nNodes,maxState,'int32');
for i=1:nNodes
    nParams = nParams+1;
    for j=1:nStates(i)
        nodeMap(i,j) = nParams;
    end
end

% Node 1 (HVAC) is special. It have 2 weights
nParams = nParams+1;
nodeMap(1,1) = nParams

nEdges = edgeStruct.nEdges;
edgeMap = zeros(maxState,maxState,nEdges,'int32');

for i=1:nNodes
    for j=i:nNodes
        if adj(i,j)==1
            nParams = nParams+1;
            edgeMap(i,j,:) = nParams; 
            edgeMap(j,i,:) = nParams;
        end
    end
end

w = zeros(nParams,1);
suffStat = UGM_MRF_computeSuffStat(y,nodeMap,edgeMap,edgeStruct);

moptions.tolFun = 1e-5;
w = minFunc(@UGM_MRF_NLL,w,moptions,nInstances,suffStat, ...
    nodeMap,edgeMap, ...
    edgeStruct,@UGM_Infer_Exact);

[nodePot,edgePot] = UGM_MRF_makePotentials(w,nodeMap,edgeMap,edgeStruct);



