#! /usr/bin/env python
"""
Creates waterfall plots from Miriad UV files.  Can tile multiple plots
on one window, or plot just a single baseline.  When taking the delay
transform (-d), channels are interepreted as selecting delays after the
the transform operation.  Similarly, the time select (-t) will be interpreted
as selecting fringe rates if the fringe-rate transform (-f) has been selected.
In both cases, the ranges specified are intepreted to be the units of the
output plot (i.e. as specified by --chan_axis and --time_axis).

Author: Aaron Parsons, Griffin Foster
some frankensteining by: Danny Jacobs
"""

import aipy as a, numpy as n, pylab as p, math, sys, optparse
from types import * 


o = optparse.OptionParser()
o.set_usage('plot_stokes.py [options] *.uv')
o.set_description(__doc__)
a.scripting.add_standard_options(o, ant=True, chan=True, dec=True,
    cmap=True, max=True, drng=True)
o.add_option('--stokes',dest='stokes',default='I',
             help="""Stokes parameter, can be one of I,Q,U,V,chi,f [default=I] """)
o.add_option('-m', '--mode', dest='mode', default='log',
    help='Plot mode can be log (logrithmic), lin (linear), phs (phase), real, or imag.')
o.add_option('--sum_chan', dest='sum_chan', action='store_true',
    help='Sum active channels together.')
o.add_option('-t', '--time', dest='time', default='all', help='Select which time sample to plot. Options are: "all" (default), "<time1 #>_<time2 #>" (a range of times to plot), or "<time1 #>,<time2 #>" (a list of times to plot). If "all" or a range are selected, a 2-d image will be plotted. If a list of times is selected an xy plot will be generated.')
o.add_option('-u', '--unmask', dest='unmask', action='store_true',
    help='Plot masked data, too.')
o.add_option('-d', '--delay', dest='delay', action='store_true',
    help='Take FFT of frequency axis to go to delay (t) space.')
o.add_option('-f', '--fringe', dest='fringe', action='store_true',
    help='Take FFT of time axis to go to fringe (Hz) space.')
o.add_option('--dt', dest='dt', action='store_true',
    help='Remove a linear extrapolation from adjacent times.')
o.add_option('--df', dest='df', action='store_true',
    help='Remove a linear extrapolation from adjacent frequency channels.')
o.add_option('-o', '--out_file', dest='out_file', default='',
    help='If provided, will save the figure to the specified file instead of popping up a window.')
o.add_option('--time_axis', dest='time_axis', default='index',
    help='Choose time axis to be integration/fringe index (index), or physical coordinates (physical), or if doing xy plot in time-mode, (lst) is also available.  Default is index.')
o.add_option('--chan_axis', dest='chan_axis', default='index',
    help='Choose channel axis to be channel/delay index (index), or physical coordinates (physical).  Default is index.')
o.add_option('--clean', dest='clean', type='float',
    help='Deconvolve delay-domain data by the "beam response" that results from flagged data.  Specify a tolerance for termination (usually 1e-2 or 1e-3).')
o.add_option('--nolegend', dest='nolegend', action='store_true',
    help='Omit legend in last plot.')

def convert_arg_range(arg):
    """Split apart command-line lists/ranges into a list of numbers."""
    arg = arg.split(',')
    return [map(float, option.split('_')) for option in arg]

def gen_chans(chanopt, uv, coords, is_delay):
    """Return an array of active channels and whether or not a range of
    channels is selected (as opposed to one or more individual channels)
    based on command-line arguments."""
    is_chan_range = True
    if chanopt == 'all': chans = n.arange(uv['nchan'])
    else:
        chanopt = convert_arg_range(chanopt)
        if coords != 'index':
            if is_delay:
                def conv(c):
                    return int(n.round(c * uv['sdf'] * uv['nchan'])) \
                        + uv['nchan']/2
            else:
                def conv(c): return int(n.round((c - uv['sfreq']) / uv['sdf']))
        else:
            if is_delay:
                def conv(c): return int(c) + uv['nchan']/2
            else:
                def conv(c): return c
        chanopt = [map(conv, c) for c in chanopt]
        if len(chanopt[0]) != 1: 
            chanopt = [n.arange(x,y, dtype=n.int) for x,y in chanopt]
        else: is_chan_range = False
        chans = n.concatenate(chanopt)
    return chans.astype(n.int), is_chan_range

def gen_times(timeopt, uv, coords, decimate, is_fringe):
    is_time_range = True
    if timeopt == 'all' or is_fringe:
        def time_selector(t, cnt): return True
    else:
        timeopt = convert_arg_range(timeopt)
        if len(timeopt[0]) != 1:
            def time_selector(t, cnt):
                if coords == 'index': t = cnt
                for opt in timeopt:
                    if (t >= opt[0]) and (t < opt[1]): return True
                return False
        else:
            is_time_range = False
            timeopt = [opt[0] for opt in timeopt]
            inttime = uv['inttime'] / a.const.s_per_day * decimate
            def time_selector(t, cnt):
                if coords == 'index': return cnt in timeopt
                for opt in timeopt:
                    if (t >= opt) and (t < opt + inttime): return True
                return False
    return time_selector, is_time_range

opts, args = o.parse_args(sys.argv[1:])

# Parse command-line options
cmap = p.get_cmap(opts.cmap)
uv = a.miriad.UV(args[0])
a.scripting.uv_selector(uv,opts.ant,'yy')
chans, is_chan_range = gen_chans(opts.chan, uv, opts.chan_axis, opts.delay)
freqs = n.arange(uv['sfreq'], uv['sfreq']+uv['nchan']*uv['sdf'], uv['sdf'])
freqs = freqs.take(chans)
delays = n.arange(-.5/uv['sdf'], .5/uv['sdf'], 1/(uv['sdf']*uv['nchan']))
delays = delays.take(chans)
time_sel, is_time_range = gen_times(opts.time, uv, opts.time_axis, 
    opts.decimate, opts.fringe)
inttime = uv['inttime'] * opts.decimate
nants = uv['nants']
del(uv)

# Loop through UV files collecting relevant data
plot_x = {}
plot_t = {'jd':[], 'lst':[], 'cnt':[]}
times = []
if opts.stokes=='I' or opts.stokes=='Q':
    pols = ['xx','yy']
elif opts.stokes in ['f','chi']:
    pols = ['xx','yy','xy','yx']
elif opts.stokes in ['U','V']:
    pols = ['xy','yx']
else:
    pols = []
    ants = a.scripting.parse_ants(opts.ant,nants)
    for ant in ants:
        if ant[2]!=-1: pols.append(ant[2])

#print "pols = ", pols
bl_pols = []    
for uvfile in args:
    print 'Reading', uvfile
    uv = a.miriad.UV(uvfile)
    # Only select data that is needed to plot
    for pol in pols:
        a.scripting.uv_selector(uv, opts.ant, pol)
    # Read data from a single UV file
    for (uvw,t,(i,j)),d in uv.all():
        bl = '%d,%d' % (i,j)
        pol = a.miriad.pol2str[uv['pol']]
        #print bl,pol
        if not (bl,pol) in bl_pols: bl_pols.append((bl,pol))
        # Implement Decimation
        if len(times) == 0 or times[-1] != t:
            times.append(t)
            use_this_time = ((len(times) - 1) % opts.decimate) == 0
            use_this_time &= time_sel(t, (len(times)-1) / opts.decimate)
            if use_this_time:
                plot_t['lst'].append(uv['lst']*12/n.pi)
                plot_t['jd'].append(t)
                plot_t['cnt'].append((len(times)-1) / opts.decimate)
        if not use_this_time: continue
        # Do delay transform if required
        if opts.delay:
            if opts.unmask:
                d = d.data
                ker = n.zeros_like(d)
                ker[0] = 1.
                gain = 1.
            else:
                flags = n.logical_not(d.mask).astype(n.float)
                gain = n.sqrt(n.average(flags**2))
                ker = n.fft.ifft(flags)
                d = d.filled(0)
            d = n.fft.ifft(d)
            if not opts.clean is None and not n.all(d == 0):
                d, info = a.deconv.clean(d, ker, tol=opts.clean)
                d += info['res'] / gain
            d = n.ma.array(d)
            d = n.ma.concatenate([d[d.shape[0]/2:], d[:d.shape[0]/2]], 
                axis=0)
        elif opts.unmask: d = d.data
        # Extract specific channels for plotting
        d = d.take(chans)
        d.shape = (1,) + d.shape
        if not plot_x.has_key(bl): plot_x[bl] = dict(zip(pols,[[],[],[],[]]))
        plot_x[bl][pol].append(d)
    del(uv)

bls = plot_x.keys()
def bl_sort_func(a, b):
    ai,aj = map(int, a.split(','))
    bi,bj = map(int, b.split(','))
    if bi > ai or (bi == ai and bj > aj): return -1
    return 1
bls.sort(cmp=bl_sort_func)
if len(bls) == 0:
    print 'No data to plot.'
    sys.exit(0)


def bl_pol_sort_func(a, b):
    ai,aj = map(int, a[0].split(','))
    bi,bj = map(int, b[0].split(','))
    if bi > ai or (bi == ai and bj > aj): return -1
    return 1
bl_pols.sort(cmp=bl_pol_sort_func)

if opts.stokes in ['I','Q','U','V','chi','f']: 
    bl_pols = list(set([bl[0] for bl in bl_pols]))
m2 = int(math.sqrt(len(bls)))
m1 = int(math.ceil(float(len(bls)) / m2))
# Generate all the plots
#print "bl_pols", bl_pols

for cnt, bl in enumerate(bls):
#    if type(bl_pol)==ListType: bl = bl_pol[0]
#    else: bl = bl_pol
    if opts.stokes in ['I','f']:
        Ibls = n.ma.array([plot_x[bl][pol] for pol in ['xx','yy']]).squeeze()
        I = n.sum(Ibls,axis=0)
        d=I
    if opts.stokes in ['Q','f','chi']:
        Qbls = n.ma.array([plot_x[bl][pol] for pol in ['xx','yy']]).squeeze()
        Q =  n.diff(Qbls,axis=0).squeeze()
        d=Q
    if opts.stokes in ['V','f']:
        Vbls = n.ma.array([plot_x[bl][pol] for pol in ['xy','yx']]).squeeze()
        if bl.split(',')[0]==bl.split(',')[1]:
            V = 2*Vbls[0,:].imag
            V.shape = V.shape + (1,)
        else:
            V =  n.diff(Vbls,axis=0).squeeze()
            V /= n.complex(0,1)
        d=V
    if opts.stokes in ['U','f','chi']:
        Ubls = n.ma.array([plot_x[bl][pol] for pol in ['xy','yx']]).squeeze()
        if bl.split(',')[0]==bl.split(',')[1]:
            U = 2*Ubls[0,:].real
        else:
            U = n.diff(Ubls,axis=0).squeeze()
        d=U
    if opts.stokes=='f':
#        Q.shape = Q.shape[:-1]
#        U.shape = U.shape[:-1]
        d = n.sqrt(n.ma.absolute(V)**2+n.ma.absolute(Q)**2+n.ma.absolute(U)**2)/n.ma.absolute(I)
        d.shape = d.shape + (1,)
    #d = n.ma.concatenate(plot_x[bl], axis=0)
    print d.shape
    if len(d.shape)<2: d.shape = d.shape + (1,)
    if len(d.shape)>2: d = d.squeeze()
    print d.shape
    if opts.df: d = d[:,:-2]/2 + d[:,2:]/2 - d[:,1:-1]
    if opts.dt: d = d[:-2]/2 + d[2:]/2 - d[1:-1]
    if opts.fringe:
        d = d.filled(0)
        flags = n.where(d[:,0] != 0, 1., 0.)
        gain = n.sqrt(n.average(flags**2))
        ker = n.fft.ifft(flags)
        d = n.fft.ifft(d, axis=0)
        if not opts.clean is None:
            for chan in range(d.shape[1]):
                d[:,chan],info = a.deconv.clean(d[:,chan],ker,tol=opts.clean)
                d[:,chan] += info['res'] / gain
        d = n.ma.concatenate([d[d.shape[0]/2:], d[:d.shape[0]/2]], axis=0)
    #print d.shape
    if opts.sum_chan:
        d = d.sum(axis=1)
        is_chan_range = False
    if opts.mode.startswith('phs'): d = n.angle(d.filled(0))
    elif opts.mode.startswith('lin'): d = n.ma.absolute(d)
    elif opts.mode.startswith('real'): d = d.real
    elif opts.mode.startswith('imag'): d = d.imag
    elif opts.mode.startswith('log'):
        d = n.ma.absolute(d.filled(0))
        d = n.ma.masked_less_equal(d, 0)
        d = n.ma.log10(d)
    else: raise ValueError('Unrecognized plot mode.')
    p.subplot(m2, m1, cnt+1)
    if is_chan_range and is_time_range:
        if opts.fringe:
            if opts.time_axis == 'index':
                if opts.time != 'all':
                    t1, t2 = map(float, opts.time.split('_'))
                    d = d[t1+d.shape[0]/2:t2+d.shape[0]/2]
                else:
                    t1 = len(plot_t['jd'])/2 - len(plot_t['jd'])
                    t2 = len(plot_t['jd'])/2
                ylabel = 'Delay-Rate (bins)'
            else:
                t1 = -500/inttime
                t2 =  500/inttime - 1000 / (inttime * len(plot_t['jd']))
                ylabel = 'Delay-Rate (milliHz)'
        else:
            if opts.time_axis == 'index':
                t1,t2 = plot_t['cnt'][0], plot_t['cnt'][-1]
                ylabel = 'Time (integrations)'
            else:
                t1,t2 = plot_t['jd'][0], plot_t['jd'][-1]
                ylabel = 'Time (Julian Date)'
        if opts.delay:
            if opts.chan_axis == 'index':
                c1,c2 = len(chans)/2 - len(chans), len(chans)/2
                xlabel = 'Delay (bins)'
            else:
                c1,c2 = delays[0], delays[-1]
                xlabel = 'Delay (ns)'
        else:
            if opts.chan_axis == 'index':
                c1,c2 = 0, len(chans) - 1
                xlabel = 'Frequency (chan)'
            else:
                c1,c2 = freqs[0], freqs[-1]
                xlabel = 'Frequency (GHz)'
        if not opts.max is None: max = opts.max
        else: max = d.max()
        if not opts.drng is None: min = max - opts.drng
        else: min = d.min()
        p.imshow(d, extent=(c1,c2,t2,t1), aspect='auto', 
            vmax=max, vmin=min, cmap=cmap)
        p.colorbar()
        p.xlabel(xlabel); p.ylabel(ylabel)
    elif is_chan_range and not is_time_range:
        if opts.delay:
            if opts.chan_axis == 'index':
                plot_chans = range(len(chans)/2 - len(chans), len(chans)/2)
                xlabel = 'Delay (bins)'
            else:
                plot_chans = delays
                xlabel = 'Delay (ns)'
        else:
            if opts.chan_axis == 'index':
                plot_chans = chans
                xlabel = 'Frequency (chan)'
            else:
                plot_chans = freqs
                xlabel = 'Frequency (GHz)'
        if cnt == 0:
            if opts.time_axis == 'index':
                plot_t = plot_t['cnt']
                label = '#%d'
            else:
                plot_t = plot_t['jd']
                label = 'jd%f'
        for i,t in enumerate(plot_t):
            try: p.plot(plot_chans, d[i,:], '-', label=label % t)
            except(ValueError): print "ValueError with data in shape:", d.shape
        p.xlabel(xlabel)
        if not opts.max is None: max = opts.max
        else: max = d.max()
        if not opts.drng is None: min = max - opts.drng
        else: min = d.min()
        p.ylim(min,max)
    elif not is_chan_range and is_time_range:
        if opts.time_axis == 'index': plot_times = range(len(plot_t['jd']))
        elif opts.time_axis == 'physical': plot_times = plot_t['jd']
        elif opts.time_axis == 'lst': plot_times = plot_t['lst']
        else: raise ValueError('Unrecognized time axis type.')
        if opts.sum_chan: p.plot(plot_times, d, '-', label='(+)')
        else:
            if opts.chan_axis == 'index': label = '#%d'
            else:
                chans = freqs
                label = '%f GHz'
            for c, chan in enumerate(chans):
                print "single channel"
                p.plot(plot_times, d[:,c], '-', label=label % chan)
        if not opts.max is None: max = opts.max
        else: max = d.max()
        if not opts.drng is None: min = max - opts.drng
        else: min = d.min()
        p.ylim(min,max)
    else: raise ValueError('Either time or chan needs to be a range.')
    if opts.stokes!='Vis': p.title(bl+" "+opts.stokes)
    else: p.title
if not opts.nolegend and (not is_time_range or not is_chan_range): 
    p.legend(loc='best')

# Save to a file or pop up a window
if opts.out_file != '': p.savefig(opts.out_file)
else: p.show()
