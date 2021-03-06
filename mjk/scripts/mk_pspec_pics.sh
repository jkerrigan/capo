#! /bin/bash
export PYTHONPATH='.':$PYTHONPATH
#PREFIX="OneDayFG"
#
##chans=`python -c "print ' '.join(['%d_%d'%(i,i+39) for i in range(10,150,1)])"`
#pols='I Q U V'
#seps='0_16 1_16 0_17'
#chans='110_149'
#RA="1:01_9:00"
#NBOOT=20
#
##DATAPATH=fringe_hor_v006
#SCRIPTSDIR=~/src/capo/pspec_pipeline
#cal="psa898_v003"
#PWD=`pwd`
#DATAPATH="${PWD}/typical_day/*FRXS"
(
echo using config $*
. $*
#set defaults to parameters which might not be set
if [[ ! -n ${WINDOW} ]]; then export WINDOW="none"; fi
#for posterity Print the cal file we are using

pywhich $cal

threadcount=`python -c "c=map(len,['${pols}'.split(),'${chans}'.split(),'${seps}'.split()]);print c[0]*c[1]*c[2]"`
echo Running $threadcount pspec visualizations
PIDS=""

#FILES=`lst_select.py -C ${cal} --ra=${RA} ${DATAPATH}`
test -e ${PREFIX} || mkdir $PREFIX
for chan in $chans; do
    chandir=${PREFIX}/${chan}
    test -e ${chandir} || mkdir ${chandir}
    for pol in $pols; do
        echo "Starting work on ${pol}" 
        poldir=${chandir}/${pol}
        test -e ${poldir} || mkdir ${poldir}
        if [ ! -e ${poldir}/pspec_${PREFIX}_${chan}_${pol}.png ]; then
            for sep in $seps; do
                sepdir=${poldir}/${sep}
                EVEN_FILES=${EVEN_DATAPATH}${sep}/*242.[3456]*uvGL
                ODD_FILES=${ODD_DATAPATH}${sep}/*243.[3456]*uvGL
                test -e ${sepdir} || mkdir ${sepdir}
                LOGFILE=`pwd`/${PREFIX}/${chan}_${pol}_${sep}.log
                echo this is mk_pspec_pics.sh with  |tee  ${LOGFILE}
                echo experiment: ${PREFIX}|tee -a ${LOGFILE}
                echo channels: ${chan}|tee -a ${LOGFILE}
                echo polarization: ${pol}|tee -a ${LOGFILE}
                echo separation: ${sep}|tee -a ${LOGFILE}
                echo `date` | tee -a ${LOGFILE}

                #ANTS=`grid2ant.py -C ${cal} --seps="${sep}"`
                ANTS='cross'
                echo python ${SCRIPTSDIR}/visualize_pspec.py -C ${cal} \
                     -b ${NBOOT} -a ${ANTS} -c ${chan} -p ${pol}\
                      --window=${WINDOW}  ${NOPROJ} --output=${sepdir} --plot \
                       ${EVEN_FILES} ${ODD_FILES} 
                
                python ${SCRIPTSDIR}/visualize_pspec.py -C ${cal} -b ${NBOOT} \
                    -a ${ANTS} -c ${chan} -p ${pol} --window=${WINDOW} \
                      ${NOPROJ} --output=${sepdir} --plot \
                      ${EVEN_FILES} ${ODD_FILES} \
                     | tee -a ${LOGFILE}

                
                echo Ploting Tsys for channels: `date` | tee -a ${LOGFILE} 
                ${SCRIPTSDIR}/plot_tsys.py -a ${ANTS} -C ${cal} \
                     -c ${chan} --vline --freqs --plot --output=${sepdir} \
                      ${EVEN_FILES} | tee -a ${LOGFILE} 
                echo complete! `date`| tee -a ${LOGFILE} 
                PIDS="${PIDS} "$!
            done
        fi
    done
done

echo waiting on `python -c "print len('${PIDS}'.split())"` power spectra threads ${PIDS} 
wait $PIDS
echo Visualization complete | tee -a ${LOGFILE}
)
