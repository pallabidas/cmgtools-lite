#!/bin/bash
# Usage: make_workspaces.sh MODEL card1.txt [card2.txt ...]

# Set environment for combine
COMBINEDIR="/afs/cern.ch/user/s/stiegerb/combine/"
cd $COMBINEDIR; eval `scramv1 runtime -sh`; cd -;

MODEL="K5"
if [[ "$1" == "K5" || "$1" == "K4" || "$1" == "K6"  || "$1" == "K6b" || "$1" == "K7" ]]; then
	MODEL=$1
	shift;
fi
echo "...running with ${MODEL} model"

RATIO_FROM_NAME () {
	# Calculate alpha from a card name:
	# i.e. extract '0p5_1p5' from 'tHq_0p5_1p5.card.txt'
	# then split it into 0p5 and 1p5, transform to 0.5 and 1.5
	# and finally return 1.5/0.5
	# Use some cut, sed, bc magic learned from Google
	KV=$(echo $1 | cut -d '_' -f 2 | sed -e 's/[p]/./g' | sed -e 's/[m]/-/g')
	KT=$(echo $1 | cut -d '_' -f 3 | cut -d '.' -f 1 | sed -e 's/[p]/./g' | sed -e 's/[m]/-/g')
	ALPHA=$(echo "scale=2; $KT/$KV" | bc)
	echo $ALPHA
}

# Run the limit
for card in "$@"
do 
	echo "...processing $card"
	# Use one of the HCG models:
	OPTIONS="-P HiggsAnalysis.CombinedLimit.LHCHCGModels:${MODEL} --PO BRU=0 -m 125"
	OUTNAME="ws_${card%.card.txt}_${MODEL}.card.root"

	# Or do the scaling by hand:
	# 'alpha' = kt/kV
	if [[ ${MODEL} == "K6b" ]]; then
		ALPHA=$(RATIO_FROM_NAME $card)
		echo "... using alpha=${ALPHA}"
		OPTIONS="-P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel -m 125"
		OPTIONS="${OPTIONS} --PO 'map=.*/ttH.*:r_ttH[1,-5,10]'"
		OPTIONS="${OPTIONS} --PO 'map=.*/tHq.*:r_tHq=expr::r_tHq(\"(2.633+3.578/(@1*@1)-5.211/(@1))*@0\",r_ttH,${ALPHA})'"
		OPTIONS="${OPTIONS} --PO 'map=.*/tHW.*:r_tHW=expr::r_tHW(\"(2.909+2.310/(@1*@1)-4.220/(@1))*@0\",r_ttH,${ALPHA})'"
	fi
	CMD="text2workspace.py ${card} -o ${OUTNAME} ${OPTIONS}"
	echo "${CMD}"
	eval $CMD
done
