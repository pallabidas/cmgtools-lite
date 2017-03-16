# tHq signal extraction procedure

### Produce datacards:

```
python makeShapeCardsTHQ.py \
--savefile report_thq_3l.root \
tHq-multilepton/signal_extraction/mca-thq-3l-mcdata-frdata_limits.txt \
tHq-multilepton/cuts-thq-3l.txt \
thqMVA_ttv_3l:thqMVA_tt_3l 40,-1,1,40,-1,1 \
tHq-multilepton/signal_extraction/systsEnv.txt \
-P treedir/mixture_jecv6prompt_datafull_jul20/ \
-P treedir/tHq_production_Jan11/ \
--tree treeProducerSusyMultilepton \
--s2v -j 8 -l 12.9 -f \
--xp data --asimov \
-F sf/t treedir/tHq_eventvars_Jan18/evVarFriend_{cname}.root \
--Fs {P}/2_recleaner_v5_b1E2 \
--mcc ttH-multilepton/lepchoice-ttH-FO.txt \
--neg \
-o 3l \
--od tHq-multilepton/signal_extraction/cards \
-L tHq-multilepton/functionsTHQ.cc \
--2d-binning-function "10:tHq_MVAto1D_3l_10" \
-v 2
```

- Change from `--savefile report.root` to `--infile report.root` to rerun quickly with a different binning.
- Binning function in `tHq-multilepton/functionsTHQ.cc`. This turns the 2d histogram of mva1 vs mva2 into a 1d histogram for shape fitting in combine.
- Keep track of reporting of empty bins and adjust binning function accordingly.

This produces two files for each point: `..input.root` and `..card.txt`.

Note that the standard selection is hardcoded in `tHq-multilepton/makecards.sh`.

Check some of the datacards using `HiggsAnalysis/CombinedLimit/test/systematicsAnalyzer.py`:

```
systematicsAnalyzer.py data.card.txt --all -f html > www/systanalysis.html
```

### Run the limit calculation:

You'll need to set your environment to a release area with `combine` available, e.g. like so:

```
cd ~stiegerb/combine/; cmsenv ; cd -;
```

Run on a single datacard you can use combine directly:

```
combine -M Asymptotic --run blind --rAbsAcc 0.0005 --rRelAcc 0.0005 ttH_3l.card.txt
```

or use `make_limit.sh cards/ttH_3l.card.txt` to do everything in one go.

In case of several datacards, combine them first with `combineCards.py *card.txt > combined.txt`.

Then the "Expected 50.0%" is the number to be quoted.

### Processing several Ct/CV points

Use `runAllLimits.py` to run on all the cards in one directory and produce a .csv file with the Ct/CV points, the expected limit, and the one and two sigma bands.

Use `combineChannels.py` to combine the corresponding cards for each point in a list of input directories. Typically you'd run something like this:

```
python combineAllCards.py cards_Jan31/2lss-mm/ cards_Jan31/2lss-em/ cards_Jan31/2lss-ee/ cards_Jan31/3l/ -o comb4
```

This will produce combined cards in a new directory (specified with the `-o` option) and also copy the root files and original cards into it.

You can then use `runAllLimits.py` to produce the combined limits, e.g.:

```
python runAllLimits.py -t 2lss_mm 2lss_mm/
```

### Making impact and pull plots

Note that you'll need the `combineTool.py` for this. See [here](https://twiki.cern.ch/twiki/bin/view/CMS/SWGuideHiggsAnalysisCombinedLimit) for instructions.

Generate the workspace:

```
text2workspace.py -o tHq_cards.root comb3/tHq_1_m1.card.txt
```

```
python combineTool.py -M Impacts -d tHq_cards.root -m 125 --robustFit 1 --rMin -5 --rMax 10 --doInitialFit

python combineTool.py -M Impacts -d tHq_cards.root -m 125 --robustFit 1 --rMin -5 --rMax 10 --doFits --parallel 12

python combineTool.py -M Impacts -d tHq_cards.root -m 125 -o impacts.json

plotImpacts.py -i impacts.json -o impacts --per-page 20
```

Note that this may require the renaming of root files:
```
for f in *123456.root; do mv $f ${f%.123456.root}.root; done
```

### Closure checks

See also [here](https://twiki.cern.ch/twiki/bin/view/CMS/HiggsWG/HiggsPAGPreapprovalChecks).

```
combine -M MaxLikelihoodFit -t -1 --expectSignal 0 tHq_1_m1.card.txt
python diffNuisances.py -a mlfit.root -g plots.root
```

Check that the fit result is `r=0` and that pulls for the background only fit are all 0.00.

```
combine -M MaxLikelihoodFit -t -1 --expectSignal 1 tHq_1_m1.card.txt
python diffNuisances.py -a mlfit.root -g plots.root
```

Check that the fit result is `r=1` and that pulls for the signal+background fit are all 0.00.

### Limits using HCG model (scaling ttH and tH coherently)

'lambda_FV' in [LambdasReduced](https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit/blob/74x-root6/python/LHCHCGModels.py#L626-L788) is basically our Ct/CV, 'kappa_VV' should correspond to CV^2.

Could also use [KappaVKappaF](https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit/blob/74x-root6/python/LHCHCGModels.py#L522-L624) which directly has Ct and CV (as 'kappa_F', 'kappa_V').

Need to have '13TeV' string in bin names. We can use `combineCards.py` for that, or just our `combineChannels.py`.

```
combineCards.py tHq_3l_1_m1_13TeV=tHq_3l_1_m1.card.txt &> tHq_3l_1_m1_13TeV.txt
```

Produce the workspace using the HCG "LambdasReduced" model. Note that there are some small changes in that code, with respect to the original. See `tHq-multilepton/signal_extraction/LambdasReducedWithr.py`.

```
text2workspace.py tHq_1_m1.card.txt \
-P HiggsAnalysis.CombinedLimit.LHCHCGModels:L2 \
--PO verbose \
--PO BRU=0
```

Or `LHCHCGModels:K3` for the kappa model.

The workspace now contains the proper scaling functions of the higgs processes. Note that it assumes that the input yields (the 'rate' line in the datacards) corresponds to standard model cross sections!

To run the limit for a given point, we need to specify the lambda_FV value at that point and redefine the parameter of interest as the signal strength. We freeze all the other nuisances, including lambda_FV (or kappa_F, kappa_V in case of the kappa model).

```
combine -M Asymptotic --run blind --rAbsAcc 0.0005 --rRelAcc 0.0005 tHq_1_m1.root --setPhysicsModelParameterRanges lambda_FV=-10,10 --setPhysicsModelParameters lambda_FV=-1.0 --freezeNuisances kappa_VV,lambda_du,lambda_Vu,kappa_uu,lambda_lq,lambda_Vq,kappa_qq,lambda_FV --redefineSignalPOIs r
```

See also `runAllLimits.py` for the combine commands to use.

Use -m 125 in text2workspace.py or combine in case you get `<ROOT::Math::GSLInterpolator::Eval>: input domain error` messages.
