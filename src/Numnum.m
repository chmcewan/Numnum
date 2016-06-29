classdef Numnum < handle
    %NUMNUM Numerical unit and integration testing for (and between) Matlab and Python
        
    properties
        idxn    = 0
        idxu    = 0
        ids     = struct()
        ctx     = {}
        gid     = 0
        state   = []
        mode    = 0
        unit    = 0
        depth   = 0
    end
    
    methods
        % push new context onto stack
        function [ctx] = push( this, name )
            if nargin < 2
                name = Numnum.caller(1);
            end
            if isfield(this.ids, name)
                this.ids.(name) = this.ids.(name) + 1;
            else
                this.ids.(name) = 1;
            end
            ctx = [];
            ctx.name = name;
            ctx.run  = this.ids.(name);
            this.ctx{end + 1} = ctx;              
        end
        
        % Pop a context off of the stack
        function [ctx] = pop( this )
            ctx = this.ctx{end};
            if this.mode > 0
                if ~isfield(this.state, ctx.name)
                    this.state.(ctx.name) = {};
                end
%                 runs = this.state.(ctx.name);
%                 runs{ ctx.run } = ctx;
                this.state.(ctx.name){ ctx.run } = ctx;
            end
            this.ctx(end) = [];
        end
        
        % Common validation functionality
        function [] = validate(this, str, varargin)
            ctx = this.ctx{end};
            
            if this.mode > 0
                ctx.(str) = varargin;
            else
                funs = this.state.( ctx.name );
                fun  = funs{ ctx.run };
                vals = fun.(str);
                if length(vals) ~= length(varargin)
                    throw(MException('Numnum:validate', 'Incorrect number of values to validate'));
                end
                
                for i=1:2:length(varargin)
                    key_a = varargin{i};
                    val_a = varargin{i+1};
                    key_b = vals{i};
                    val_b = vals{i+1};
                    Numnum.equivalent(val_a, val_b, key_a, key_b);
                end 
                
            end    
            this.ctx{end} = ctx;
        end
    end
    
    
    
    methods(Static)
   
        % Returns static state since no language support in Matlab 
        function [obj] = get_instance()
            persistent singleton;
            if isempty(singleton)
                singleton = Numnum();
            end
            obj = singleton;
        end
        
        % Reads static state from file and reset dynamic state
        function [] = replay(filename, mode)        
            this       = Numnum.get_instance();
            this.idxn  = 0;
            this.idxu  = 0;
            this.ids   = struct();
            this.ctx   = {};
            this.gid   = 0;
            this.state = load(filename);
            this.mode  = -1;
            this.unit  = 1;

            testname = [];
            if nargin == 1 || isempty(mode)
                mode = 0;
            elseif strcmp(class(mode), 'char')
                testname = mode;
                mode     = -1;
            end
            
            % run integration test
            if mode == 0 || mode > 0
                f = str2func(this.state.numnum_function);
                v = this.state.numnum_varargin;
                f(v{:});
            end
            
            % run unit tests
            if mode == 0 || mode < 0
                funcs = fieldnames(this.state);
                for i=1:numel(funcs)
                    func = funcs{i};
                    
                    if ~isempty(testname) && ~strcmp(testname, func)
                        continue;
                    end
          
                    if ~strncmpi(func,'numnum_',7)
                        runs = this.state.(func);  
                        f    = str2func(func);
                        try
                            N = nargout(f);
                        catch exception
                            fprintf('Skipping %s...\n', func);
                            continue;
                        end
                        
                        passes = 0;
                        for j=1:length(runs)
                            run = runs{j};
                            this.mode  = 0; % disable verification in functions
                            this.unit  = 1; % keep random generation enabled
                            this.idxn  = 0; % reset random numbers
                            this.idxu  = 0;
                            
                            N = length(run.ret) / 2;
                            [results{1:N}] = f( run.arg{ 2:2:end  } );
                            this.mode  = -1;

                            try
                                for k=1:2:length(run.ret)
                                    Numnum.equivalent( run.ret{k+1}, results{ ceil(k/2)}, run.ret{k}, run.ret{k} );
                                end
                                passes = passes + 1;
                            catch exception
                                warning off backtrace
                                warning('%s(%d): %s', func, run.run, exception.message)
                            end
                        end
                        fprintf('%s %d%% pass (%d/%d)\n', run.name, round(passes/length(runs)*100), passes, length(runs));
                    end
                end
            end
        end   
        
        % Writes static state to file and reset dynamic state. Seed is optional.
        function [] = record(filename, f, varargin) 
            this       = Numnum.get_instance();
            this.idxn  = 0;
            this.idxu  = 0;
            this.ids   = struct();
            this.ctx   = {};
            this.gid   = 0;
            this.state = struct();
            this.mode  = 1;
            this.unit  = 0;

            seed = 'shuffle';
            n    = 10000;
        
            rng(seed);
            this.state.numnum_randn    = randn(1, n);
            this.state.numnum_rand     = rand(1, n);
            this.state.numnum_function = func2str(f);
            this.state.numnum_varargin = varargin;
            f(varargin{:});
            
            
            tmp = this.state;
            save(filename, '-struct', 'tmp', '-v7'); 
        end
                      
        % Utility to retrieve calling functions name
        function [f] = caller( offset )
            if nargin == 0
                offset = 0;
            end
            st = dbstack(2 + offset);
            if size(st, 1) == 0
                f = 'global';
            else
                f = st.name;
            end
        end
                 
        % Validate function arguments
        function arguments(callerName,varargin)
            this = Numnum.get_instance();
            if this.mode
                try
                    args = varargin;
                    if cellfun( @(t) ischar(t), varargin)
                        args = cell(1, length(args)*2);
                        for i=1:2:length(args)
                            args{i}   = varargin{ceil(i/2)};
                            args{i+1} = evalin('caller', varargin{ceil(i/2)});
                            %fprintf('%s : in %s %dx%d\n', Numnum.caller(), args{i}, size(args{i+1}, 1), size(args{i+1}, 2));
                        end
                    end
                    this.push(callerName);
                    this.validate('arg', args{:});
                catch exception
                    throwAsCaller(exception)
                end
            end
        end
        
        % Validate function return values
        function returns(varargin)
            this = Numnum.get_instance();
            if this.mode
                try
                    args = varargin;
                    if cellfun( @(t) ischar(t), varargin )
                        args = cell(1, length(args)*2);
                        for i=1:2:length(args)
                            args{i}   = varargin{ceil(i/2)};
                            args{i+1} = evalin('caller', varargin{ceil(i/2)});
                            %fprintf('%s : out %s %dx%d\n', Numnum.caller(), args{i}, size(args{i+1}, 1), size(args{i+1}, 2));
                        end
                    end                    
                    this.validate('ret', args{:});
                    this.pop();
                catch exception
                    throwAsCaller(exception)
                end
            end
        end
        
        % Validate function intermediate values
        function values(varargin)
            this = Numnum.get_instance();
            if this.mode
                try
                    args = varargin;
                    if cell2mat(cellfun( @(t) strcmp(class(t),'char'), varargin , 'UniformOutput', 0))
                        args = cell(1, length(varargin)*2);
                        for i=1:2:length(args)
                            args{i}   = varargin{ceil(i/2)};
                            args{i+1} = evalin('caller', varargin{ceil(i/2)});
                        end
                    end                    
                    this.validate('val', args{:});
                catch exception
                    throwAsCaller(exception)
                end
            end
        end          
    
        % Check for equivalence between structures
        % TODO: support cells and structs...
        function [] = equivalent(a, b, A, B)
            if nargin == 2
                A = 'a';
                B = 'b';
            end
            if ~strcmp(class(a), class(b))
                throw(MException('Numnum:equivalent', sprintf('class(%s) = %s and class(%s) = %s', A, class(a), B, class(b))));
            end
            if isnumeric(a) 
                if sum(size(a) ~= size(b))
                    throw(MException('Numnum:equivalent', sprintf('size(%s) = %dx%d and size(%s) = %dx%d', A, size(a,1), size(a,2), B, size(b,1), size(b, 2))));
                end
                
                if abs(a-b) >= 1e4 * eps(min(abs(a),abs(b)))
                    throw(MException('Numnum:equivalent', sprintf('%s ~= %s\n%d', A, B, evalc('disp(a);disp(b)'))));
                end
            elseif isstruct(a)
                return
            elseif iscell(a)
                return
            end
        end        
         
        % Reproducible deterministic random number generation
        function [v] = randn(r, c)
            this = Numnum.get_instance();
            v    = randn(r, c);
            if this.mode || this.unit
                % need to start from deterministic location to recreate for unit tests
                idx = 0;
                for i=1:r
                    for j=1:c
                        v(i,j) = this.state.numnum_randn( mod(idx, size(this.state.numnum_randn, 2)) + 1 );
                        idx    = idx + 1;
                    end
                end
            end
        end
        
        % Reproducible deterministic random number generation
        function [v] = rand(r, c)
            this = Numnum.get_instance();
            v    = rand(r, c);
            if this.mode || this.unit
                % need to start from deterministic location to recreate for unit tests
                idx = 0; 
                for i=1:r
                    for j=1:c
                        v(i,j) = this.state.numnum_rand( mod(idx, size(this.state.numnum_rand, 2)) + 1 );
                        idx    = idx + 1;
                    end
                end
            end  
        end
                
        % Reproducible deterministic random number generation
        function [v] = randperm(n)
            this = Numnum.get_instance();
            v    = randperm(n);
            if this.mode || this.unit
                % FIXME: slow and dumb...
                throw(MException('Numnum:randperm', 'Not implemented'));
            end
        end
        
    end
end

