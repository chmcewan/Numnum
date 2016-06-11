import numpy as np
import numpy.matlib
import scipy as sp
import scipy.io as sio
import inspect

singleton = None

class Numnum:
        def __init__(this):
            this.idxn  = 0
            this.idxu  = 0
            this.ids   = {}
            this.ctx   = {}
            this.gid   = 0
            this.state = {}
            this.mode  = 0 
            this.unit  = 0  

        def push(this):
            """ push new context onto stack """
            pass

        def pop(this):
            """ pop context off of stack """
            pass

        def validate(this, str, *args):
            pass



def parse(obj):
    ans = obj
    if type(obj) == dict:
        for key in ans:
            ans[key] = parse(ans[key])       
    elif isinstance(obj, sio.matlab.mio5_params.mat_struct):
        ans = {}
        for key in obj._fieldnames:
            ans[key] = parse(obj.__dict__[key])
    elif isinstance(obj,np.ndarray):
        if obj.dtype == np.dtype('O'):
            # cell-array, otherwise leave alone. Assumes 1D.
            ans = []
            for item in obj:
                ans.append(parse(item))
    return ans

def str2func(name):
    # TODO ...
    pass

def get_instance():
    global singleton
    if singleton == None:
        singleton = Numnum()
    return singleton

def replay(filename, mode=0):      
    this       = get_instance()
    this.idxn  = 0
    this.idxu  = 0
    this.ids   = {}
    this.ctx   = {}
    this.gid   = 0
    this.state = parse(sio.loadmat(filename, chars_as_strings=True, struct_as_record=False, squeeze_me=True))
    this.mode  = -1
    this.unit  = 1

    # run integration test
    if mode == 0 or mode > 0:
        f = str2func(this.state["numnum_function"])
        v = this.state["numnum_varargin"]
        f(*v)
        
    # run unit tests
    if mode == 0 or mode < 0:
        for key in this.state.keys():
            if not( key.startswith("numnum_") ):
                runs = this.state[key]  
                f    = str2func(key)
                if f == None:
                    print('Skipping %s...\n' % key)
                    continue
                             
                passes = 0
                for j in range(0, len(runs)): 
                    run = runs[j]
                    this.mode  = 0 # disable verification in functions
                    this.unit  = 1 # keep random generation enabled
                    this.idxn  = 0 # reset random numbers
                    this.idxu  = 0

                    # TODO
                    [results{1:N}] = f( run.arg{ 2:2:end  } );
                    
                    this.mode  = -1

                    try
                        for k in range(0, len(run["ret"]), 2):
                            equivalent( run["ret"][k+1], results[ceil(k/2)], run["ret"][k], run["ret"][k] )
                        end
                        passes = passes + 1;
                    except:
                        pass
                
                print("%s %d%% pass (%d/%d)\n" % (run["name"], round(passes/len(runs)*100), run["run"], len(runs) ))
            end
        end
    end


def record(filename, f, *args):
    this       = get_instance()
    this.idxn  = 0
    this.idxu  = 0
    this.ids   = {}
    this.ctx   = {}
    this.gid   = 0
    this.state = {}
    this.mode  = 1
    this.unit  = 0

    n = 10000
    this.state["numnum_randn"]    = np.random.standard_normal((1, n))
    this.state["numnum_rand"]     = np.random.uniform( (1, n) )
    this.state["numnum_function"] = None # FIXME
    this.state["numnum_varargin"] = args

    f(*args)
    sio.savemat(filename, this.state)

def equivalent(a, b, A = "a", B = "b"):

    if type(a) != type(b):
        raise Exception(sprintf('class(%s) = %s and class(%s) = %s', A, type(a), B, type(b)))

    if type(a) == np.ndarray: 
        if a.shape != b.shape:
            raise Exception(sprintf('size(%s) = %dx%d and size(%s) = %dx%d', A, a.shape[0], a.shape[1], B, b.shape[0], b.shape[1]))
                
        if abs(a-b) >= 1e4 * eps(min(abs(a),abs(b))):
            raise Exception(sprintf('%s ~= %s\n%f ~= %f\n', A, B, a, b))
        
    elif type(a) == dict:
        return
    elif type(a) == list:
        return

def caller():
    return inspect.stack()[1][3]

def arguments(*args):
    this = get_instance()
    if this.mode:
        this.push()
        try:
            this.validate('arg', *args)
        except:
            # TODO: throwAsCaller(exception)
            raise

def returns(*args):
    this = get_instance()
    if this.mode:
        try:
            this.validate('ret', *args)
            this.pop()
        except:
            # TODO: throwAsCaller(exception)
            raise

def values(*args):
    this = get_instance()
    if this.mode:
        try:
            this.validate('val', *args)
        except:
            # TODO: throwAsCaller(exception)
            raise

# Reproducible deterministic random number generation
def randn(r, c):
    this = get_instance()
    v    = np.random.standard_normal((r, c))
    if this.mode or this.unit:
        # FIXME: slow and dumb...
        for i in range(0, r):
            for j in range(0, c):
                v[i,j]    = this.state.randn[ this.idxn % this.state.randn.shape[2] ]
                this.idxn = this.idxn + 1
    return v

# Reproducible deterministic random number generation
def rand(r, c):
    this = get_instance()
    v    = np.random.random((r, c))
    if this.mode or this.unit:
        # FIXME: slow and dumb...
        for i in range(0, r):
            for j in range(0, c):
                v[i,j]    = this.state.rand[ this.idxu % this.state.rand.shape[2] ]
                this.idxu = this.idxu + 1
    return v  

# Reproducible deterministic random number generation
def randperm(n):
    this = get_instance()
    v    = randperm(n)
    if this.mode or this.unit:
        # FIXME: slow and dumb...
        raise Exception('Not implemented')

    