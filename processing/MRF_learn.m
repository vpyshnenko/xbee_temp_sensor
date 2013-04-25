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

nodeMap = zeros(nNodes,maxState,'int32');
nodeMap(:,1) = 1;

nEdges = edgeStruct.nEdges;
edgeMap = zeros(maxState,maxState,nEdges,'int32');
