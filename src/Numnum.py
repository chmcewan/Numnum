import numpy as np
import numpy.matlib
import scipy as sp
import scipy.io as sio
import inspect
import pdb

singleton = None

class Numnum:
        def __init__(this):
            this.idxn  = 0
            this.idxu  = 0
            this.ids   = {}
            this.ctx   = []
            this.gid   = 0
            this.state = {}
            this.mode  = 0 
            this.unit  = 0  

        def push(this):
            """ push new context onto stack """
            name = caller(1)
            if name in this.ids:
                this.ids[name] = this.ids[name] + 1
            else:
                this.ids[name] = 1
            ctx = {}
            ctx["name"] = name
            ctx["run"]  = this.ids[name]
            this.ctx.append(ctx) 

        def pop(this):
            """ pop context off of stack """
            ctx = this.ctx.pop()
            if this.mode > 0:
                if ctx["name"] not in this.state:
                    this.state[ctx["name"]] = []
                
                runs = this.state[ctx["name"]]
                
                if ctx["run"] == len(runs)+1:
                    runs.append(ctx)
                else:
                    raise Exception("wtf: %d ~ %d" % (ctx["run"] , len(runs)))
                # this.state[ctx.name] = runs
            

        def validate(this, str, *args):
            ctx = this.ctx[-1]
            
            if this.mode > 0:
                ctx[str] = args
            else:
                funs = this.state[ctx["name"]]
                if type(funs) != list:
                    funs = [funs]
                fun  = funs[ ctx["run"] - 1 ]
                vals = fun[str]

                if len(vals) != len(args):
                    raise Exception('Incorrect number of values to validate')
                
                for i in range(0, len(args), 2):
                    key_a = args[i]
                    val_a = args[i+1]
                    key_b = vals[i]
                    val_b = vals[i+1]
                    equivalent(val_a, val_b, key_a, key_b)   
            # this.ctx{end} = ctx;



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

def str2func(name, offset=0):
    return inspect.stack()[1+offset][0].f_locals[name]
    #frame = inspect.currentframe()
    #return frame.f_back.f_back.f_locals


def get_instance():
    global singleton
    if singleton == None:
        singleton = Numnum()
    return singleton

def named_args(kv):
    v = []
    for i in range(0, len(kv), 2):
        v.append(kv[i+1])
    return v

def unnamed_args(k):
    v = []
    if type(k) == np.ndarray or type(k) == list:
        for i in range(0, len(k)):
            v.append(k[i+1])
    else:
        v.append(k)
    return v

def replay(filename, mode=0):      
    this       = get_instance()
    this.idxn  = 0
    this.idxu  = 0
    this.ids   = {}
    this.ctx   = []
    this.gid   = 0
    this.state = parse(sio.loadmat(filename, chars_as_strings=True, struct_as_record=False, squeeze_me=True))
    this.mode  = -1
    this.unit  = 1

    testname = None
    if type(mode) == str:
        testname = mode
        mode     = -1

    # run integration test
    if mode == 0 or mode > 0:
        f = str2func(this.state["numnum_function"], 1)
        v = unnamed_args(this.state["numnum_varargin"])
        f(*v)
        print("integration %s: pass" % this.state["numnum_function"])
        
    # run unit tests
    if mode == 0 or mode < 0:
        for key in this.state.keys():
            if testname and (testname != key):
                continue
            if not( key.startswith("numnum_") or key.startswith("_") ):
                runs = this.state[key]  
                f    = str2func(key, 1)
                if f == None:
                    print('Skipping %s...\n' % key)
                    continue
                             
                if type(runs) != list:
                    runs = [runs]

                passes = 0
                for j in range(0, len(runs)): 
                    run = runs[j]
                    arg = named_args(run["arg"])
                    ret = named_args(run["ret"])

                    this.mode  = 0 # disable verification in functions
                    this.unit  = 1 # keep random generation enabled
                    this.idxn  = 0 # reset random numbers
                    this.idxu  = 0
                    results    = f( *arg ) # invoke!
                    this.mode  = -1

                    try:
                        if len(ret) == 1:
                            equivalent( ret[0], results, run["ret"][0], run["ret"][0] )
                        else:
                            for k in range(0, len(ret)):
                                equivalent( ret[k], results[k], run["ret"][2*k], run["ret"][2*k] )
                        passes = passes + 1;
                    except Exception as e:
                        print(e.message)
                        pass
                
                print("unit %s: %d%% pass (%d/%d)" % (run["name"], round(passes/len(runs)*100), run["run"], len(runs) ))


def record(filename, f, *args):
    this       = get_instance()
    this.idxn  = 0
    this.idxu  = 0
    this.ids   = {}
    this.ctx   = []
    this.gid   = 0
    this.state = {}
    this.mode  = 1
    this.unit  = 0

    n = 10000
    this.state["numnum_randn"]    = np.random.standard_normal((1, n))
    this.state["numnum_rand"]     = np.random.random( (1, n) )
    this.state["numnum_function"] = "" # FIXME
    this.state["numnum_varargin"] = args

    f(*args)
    sio.savemat(filename, this.state)

def equivalent(a, b, A = "a", B = "b"):

    if type(a) != type(b):
        raise Exception("class(%s) = %s and class(%s) = %s" % (A, type(a), B, type(b)))

    if type(a) == np.ndarray: 

        # Meh. Fix up shapes
        if len(a.shape) == 1 and len(b.shape) == 2:
            if b.shape[0] == 1:
                a = a.reshape(1, a.shape[0])
            elif b.shape[1] == 1:
                a = a.reshape(a.shape[0], 1)

        if len(b.shape) == 1 and len(a.shape) == 2:
            if a.shape[0] == 1:
                b = b.reshape(1, b.shape[0])
            elif a.shape[1] == 1:
                b = b.reshape(b.shape[0], 1)

        if a.shape != b.shape:
            raise Exception("size(%s) = %dx%d and size(%s) = %dx%d" % (A, a.shape[0], a.shape[1], B, b.shape[0], b.shape[1]))
             
        delta = abs(a-b)
        chk   = delta > 1e-6   
        if chk.any():
            raise Exception("%s ~= %s (%d failed with max error of %f)" % (A, B, chk.sum(), delta.max()))
        
    elif type(a) == dict:
        return
    elif type(a) == list:
        return

def caller(offset=0):
    return inspect.stack()[2+offset][3]

def arguments(*args):
    this = get_instance()
    if this.mode:
        this.push()
        #try:
        this.validate('arg', *args)
        #except:
        #    # TODO: throwAsCaller(exception)
        #    raise

def returns(*args):
    this = get_instance()
    if this.mode:
        #try:
        this.validate('ret', *args)
        this.pop()
        #except:
        #    # TODO: throwAsCaller(exception)
        #    raise

def values(*args):
    this = get_instance()
    if this.mode:
        #try:
        this.validate('val', *args)
        #except:
        #    # TODO: throwAsCaller(exception)
        #    raise

# Reproducible deterministic random number generation
def randn(r, c):
    this = get_instance()
    v    = np.random.standard_normal((r, c))
    if this.mode or this.unit:
        # FIXME: slow and dumb...
        for i in range(0, r):
            for j in range(0, c):
                v[i,j]    = this.state["numnum_randn"][ this.idxn % this.state["numnum_randn"].shape[0] ]
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
                v[i,j]    = this.state["numnum_rand"][ this.idxu % this.state["numnum_rand"].shape[0] ]
                this.idxu = this.idxu + 1
    return v  

# Reproducible deterministic random number generation
def randperm(n):
    this = get_instance()
    v    = randperm(n)
    if this.mode or this.unit:
        # FIXME: slow and dumb...
        raise Exception('Not implemented')

    