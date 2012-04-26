''' This is a calibration file for data collected at PAPER in Karoo, South Africa
on JD 2455742 '''

import aipy as a, numpy as n,glob,ephem
import bm_prms as bm
import generic_catalog
import logging
loglevel = logging.CRITICAL
logging.basicConfig(level=loglevel)
log = logging.getLogger('psa_null')
log.setLevel(loglevel)

prms = {
    'loc': ('-30:43:17.5', '21:25:41.9'), # KAT, SA (GPS)
    'antpos':{
        0:[147.659407413, 336.269469733, 264.566180759],
        1:[-120.566931266, -270.142735412, -201.208899961],
        2:[175.483874,-282.046474,309.593714],
        3:[-24.5939776529, -369.022493234, -35.9049669793],
        #--------------------------------------------------------
        4:[-135.977107,-65.373043,-223.715356],
        5:[-184.222167454,  60.9256169154, -307.675312464],
        7:[84.568610,-397.906007,151.703088],
        6:[60.9037241018, 422.222408268, 116.124879563],
        #--------------------------------------------------------
        8:[148.405177,-231.475974,263.305593],
        9:[-151.30695,-328.29684,-185.60087],
        10:[-28.800063,-420.849441,-43.564604],
        #11:[-180.112865,-190.297251,-301.062917],
        11:[-178.169736505,-185.482180584,-315.619611243],
        #--------------------------------------------------------
        12:[161.032208592, 207.530151484, 286.703007713],
        13:[-79.830818,266.416356,-122.828467],
        14:[90.491568,406.666552,171.303074],
        15:[136.833937217,-349.10409, 256.16691],
        #========================================================
	    16:[75.008275,-366.663944,135.807286],
        17:[-170.082246,113.392564,-280.090332],
        18:[-173.308984588, -52.5844630491, -289.495946419],
        19:[35.6156894023, -76.4247822222, 68.8003235664],
        #-------------------------------------------------------
        20:[ 223.405495506, -111.371927382, 391.352958368],
        21:[ 211.984088554, -181.820834933, 372.672243377],
        22:[-52.9274701935, -409.284993158, -84.1268196632],
        23:[-75.327786,379.129646,-113.829018],
        #--------------------------------------------------------
        24:[-90.374808,3.548977,-144.207995],
        25:[-23.653561,-153.921245,-31.289596],
        26:[208.418197,189.287085,370.725255],
        27:[-22.2282015089, 311.926612877, -26.8228657991],
        #--------------------------------------------------------
        28:[-18.1453146192, 166.083642242, -21.2052534495],
        29:[89.6597220746, -22.1294190136, 162.698139384],
        30:[-139.053365,312.917932,-223.870462],
        31:[229.945829,48.161862,406.414507],
        #--------------------------------------------------------
        32:[-112.893563,109.228967,-182.880941],
        33:[121.355347,-319.429590,209.575748],
        34:[-1.186004,298.790781,-1.572735],
        35:[-150.754218,-224.460782,-258.594058],
        #--------------------------------------------------------
        36:[-148.166345,285.390149,-254.152706],
        37:[73.704070,-378.161280,127.753480],
        38:[183.238623,145.046381,314.997386],
        39:[201.110057,270.608943,345.388038],
        #--------------------------------------------------------
        40:[-187.753175,101.634584,-322.330703],
        41:[32.859445,-311.361270,57.492402],
        42:[111.791791,-360.752264,193.124569],
        43:[185.296482,12.473870,318.948404],
        #--------------------------------------------------------
        44:[66.840886,269.989165,115.139909],
        45:[208.327549,-181.024029,358.713760],
        46:[222.401981,114.559981,382.329808],
        47:[82.998742,-157.005822,143.375763],
        #-------------------------------------------------------
        48:[-123.364050,7.568406,-211.391982],
        49:[42.324815,-394.596554,73.800150],
        50:[155.428104,103.981800,267.545140],
        51:[4.002712,454.858259,7.086482],
        #-------------------------------------------------------
        52:[40.840441,382.998141,70.689703],
        53:[228.948582,78.038958,393.662509],
        54:[208.232148,171.396294,357.761446],
        55:[22.162702,221.120016,38.449461],
        #--------------------------------------------------------
        56:[-85.962903,360.456826,-147.018238],
        57:[-22.182170,447.517664,-37.585541],
        58:[-40.132905,-349.207661,-68.174661],
        59:[-38.864384,362.866457,-66.270033],
        #--------------------------------------------------------
        60:[134.062901,401.074665,230.468279],
        61:[-81.496611,-277.174777,-139.301327],
        62:[-161.608043,226.512058,-277.243397],
        63:[170.275635,-299.764724,293.554481],
    },    
    'twist': n.array([.1746] * 64),
}

def get_aa(freqs):
    '''Return the AntennaArray to be used for simulation.'''
    location = prms['loc']
    antennas = []
    nants = len(prms['antpos'])
    for pi in ('x','y'):
        for i in prms['antpos'].keys():
            beam = bm.prms['beam'](freqs,nside=32,lmax=20,mmax=20,deg=7)
            #beam = a.fit.Beam2DGaussian(freqs, xwidth=45*n.pi/180, ywidth=45*n.pi/180)
            try: beam.set_params(bm.prms['bm_prms'])
            except(AttributeError): pass
            pos = prms['antpos'][i]
            dly = 0.
            off = 0. 
            amp =  1. 
            twist = prms['twist'][i]
            bp_r =  n.array([1])
            bp_i = n.array([0])
            twist = prms['twist'][i]
            #if pi == 'y': twist += n.pi/2.
            antennas.append(
                a.pol.Antenna(pos[0],pos[1],pos[2],  beam, num=i, pol=pi,phsoff=[dly,off],
                amp=amp, bp_r=bp_r, bp_i=bp_i, pointing=(0.,n.pi/2,twist),
                lat=prms['loc'][0])
            )
    aa = a.pol.AntennaArray(prms['loc'], antennas)
    return aa

src_prms = {
    #'cyg':{ 'jys':10**4.038797, 'index': -0.712972, },
    #'cas': {
    #    'a1':.00087, 'a2':.00064, 'th':0,
    #    'jys':10**4.047758, 'index': -1.169779,
    #    #'jys':11334.8238655,'index': -1.254381,
    #},
    'Sun': {
        'ra':0,'dec':0,'jys': 37320, 'index':2.08, 'a1':.00540, 'a2':.00490, 'th':0,
    },
    #'vir':{ 'jys':10**3.056388, 'index':  -1.457298 , },
    #'crab':{ 'jys':10**3.172870, 'index':  -0.837350 , },
#    'her':{ 'jys':10**2.599899, 'index':  -1.345695 , },
#    'hyd':{ 'jys':10**2.474107, 'index':  0.668695 , },
    'J0030+636':{ 'jys':10**0.191821, 'index':  2.887518 , },
    'J0043+520':{ 'jys':10**1.736237, 'index':  -0.563678 , },
    'J0056+262':{ 'jys':10**1.475688, 'index':  -0.390762 , },
    'J0109+132':{ 'jys':10**2.254138, 'index':  -1.267875 , },
    'J0136+206':{ 'jys':10**1.841271, 'index':  -0.854255 , },
    'J0138+331':{ 'jys':10**1.886556, 'index':  -0.370976 , },
    'J0157+285':{ 'jys':10**1.594649, 'index':  -0.773429 , },
    'J022212+430439':{ 'ra':'02:22:12.8', 'dec':'43:04:40',
                       'jys':10**1.574161, 'index':  -0.251043 , },
    'J0224+400':{ 'jys':10**0.689736, 'index':  1.318209 , },
    'J0238+591':{ 'jys':10**1.941454, 'index':  -1.836028 , },
    'J0310+171':{ 'jys':10**2.316485, 'index':  -2.375518 , },
    'J0320+413':{ 'jys':10**2.305994, 'index':  -1.436542 , },
    'J0327+552':{ 'jys':10**1.874233, 'index':  -1.324181 , },
    'J0359+103':{ 'jys':10**2.303049, 'index':  -1.870490 , },
    'J0408+430':{ 'jys':10**1.583597, 'index':  -0.436948 , },
    'J0414+111':{ 'jys':10**2.125283, 'index':  -2.383826 , },
    'J0418+380':{ 'jys':10**1.949744, 'index':  -0.566860 , },
    'J0437+294':{ 'jys':10**2.302792, 'index':  -0.218577 , },
    'J0453+313':{ 'jys':10**0.983521, 'index':  0.298799 , },
    'J0505+381':{ 'jys':10**2.086846, 'index':  -0.886797 , },
    'J0543+495':{ 'jys':10**1.634059, 'index':  0.419328 , },
    'J0655+541':{ 'jys':10**1.600191, 'index':  -0.832907 , },
    'J0814+481':{ 'jys':10**1.937615, 'index':  -0.289667 , },
    'J0921+454':{ 'jys':10**1.954430, 'index':  -1.026192 , },
    'J1002+285':{ 'jys':10**1.839322, 'index':  -0.928357 , },
    'J1034+581':{ 'jys':10**1.876009, 'index':  -1.610446 , },
    'J1115+404':{ 'jys':10**1.676975, 'index':  -1.162291 , },
    'J1143+221':{ 'jys':10**1.228729, 'index':  -0.267581 , },
    'J1145+313':{ 'jys':10**1.579171, 'index':  -1.056825 , },
    'J1225+125':{ 'jys':10**2.088954, 'index':  -5.055916 , },
    'J1229+020':{ 'jys':10**1.545973, 'index':  -0.060202 , },
    'J1257+472':{ 'jys':10**1.688368, 'index':  -1.129730 , },
    'J1331+251':{ 'jys':10**1.164162, 'index':  -0.220057 , },
    'J1331+303':{ 'jys':10**1.264128, 'index':  -0.021652 , },
    'J1339+385':{ 'jys':10**1.814529, 'index':  -1.959537 , },
    'J1411+521':{ 'jys':10**2.202616, 'index':  -1.136220 , },
    'J1419+063':{ 'jys':10**1.874051, 'index':  -0.654386 , },
    'J1423+194':{ 'jys':10**1.888458, 'index':  -1.792000 , },
    'J1449+632':{ 'jys':10**1.501942, 'index':  -1.096659 , },
    'J1505+260':{ 'jys':10**2.332983, 'index':  -1.690497 , },
    'J1514+261':{ 'jys':10**1.960809, 'index':  -1.863940 , },
    'J1517+070':{ 'jys':10**2.419419, 'index':  -2.066530 , },
    'J1524+543':{ 'jys':10**1.808875, 'index':  -1.846134 , },
    'J1535+554':{ 'jys':10**1.883996, 'index':  -2.520915 , },
    'J1550+624':{ 'jys':10**1.662471, 'index':  -1.324136 , },
    'J1610+656':{ 'jys':10**1.692072, 'index':  -0.835076 , },
    'J1629+393':{ 'jys':10**2.041014, 'index':  -1.069688 , },
    'J1629+442':{ 'jys':10**1.495836, 'index':  -1.080520 , },
    'J1659+470':{ 'jys':10**1.452768, 'index':  -0.866724 , },
    'J1721-006':{ 'jys':10**2.552949, 'index':  -0.478135 , },
    'J1724+506':{ 'jys':10**0.947480, 'index':  0.396705 , },
    'J1830+484':{ 'jys':10**1.675920, 'index':  0.230683 , },
    'J1835+324':{ 'jys':10**1.485494, 'index':  -0.418048 , },
    'J1844+453':{ 'jys':10**1.550063, 'index':  -0.683977 , },
    'J1846+095':{ 'jys':10**1.835401, 'index':  -1.426348 , },
    'J1940+604':{ 'jys':10**1.550293, 'index':  -0.782578 , },
    'J2014+233':{ 'jys':10**1.983872, 'index':  -0.056478 , },
    'J2020+294':{ 'jys':10**0.936397, 'index':  1.634560 , },
    'J2108+494':{ 'jys':10**1.228081, 'index':  -0.285497 , },
    'J2118+605':{ 'jys':10**1.565675, 'index':  -0.230063 , },
    'J2119+494':{ 'jys':10**1.669059, 'index':  -0.801152 , },
    'J2124+250':{ 'jys':10**2.034735, 'index':  -0.662073 , },
    'J2144+281':{ 'jys':10**1.787362, 'index':  -1.452676 , },
    'J2156+380':{ 'jys':10**2.074528, 'index':  -1.338374 , },
    'J2246+394':{ 'jys':10**2.115869, 'index':  -1.139904 , },
    'J233815+270154':{ 'ra':'23:38:15.78', 'dec':'27:01:54.2',
                       'jys':10**0.885863, 'index':  -4.125722 , },
    'J2351+644':{ 'jys':10**0.910023, 'index':  0.811619 , },
}

def get_catalog(srcs=None, cutoff=None, catalogs=['helm','misc']):
    '''Return a catalog containing the listed sources.'''
#    custom_srcs = ['J1615-605','J1935-461','J2154-692','J2358-605']
    log.info("get_catalog")
    specials = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter',
    'Saturn', 'Uranus', 'Neptune']
    srclist =[]
    for c in catalogs:
        log.info("looking for %s in a local file"%(c,))
        this_srcs = generic_catalog.get_srcs(srcs=srcs,
              cutoff=cutoff,catalogs=[c],loglevel=loglevel)
        if len(this_srcs)==0:
            log.warning("no sources found with genericfile, trying built in catalog")
            tcat = a.src.get_catalog(srcs=srcs, 
                   cutoff=cutoff, catalogs=[c])
            srclist += [tcat[src] for src in tcat]
        else: srclist += this_srcs
    #test bit. make all source indexes 0
    #for i in range(len(srclist)):
    #    srclist[i].index=0
    
    cat = a.fit.SrcCatalog(srclist)
    #Add specials.  All fixed radio sources must be in catalog, for completeness
    if not srcs is None:
        for src in srcs:
            if src in src_prms.keys():
                if src in specials:
                    cat[src] = a.fit.RadioSpecial(src,**src_prms[src])
    return cat

if __name__=='__main__':
    import sys, numpy as n
    if len(sys.argv)>1:
        print "loading catalog: ",sys.argv[1]
        logging.basicConfig(level=logging.DEBUG)
        cat = get_catalog(catalogs=[sys.argv[1]])
        names = [cat[src].src_name for src in cat]
        print "loaded",len(names)," sources"
        flx = [cat[src]._jys for src in cat]
        #print names
        print "brightest source in catalog"
        print names[flx.index(n.max(flx))],n.max(flx)
        log.info("loaded %d items from %s"%(len(cat),sys.argv[1]))
        try: assert([cat[src].e_S_nu for src in cat])
        except(AttributeError): print "this catalog does not have flux errors"