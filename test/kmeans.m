function [means, clust, err] = kmeans(data, k)
    Numnum.arguments('data', data, 'k', k);
    
    [means, clust, err] = kmeans_internal(data, k);
    for i=1:5
        [means_, clust_, err_] = kmeans_internal(data, k);
        if err_ < err
            means = means_;
            clust = clust_;
            err   = err_;
        end
    end
    
    Numnum.returns('means', means, 'clust', clust, 'err', err);
end

% This private function cannot be unit tested
% but it can still be integration tested
function [means, clust, err] = kmeans_internal(data, k)
    n = size(data,1);
    p = size(data,2);

    means = data( ceil( Numnum.rand(k,1)*n) , : ) + Numnum.randn(k, p)*1e-3;
    dists = zeros(n, k);
    clust = zeros(n, 1);
    done  = 0;
    while done ~= k
        done = 0;
        for i=1:k
            temp = repmat(means(i, :), n, 1) - data;
            dists(:, i) = dot(temp, temp, 2);
        end
        [vals, clust] = min(dists, [], 2);
        err = sum(vals);
        
        for i=1:k
            mu = mean(data( clust==i, : ), 1);
            if norm(means(i, :) - mu, 2) < 1e-3
                done = done + 1;
            end
            means(i, :) = mu;
        end
    end
end