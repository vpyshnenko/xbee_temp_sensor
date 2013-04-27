
% Using Markov Random Field to model 3 sensor and A/C

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
edgeStruct = UGM_makeEdgeStruct(adj, nStates);
edgeStruct.useMex = 0;

maxState = max(nStates);
nParams = 0;

nodeMap = zeros(nNodes, maxState,'int32');
for i=1:nNodes
    for j=1:nStates(i)
        nParams = nParams+1;
        nodeMap(i,j) = nParams;
    end
end

nEdges = edgeStruct.nEdges;
edgeMap = zeros(maxState,maxState,nEdges,'int32');

for e=1:nEdges
    a = edgeStruct.edgeEnds(e,1);
    b = edgeStruct.edgeEnds(e,2);
    for i=1:nStates(a)
        for j=1:1:nStates(b)
            nParams = nParams+1;
            edgeMap(i,j,e) = nParams;
        end
    end
end

w = zeros(nParams,1);
suffStat = UGM_MRF_computeSuffStat(y,nodeMap,edgeMap,edgeStruct);

moptions.tolFun = 1e-7;
%moptions.Method = 'scg';
w = minFunc(@UGM_MRF_NLL,w,moptions,nInstances,suffStat, ...
    nodeMap,edgeMap, ...
    edgeStruct,@UGM_Infer_Exact);
[nodePot,edgePot] = UGM_MRF_makePotentials(w,nodeMap,edgeMap,edgeStruct);


% ====================================================================

% Get all of the unary and pairwise marginals 
% (as well as the logarithm of the normalizing constant Z) using:

%[nodeBel,edgeBel,logZ] = UGM_Infer_Exact(nodePot,edgePot,edgeStruct)

% Optimal decoding
optimalDecoding = UGM_Decode_Exact(nodePot,edgePot,edgeStruct)

% Clamped samping
%clamped = zeros(nNodes,1);
%clamped(1) = 2; % Heater ON
%edgeStruct.maxIter=1000;
%samples = UGM_Sample_Conditional(nodePot,edgePot, ...
%    edgeStruct,clamped,@UGM_Sample_Exact);


% Plot optimal decoding for nodes states
a = 2;
b = 3;
clamped = zeros(nNodes,1);
x = unique(y(:,a));
xsize = size(x,1);
y0 = zeros(xsize,1);
y1 = zeros(xsize,1);
for i=1:xsize
    clamped(a) = x(i);
    disp(x(i))
    % Heater ON
    clamped(1) = 2; 
    v = UGM_Decode_Conditional(nodePot,edgePot,edgeStruct, ...
        clamped,@UGM_Decode_Tree);
    y0(i) = v(b);
    
    % Heater OFF
    clamped(1) = 1; 
    v = UGM_Decode_Conditional(nodePot,edgePot,edgeStruct, ...
        clamped,@UGM_Decode_Tree);
    y1(i) = v(b);
    
end
mina=min(unique(y(:,[a b])))
maxa=max(unique(y(:,[a b])))
plot(x,y0,'r');
axis([ mina maxa mina maxa ])
hold on;
p=plot(x,y1,'g');
xlabel(a)
ylabel(b)

saveas(p,sprintf('results/%d-%d.png',a,b)) 

