function [] = iris(k)
    if nargin == 0
       k = 3; 
    end
    
    data  = readtable('test/iris.dat');
    means = kmeans(data{:,1:4}, k);
    
    data.class = categorical(data.class);
    classes    = categories(data.class);
    
    figure(1); clf; hold on;
    for i=1:length(classes)
         points = data( data.class == classes(i), 1:4 );
         plot(points{:, 1}, points{:, 2}, 'o', 'color', rand(3,1));
    end
    plot(means(:, 1), means(:, 2), 'k.', 'MarkerSize', 20);
    
end