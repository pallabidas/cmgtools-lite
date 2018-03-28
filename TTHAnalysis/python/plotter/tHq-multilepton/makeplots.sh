#!/bin/bash
USAGE="
makeplots.sh outdir plottag

Where plottag is one of:
 3l, 3l-zcontrol, 3l-ttcontrol
 2lss-mm, 2lss-mm-ttcontrol
 2lss-em, 2lss-em-ttcontrol
 2lss-ee, 2lss-ee-ttcontrol

And the plots will be stored in outdir/
"
function DONE {
    echo -e "\e[92mDONE\e[0m"
    exit 0
}

if [[ "X$1" == "X" ]]; then echo "Please provide output directory name: [makeplots.sh outdir plottag]"; exit; fi
OUTDIR=$1; shift;
if [[ "X$1" == "X" ]]; then echo "Please Provide plottag (e.g. 2lss-mm): [makeplots.sh outdir plottag]"; exit; fi
PLOTTAG=$1; shift;


# Note: tthtrees is a symlink to /afs/cern.ch/work/p/peruzzi/tthtrees/
#       thqtrees is a symlink to /afs/cern.ch/work/s/stiegerb/TTHTrees/13TeV/

LUMI=35.9
BASEOPTIONS=" -f -j 8 -l ${LUMI} --s2v"\
" -L ttH-multilepton/functionsTTH.cc"\
" -L tHq-multilepton/functionsTHQ.cc"\
" --tree treeProducerSusyMultilepton"\
" --mcc ttH-multilepton/lepchoice-ttH-FO.txt"
TREEINPUTS="-P thqtrees/TREES_TTH_250117_Summer16_JECV3_noClean_qgV2_tHqsoup_v2/"
FRIENDTREES=" -F sf/t thqtrees/tHq_production_Jan25/1_thq_recleaner_240217/evVarFriend_{cname}.root"\
" -F sf/t thqtrees/tHq_production_Jan25/2_thq_friends_Feb24/evVarFriend_{cname}.root"\
" -F sf/t thqtrees/tHq_production_Jan25/5_triggerDecision_250117_v1/evVarFriend_{cname}.root"\
" -F sf/t thqtrees/tHq_production_Jan25/6_bTagSF_v2/evVarFriend_{cname}.root"
DRAWOPTIONS="--lspam '#bf{CMS} #it{Preliminary}' --legendFontSize 0.035"\
"  --maxRatioRange 0 2 --fixRatioRange --showMCError"\

# Pileup weight, btag SFs, trigger SFs, lepton Eff SFs:
OPT2L="-W puw2016_nTrueInt_36fb(nTrueInt)*eventBTagSF*"\
"triggerSF_ttH(LepGood_pdgId[iLepFO_Recl[0]],LepGood_pdgId[iLepFO_Recl[1]],2)*"\
"leptonSF_ttH(LepGood_pdgId[iLepFO_Recl[0]],LepGood_pt[iLepFO_Recl[0]],LepGood_eta[iLepFO_Recl[0]],2)*"\
"leptonSF_ttH(LepGood_pdgId[iLepFO_Recl[1]],LepGood_pt[iLepFO_Recl[1]],LepGood_eta[iLepFO_Recl[1]],2)"
OPT3L="-W puw2016_nTrueInt_36fb(nTrueInt)*eventBTagSF*"\
"triggerSF_ttH(LepGood_pdgId[iLepFO_Recl[0]],LepGood_pdgId[iLepFO_Recl[1]],3)*"\
"leptonSF_ttH(LepGood_pdgId[iLepFO_Recl[0]],LepGood_pt[iLepFO_Recl[0]],LepGood_eta[iLepFO_Recl[0]],3)*"\
"leptonSF_ttH(LepGood_pdgId[iLepFO_Recl[1]],LepGood_pt[iLepFO_Recl[1]],LepGood_eta[iLepFO_Recl[1]],3)*"\
"leptonSF_ttH(LepGood_pdgId[iLepFO_Recl[2]],LepGood_pt[iLepFO_Recl[2]],LepGood_eta[iLepFO_Recl[2]],3)"

OPTIONS="--pdir ${OUTDIR}"
MCA=""
CUTS=""
PLOTS=""
case "$PLOTTAG" in
    "3l" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT3L} --sP finalBins_log_40"
        MCA="tHq-multilepton/mca-thq-3l-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-3l.txt"
        PLOTS="tHq-multilepton/plots-thq-3l-kinMVA.txt"
        ;;
    "3l-mvaout" )
        OPTIONS="${OPTIONS} ${OPT3L} --plotmode norm"
        OPTIONS="${OPTIONS} --select-plot thqMVA_tt_3l,thqMVA_ttv_3l"
        OPTIONS="${OPTIONS} --xp WWss,WWDPS,VVV,tttt,tZq,ZZ,WZ"
        MCA="tHq-multilepton/mca-thq-3l-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-3l.txt"
        PLOTS="tHq-multilepton/plots-thq-3l-kinMVA.txt"
        ;;
    "3l-zcontrol" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT3L}"
        MCA="tHq-multilepton/mca-thq-3l-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-3l-Zcontrol.txt"
        PLOTS="tHq-multilepton/plots-thq-3l-zcontrol.txt"
        ;;
    "3l-ttcontrol" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT3L}"
        MCA="tHq-multilepton/mca-thq-3l-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-3l-ttbarcontrol.txt"
        PLOTS="tHq-multilepton/plots-thq-3l-kinMVA.txt"
        ;;
    "3l-otherhiggs" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT3L}"
        MCA="tHq-multilepton/mca-3l-otherhiggs.txt"
        CUTS="tHq-multilepton/cuts-thq-3l.txt"
        PLOTS="tHq-multilepton/plots-thq-3l-kinMVA.txt"
        ;;
    "3l-frclosure" )
        DRAWOPTIONS="${DRAWOPTIONS} --ratioDen TT_FR_QCD --errors --AP --rebin 2 --ratioNums TT_fake"
        SELECTPLOT="--sP thqMVA_tt_3l --sP thqMVA_ttv_3l"
        SELECTPROCESS="-p incl_FR_QCD_elonly -p incl_FR_QCD_muonly -p TT_FR_QCD -p TT_FR_TT -p TT_fake"

        OPTIONS="${TREEINPUTS} ${FRIENDTREES} ${BASEOPTIONS} ${DRAWOPTIONS} ${OPT3L} ${SELECTPROCESS} ${SELECTPLOT}"
        MCA="ttH-multilepton/mca-3l-mc-closuretest.txt"
        CUTS="tHq-multilepton/cuts-thq-3l.txt"
        PLOTS="tHq-multilepton/plots-thq-3l-kinMVA.txt"
        ARGOPTS="${MCA} ${CUTS} ${PLOTS} ${OPTIONS}"

        python mcPlots.py ${ARGOPTS} --pdir ${OUTDIR}/3l_mufake_norm/  -E mufake --plotmode nostack --fitRatio 0
        python mcPlots.py ${ARGOPTS} --pdir ${OUTDIR}/3l_mufake_shape/ -E mufake --plotmode norm --fitRatio 1
        python mcPlots.py ${ARGOPTS} --pdir ${OUTDIR}/3l_elfake_norm/  -E elfake --plotmode nostack --fitRatio 0
        python mcPlots.py ${ARGOPTS} --pdir ${OUTDIR}/3l_elfake_shape/ -E elfake --plotmode norm --fitRatio 1
        DONE
        ;;
    "2lss-otherhiggs" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT2L} -E mm_chan --neg"
        MCA="tHq-multilepton/mca-2lss-otherhiggs.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss.txt"
        PLOTS="tHq-multilepton/plots-thq-2lss-kinMVA.txt"
        ;;
    "2lss-mvaout" )
        OPTIONS="${OPTIONS} ${OPT2L} --plotmode norm"
        OPTIONS="${OPTIONS} --select-plot thqMVA_tt_2lss,thqMVA_ttv_2lss"
        OPTIONS="${OPTIONS} --xp WWss,WWDPS,VVV,tttt,tZq,ZZ,WZ"
        MCA="tHq-multilepton/mca-thq-2lss-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss.txt"
        PLOTS="tHq-multilepton/plots-thq-2lss-kinMVA.txt"
        ;;
    "2lss-mm" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT2L}"
        OPTIONS="${OPTIONS} --xP finalBins_log_em_40 --xP finalBins_log_ee_40"
        #OPTIONS="${OPTIONS} --sP finalBins_log_mm_40 "
        MCA="tHq-multilepton/mca-thq-2lss-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss.txt"
        PLOTS="tHq-multilepton/plots-thq-2lss-kinMVA.txt"
        ;;
    "2lss-ttcontrol" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT2L}"
        MCA="tHq-multilepton/mca-thq-2lss-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss-ttbarcontrol.txt"
        PLOTS="tHq-multilepton/plots-thq-2lss-kinMVA.txt"
        ;;
    "2lss-mm-ttcontrol" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT2L} -E mm_chan --xp data_flips"
        OPTIONS="${OPTIONS} --xP finalBins_log_em_40 --xP finalBins_log_ee_40"
        MCA="tHq-multilepton/mca-thq-2lss-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss-ttbarcontrol.txt"
        PLOTS="tHq-multilepton/plots-thq-2lss-kinMVA.txt"
        ;;
    "2lss-em" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT2L} -E em_chan"
        # OPTIONS="${OPTIONS} --xP finalBins_log_mm_40 --xP finalBins_log_ee_40"
        OPTIONS="${OPTIONS} --sP finalBins_log_em_40"
        MCA="tHq-multilepton/mca-thq-2lss-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss.txt"
        PLOTS="tHq-multilepton/plots-thq-2lss-kinMVA.txt"
        ;;
    "2lss-me" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT2L} -E me_chan"
        MCA="tHq-multilepton/mca-thq-2lss-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss.txt"
        PLOTS="tHq-multilepton/plots-thq-2lss-kinMVA.txt"
        ;;
    "2lss-em-ttcontrol" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT2L} -E em_chan"
        OPTIONS="${OPTIONS} --xP finalBins_log_mm_40 --xP finalBins_log_ee_40"
        MCA="tHq-multilepton/mca-thq-2lss-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss-ttbarcontrol.txt"
        PLOTS="tHq-multilepton/plots-thq-2lss-kinMVA.txt"
        ;;
    "2lss-ee" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT2L} -E ee_chan"
        # OPTIONS="${OPTIONS} --xP finalBins_log_mm_40 --xP finalBins_log_em_40"
        OPTIONS="${OPTIONS} --sP finalBins_40 --sP finalBins_log_ee_40"
        MCA="tHq-multilepton/mca-thq-2lss-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss.txt"
        PLOTS="tHq-multilepton/plots-thq-2lss-kinMVA.txt"
        ;;
    "2lss-ee-ttcontrol" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT2L} -E ee_chan"
        OPTIONS="${OPTIONS} --xP finalBins_log_mm_40 --xP finalBins_log_em_40"
        MCA="tHq-multilepton/mca-thq-2lss-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss-ttbarcontrol.txt"
        PLOTS="tHq-multilepton/plots-thq-2lss-kinMVA.txt"
        ;;
    "2los-em-ttcontrol" )
        TREEINPUTS="-P tthtrees/TREES_TTH_250117_Summer16_JECV3_noClean_qgV2"
        FRIENDTREES="-F sf/t thqtrees/5_triggerDecision_230217_v6/evVarFriend_{cname}.root"\
        " -F sf/t thqtrees/6_bTagSF_v6/evVarFriend_{cname}.root"\
        " -F sf/t thqtrees/1_thq_recleaner_240217_full/evVarFriend_{cname}.root"\
        " -F sf/t thqtrees/2_thq_friends_Feb24_full/evVarFriend_{cname}.root"
        OPTIONS="${TREEINPUTS} ${FRIENDTREES} ${BASEOPTIONS} ${OPTIONS} ${DRAWOPTIONS} ${OPT2L}"
        OPTIONS="${OPTIONS} --scaleBkgToData TT --scaleBkgToData DY --scaleBkgToData WJets --scaleBkgToData SingleTop --scaleBkgToData WW"
        MCA="tHq-multilepton/mca-2los-mcdata.txt"
        CUTS="tHq-multilepton/cuts-thq-ttbar-fwdjet.txt"
        PLOTS="tHq-multilepton/plots-thq-ttbar-fwdjet.txt"
        python mcPlots.py ${MCA} ${CUTS} ${PLOTS} ${OPTIONS} -E fwdjetpt25 --select_plot maxEtaJet25
        DONE
        ;;
    "2lss-frclosure" )
        DRAWOPTIONS="${DRAWOPTIONS} --ratioDen TT_FR_QCD --errors --AP --rebin 2 --ratioNums TT_fake"
        SELECTPLOT="--sP thqMVA_tt_2lss --sP thqMVA_ttv_2lss"
        SELECTPROCESS="-p incl_FR_QCD_elonly -p incl_FR_QCD_muonly -p TT_FR_QCD -p TT_FR_TT -p TT_fake"

        OPTIONS="${TREEINPUTS} ${FRIENDTREES} ${BASEOPTIONS} ${DRAWOPTIONS} ${OPT3L} ${SELECTPROCESS} ${SELECTPLOT}"
        MCA="ttH-multilepton/mca-2lss-mc-closuretest.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss.txt"
        PLOTS="tHq-multilepton/plots-thq-2lss-kinMVA.txt"
        ARGOPTS="${MCA} ${CUTS} ${PLOTS} ${OPTIONS}"

        python mcPlots.py ${ARGOPTS} --pdir ${OUTDIR}/2lss_mm_norm/  -E mm_chan --plotmode nostack --fitRatio 0
        python mcPlots.py ${ARGOPTS} --pdir ${OUTDIR}/2lss_mm_shape/ -E mm_chan --plotmode norm --fitRatio 1
        python mcPlots.py ${ARGOPTS} --pdir ${OUTDIR}/2lss_ee_norm/  -E ee_chan --plotmode nostack --fitRatio 0
        python mcPlots.py ${ARGOPTS} --pdir ${OUTDIR}/2lss_ee_shape/ -E ee_chan --plotmode norm --fitRatio 1
        python mcPlots.py ${ARGOPTS} --pdir ${OUTDIR}/2lss_em_mufake_norm/  -E em_chan -E mufake --plotmode nostack --fitRatio 0
        python mcPlots.py ${ARGOPTS} --pdir ${OUTDIR}/2lss_em_mufake_shape/ -E em_chan -E mufake --plotmode norm --fitRatio 1
        python mcPlots.py ${ARGOPTS} --pdir ${OUTDIR}/2lss_em_elfake_norm/  -E em_chan -E elfake --plotmode nostack --fitRatio 0
        python mcPlots.py ${ARGOPTS} --pdir ${OUTDIR}/2lss_em_elfake_shape/ -E em_chan -E elfake --plotmode norm --fitRatio 1
        DONE
        ;;
    "ntuple_3l" )
        OPTIONS="${OPTIONS} ${OPT3L}"
        # MCA="tHq-multilepton/signal_extraction/mca-thq-3l-tontuple.txt"
        MCA="tHq-multilepton/signal_extraction/mca-thq-3l-tontuple-allSM.txt"
        CUTS="tHq-multilepton/cuts-thq-3l.txt"
        PLOTS="tHq-multilepton/plots-ntuplecontent.txt"
        SELECTPLOT=""
        SELECTPROCESS=""
        OUTFILE="${OUTDIR}/ntuple_{name}.root"
        test -d ${OUTDIR} || mkdir -p ${OUTDIR}

        ARGUMENTS="${MCA} ${CUTS} ${PLOTS}"
        OPTIONS="${TREEINPUTS} ${FRIENDTREES} ${BASEOPTIONS} ${OPTIONS} ${SELECTPLOT} ${SELECTPROCESS}"
        echo "mca    : ${MCA}"
        echo "cuts   : ${CUTS}"
        echo "plots  : ${PLOTS}"
        echo "outfile: ${OUTFILE}"
        python mcNtuple.py ${MCA} ${CUTS} ${PLOTS} ${OUTFILE} ${OPTIONS}
        DONE
        ;;
    "ntuple_2lss" )
        OPTIONS="${OPTIONS} ${OPT2L}"
        # MCA="tHq-multilepton/signal_extraction/mca-thq-2lss-tontuple.txt"
        MCA="tHq-multilepton/signal_extraction/mca-thq-2lss-tontuple-allSM.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss.txt"
        PLOTS="tHq-multilepton/plots-ntuplecontent.txt"
        SELECTPLOT=""
        SELECTPROCESS=""
        OUTFILE="${OUTDIR}/ntuple_{name}.root"
        test -d ${OUTDIR} || mkdir -p ${OUTDIR}

        ARGUMENTS="${MCA} ${CUTS} ${PLOTS}"
        OPTIONS="${TREEINPUTS} ${FRIENDTREES} ${BASEOPTIONS} ${OPTIONS} ${SELECTPLOT} ${SELECTPROCESS}"
        echo "mca     : ${MCA}"
        echo "cuts    : ${CUTS}"
        echo "plots   : ${PLOTS}"
        echo "outfiles: ${OUTFILE}"
        python mcNtuple.py ${MCA} ${CUTS} ${PLOTS} ${OUTFILE} ${OPTIONS}
        DONE
        ;;
    "all" )
        ./$0 ${OUTDIR}/3l 3l
        ./$0 ${OUTDIR}/2lss-mm 2lss-mm
        ./$0 ${OUTDIR}/2lss-em 2lss-em
        ./$0 ${OUTDIR}/2lss-ee 2lss-ee
        # ./$0 ${OUTDIR}/3l-zcontrol 3l-zcontrol
        # ./$0 ${OUTDIR}/2lss-mm-ttcontrol 2lss-mm-ttcontrol
        # ./$0 ${OUTDIR}/2lss-em-ttcontrol 2lss-em-ttcontrol
        # ./$0 ${OUTDIR}/2lss-ee-ttcontrol 2lss-ee-ttcontrol
        DONE
        ;;
    "frclosures" )
        ./$0 ${OUTDIR} 3l-frclosure
        ./$0 ${OUTDIR} 2lss-frclosure
        DONE
        ;;
    "ntuples" )
        ./$0 ${OUTDIR}/3l ntuple_3l
        ./$0 ${OUTDIR}/2lss ntuple_2lss
        DONE
        ;;
    "postfit" )
        FITRESULT="tHq-multilepton/signal_extraction/cards_Mar28_unblinded/comb3/mlfit.root"
        DRAWOPTIONS="--maxRatioRange 0 3.2 --fixRatioRange"

        MCA1="tHq-multilepton/mca-thq-3l-mcdata-frdata.txt"
        MCA2="tHq-multilepton/signal_extraction/mca-thq-3l-mcdata-frdata_limits.txt"
        PLOTINPUT="www/Mar28_unblinding/3l/plots-thq-3l-kinMVA.root"
        ./postFitPlotsTHq.py ${MCA1} ${MCA2} ${PLOTINPUT} ${FITRESULT} 3l --outDir ${OUTDIR}/3l/ ${DRAWOPTIONS} --doLog 
        ./postFitPlotsTHq.py ${MCA1} ${MCA2} ${PLOTINPUT} ${FITRESULT} 3l --outDir ${OUTDIR}/3l/ ${DRAWOPTIONS}

        MCA1="tHq-multilepton/mca-thq-2lss-mcdata-frdata.txt"
        MCA2="tHq-multilepton/signal_extraction/mca-thq-2lss-mcdata-frdata_limits.txt"
        PLOTINPUT="www/Mar28_unblinding/2lss-mm/plots-thq-2lss-kinMVA.root"
        ./postFitPlotsTHq.py ${MCA1} ${MCA2} ${PLOTINPUT} ${FITRESULT} 2lss_mm --outDir ${OUTDIR}/2lss_mm/ ${DRAWOPTIONS} --doLog 
        ./postFitPlotsTHq.py ${MCA1} ${MCA2} ${PLOTINPUT} ${FITRESULT} 2lss_mm --outDir ${OUTDIR}/2lss_mm/ ${DRAWOPTIONS}

        PLOTINPUT="www/Mar28_unblinding/2lss-em/plots-thq-2lss-kinMVA.root"
        ./postFitPlotsTHq.py ${MCA1} ${MCA2} ${PLOTINPUT} ${FITRESULT} 2lss_em --outDir ${OUTDIR}/2lss_em/ ${DRAWOPTIONS} --doLog 
        ./postFitPlotsTHq.py ${MCA1} ${MCA2} ${PLOTINPUT} ${FITRESULT} 2lss_em --outDir ${OUTDIR}/2lss_em/ ${DRAWOPTIONS}

        DONE
        ;;
    *)
        echo "${USAGE}"
        echo -e "\e[31mUnknown plottag\e[0m"
        exit 1
esac

echo "Storing output in ${OUTDIR}/";
echo "Normalizing to ${LUMI}/fb";

ARGUMENTS="${MCA} ${CUTS} ${PLOTS}"
OPTIONS="${TREEINPUTS} ${FRIENDTREES} ${BASEOPTIONS} ${OPTIONS}"

echo "mca  : ${MCA}"
echo "cuts : ${CUTS}"
echo "plots: ${PLOTS}"



if [[ "X$1" != "X" ]]; then
    SELECTPLOT=$1; shift;
    echo "Running a single plot: ${SELECTPLOT}";
    python mcPlots.py ${ARGUMENTS} ${OPTIONS} --select-plot ${SELECTPLOT}
else
    # python mcPlots.py ${ARGUMENTS} ${OPTIONS} --enable-cut 2bl --select-plot dEtaFwdJet2BJet_40
    python mcPlots.py ${ARGUMENTS} ${OPTIONS} --exclude-plot dEtaFwdJet2BJet_40
fi

DONE
