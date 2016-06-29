import numpy as np
import numpy.matlib
import scipy as sp
import scipy.io as sio
import inspect
import pdb
from numbers import Number

import warnings
import pdb

singleton = None

class Result:
    def __init__(this, name, passes=0, total=0):
        this.name   = name
        this.passes = float(passes)
        this.total  = float(total)

    def __iadd__(this, that):
        this.passes = this.passes + that.passes
        this.total  = this.total  + that.total
        return this

    def passed(this):
        return this.passes == this.total

    def __repr__(this):
        fr = 0.0
        if this.total > 0:
            fr = this.passes / this.total
        return "%s: %d%% pass (%d/%d)" % (this.name, round(fr*100.0), this.passes, this.total )


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
            this.run   = None
            this.depth = 0

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
                this._validate(vals, *args)
            # this.ctx{end} = ctx;

        def _validate(this, vals, *args):
                if len(vals) != len(args):
                    warnings.warn("Unequal number of values: %d != %d" % (len(vals)/2, len(args)/2), stacklevel=3)
                # Assume lost trailing arguments are optional
                for i in range(0, min(len(args), len(vals)), 2):
                    key_a = args[i]
                    val_a = args[i+1]
                    key_b = vals[i]
                    val_b = vals[i+1]
                    equivalent(val_a, val_b, key_a, key_b)   
            


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
    scope = inspect.stack()[1+offset][0].f_globals
    if name in scope:
        return scope[name]
    else:
        for s in scope:
            if inspect.ismodule(scope[s]):
                # print("str2func recursing into '%s'" % s)
                for m in inspect.getmembers(scope[s]):
                    if m[0] == name:
                        return m[1]    


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
    this.run   = None
    this.depth = 0

    testname = None
    if type(mode) == str:
        testname = mode
        mode     = -1

    # print(filename)

    test_results = {}

    # run integration test
    if mode == 0 or mode > 0:
        f = str2func(this.state["numnum_function"], 1)
        v = unnamed_args(this.state["numnum_varargin"])
        f(*v)
        print("integration %s: pass" % this.state["numnum_function"])
        
    # run unit tests
    if mode == 0 or mode < 0:
        total_tests = 0
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

                    this.mode  = 0      # disable verification in functions...
                    this.run   = run    # ...except top-level
                    this.depth = 0      
                    this.unit  = 1      # keep random generation enabled
                    this.idxn  = 0      # reset random numbers
                    this.idxu  = 0

                    try:
                        # Invoke. Return values validated internally.
                        f( *arg )
                        passes  = passes + 1
                    except Exception as e:
                        print(e.message)
                        pass
                        #raise

                    this.mode  = -1
                    this.run   = None
                    this.depth = 0

                    #total_tests = total_tests + 1
                    #try:
                    #    if len(ret) == 1:
                    #        equivalent( ret[0], results, run["ret"][0], run["ret"][0] )
                    #    else:
                    #        for k in range(0, len(ret)):
                    #            equivalent( ret[k], results[k], run["ret"][2*k], run["ret"][2*k] )
                    #    passes = passes + 1;
                    #except Exception as e:
                    #    print(e.message)
                    #    pass
                
                #errstr= "%s: %d%% pass (%d/%d)" % (run["name"], round(float(passes)/float(len(runs))*100.0), passes, len(runs) )
                #print(errstr)
                #if passes != len(runs):
                #    raise Exception(errstr)
                #assert passes == len(runs)

                test_results[key] = Result( key, passes, len(runs) )

        #if total_tests == 0:
        #    raise Exception("No unit tests found");
    return test_results

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
    this.run   = None
    this.depth = 0

    n = 10000
    this.state["numnum_randn"]    = np.random.standard_normal((1, n))
    this.state["numnum_rand"]     = np.random.random( (1, n) )
    this.state["numnum_function"] = "" # FIXME
    this.state["numnum_varargin"] = args

    f(*args)
    sio.savemat(filename, this.state)
   
def caller(offset=0):
    return inspect.stack()[2+offset][3]

def arguments(*args):
    this = get_instance()
    this.depth = this.depth + 1

    if this.mode:
        this.push()
        this.validate('arg', *args)
    elif this.run and this.depth == 1:
        this._validate(this.run['arg'], *args)

def returns(*args):
    this = get_instance()
    this.depth = this.depth - 1

    if this.mode:
        this.validate('ret', *args)
        this.pop()
    elif this.run and this.depth == 0:
        this._validate(this.run['ret'], *args)

def values(*args):
    this = get_instance()
    if this.mode:
        this.validate('val', *args)
    elif this.run and this.depth == 1:
        this._validate(this.run['val'], *args)

# Reproducible deterministic random number generation
def randn(r, c):
    this = get_instance()
    v    = np.random.standard_normal((r, c))
    if this.mode or this.unit:
        idx = 0 # needs to be deterministic for unit tests
        for i in range(0, r):
            for j in range(0, c):
                v[i,j] = this.state["numnum_randn"][ idx % this.state["numnum_randn"].shape[0] ]
                idx    = idx + 1
    return v

# Reproducible deterministic random number generation
def rand(r, c):
    this = get_instance()
    v    = np.random.random((r, c))
    if this.mode or this.unit:
        idx = 0 # needs to be deterministic for unit tests
        for i in range(0, r):
            for j in range(0, c):
                v[i,j] = this.state["numnum_rand"][ idx % this.state["numnum_rand"].shape[0] ]
                idx    = idx + 1
    return v  

# Reproducible deterministic random number generation
def randperm(n):
    this = get_instance()
    v    = randperm(n)
    if this.mode or this.unit:
        # FIXME: slow and dumb...
        raise Exception('Not implemented')

 
# Fix handling of 1d ndarrays
def insist(v, rows, cols):
    if rows == 0 and cols == 0:
        raise Exception("Both rows and cols connot be zero")
    
    if type(v) == float:
        v = np.ones(shape=(1,1), dtype=np.float64) * v

    if type(v) == int:
        v = np.ones(shape=(1,1), dtype=np.float64) * float(v)

    if rows == 0:
        rows = v.size / cols
    if cols == 0:
        cols = v.size / rows

    if v.ndim == 1:
        v = v.reshape( ( rows  , cols) )

    # TODO: is this ever desirable?    
    elif (v.shape[0] != v.shape[1]) and v.shape[0] == cols and v.shape[1] == rows:
        warnings.warn("Implicit use of transpose")
        v = v.T

    assert v.shape[1] == cols    
    assert v.shape[0] == rows       
    return v

def equivalent(a, b, A = "a", B = "b"):

    olda = a
    oldb = b

    if type(a) == type(None):
        warnings.warn("Ignoring null (return?) value for '%s'" % A)
        return

    if isinstance(a,np.bool_) and not isinstance(b,np.bool_):
        if a:
            a = 1
        else:
            a = 0
            
    if isinstance(a,Number):
        a = np.ones( (1,1) ).reshape((1,1)) * float(a)

    if isinstance(b,Number):
        b = np.ones( (1,1) ).reshape((1,1)) * float(b)

    if type(a) != type(b):
        # check if scalar before complaining
        if type(a) == np.ndarray and len(a.shape):   
            if a.shape[0] == 1:
                if len(a.shape) == 1:
                    a0 = a[0]
                else:
                    a0 = a[0,0]
                if float(a0) == float(b):
                    return
        elif type(a) == list and type(b) == np.ndarray:
            pass
        elif isinstance(a,Number) and type(b) == np.ndarray:
            # Compare a scalar with an array: start by converting
            # a to a length-1 list
            a = [a]
        else:
            raise Exception("class(%s) = %s and class(%s) = %s" % (A, type(a), B, type(b)))

    if type(a) == np.ndarray: 

        # Meh. Fix up shapes
        if len(a.shape) == 1 and len(b.shape) == 2:
            if b.shape[0] == 1:
                a = a.reshape( (1, a.shape[0]) )
            elif b.shape[1] == 1:
                a = a.reshape( (a.shape[0], 1) )

        if len(b.shape) == 1 and len(a.shape) == 2:
            if a.shape[0] == 1:
                b = b.reshape( (1, b.shape[0]) )
            elif a.shape[1] == 1:
                b = b.reshape( (b.shape[0], 1) )

        if len(a.shape) == 1 and len(b.shape) == 1:
            a = a.reshape( (a.shape[0], 1) )
            b = b.reshape( (b.shape[0], 1) )

        if b.shape[1] == 0:
            pdb.set_trace()
            b = np.ones((1,1)).resize((1,1)) * float(b)

        if a.shape != b.shape:
            raise Exception("size(%s) = %dx%d and size(%s) = %dx%d" % (A, a.shape[0], a.shape[1], B, b.shape[0], b.shape[1]))

        delta = np.abs(a-b)
        chk   = delta > 1e-6   
        if chk.any():
            errstr = "%s ~= %s\n%s\n%s" % (A, B, str(a), str(b))
            raise Exception(errstr)
        
    elif type(a) == dict:
        for k in a.keys():
            equivalent(a[k], b[k], A = "%s.%s" % (A, k), B = "%s.%s" % (B, k))
    elif type(a) == list:
        if len(a) != len(b):
            raise Exception("len(%s) = %i and len(%s) = %i" % (A, len(a), B, len(b)))        
        for i in range(0, min(len(a), len(b))):
            equivalent(a[i], b[i], A = "%s[%d]" % (A, i), B = "%s[%s]" % (B, i))

    raise Exception("Cannot check equivalence of %s (%s) and %s (%s)" % (A, type(a), B, type(b) ))
    