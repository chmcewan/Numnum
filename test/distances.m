% NB: this implementation is different from Python
function [d] = distances( mu, data )
    Numnum.arguments('mu', mu, 'data', data);
    temp = repmat(mu, size(data,1), 1) - data;
    d = dot(temp, temp, 2);
    Numnum.returns('d', d);
end

