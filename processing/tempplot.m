function [ p ] = tempplot( a, b, nNodes, y, yoff, nodePot, edgePot, edgeStruct)
%UNTITLED Plot two temperatures plots
clamped = zeros(nNodes,1);
x = unique(y(:,a));
xsize = size(x,1);
y0 = zeros(xsize,1);
y1 = zeros(xsize,1);
for i=1:xsize
    clamped(a) = x(i);    
    % Heater ON
    clamped(1) = 2; 
    v = transpose(UGM_Decode_Conditional(nodePot,edgePot,edgeStruct, ...
        clamped,@UGM_Decode_Tree))+yoff;
    y0(i) = v(b);
    
    % Heater OFF
    clamped(1) = 1; 
    v = transpose(UGM_Decode_Conditional(nodePot,edgePot,edgeStruct, ...
        clamped,@UGM_Decode_Tree))+yoff;
    y1(i) = v(b);
    
end
yc=bsxfun(@plus,double(y),yoff);
mina=min(unique(yc(:,[a b])));
maxa=max(unique(yc(:,[a b])));
xc = x+yoff(a);
plot(xc,y0, 'red', 'LineWidth', 3);
axis([ mina maxa mina maxa ]);
hold on;
plot(xc,y1,'green');
hold on;
p=plot(mina:maxa,mina:maxa,'-.k');
xlabel(a);
ylabel(b);

end

