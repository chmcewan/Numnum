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
    end
    
    methods
        % push new context onto stack
        function [ctx] = push( this )
            name = Numnum.caller(1);
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
                runs = this.state.(ctx.name);
                runs{ ctx.run } = ctx;
                this.state.(ctx.name) = runs;
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

            if nargin == 1 || isempty(mode)
                mode = 0;
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
                            [results{1:N}] = f( run.arg{ 2:2:end  } );
                            this.mode  = -1;

                            try
                                for k=1:2:length(run.ret)
                                    Numnum.equivalent( run.ret{k+1}, results{ ceil(k/2)}, run.ret{k}, run.ret{k} );
                                end
                                passes = passes + 1;
                            catch exception
                                
                            end
                        end
                        fprintf('%s %d%% pass (%d/%d)\n', run.name, round(passes/length(runs)*100), run.run, length(runs));
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
        function arguments(varargin)
            this = Numnum.get_instance();
            if this.mode
                this.push();
                try
                    this.validate('arg', varargin{:});
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
                    this.validate('ret', varargin{:});
                catch exception
                    throwAsCaller(exception)
                end
                this.pop();
            end
        end
        
        % Validate function intermediate values
        function values(varargin)
            this = Numnum.get_instance();
            if this.mode
                try
                    this.validate('val', varargin{:});
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
                    throw(MException('Numnum:equivalent', sprintf('%s ~= %s\n%f ~= %f\n', A, B, a, b)));
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
                % FIXME: slow and dumb...
                for i=1:r
                    for j=1:c
                        v(i,j)    = this.state.numnum_randn( mod(this.idxn, size(this.state.numnum_randn, 2)) + 1 );
                        this.idxn = this.idxn + 1;
                    end
                end
            end
        end
        
        % Reproducible deterministic random number generation
        function [v] = rand(r, c)
            this = Numnum.get_instance();
            v    = rand(r, c);
            if this.mode || this.unit
                % FIXME: slow and dumb...
                for i=1:r
                    for j=1:c
                        v(i,j)    = this.state.numnum_rand( mod(this.idxu, size(this.state.numnum_rand, 2)) + 1 );
                        this.idxu = this.idxu + 1;
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

