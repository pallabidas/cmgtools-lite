import operator
import itertools
import copy
import ROOT

from PhysicsTools.Heppy.analyzers.core.Analyzer import Analyzer
from PhysicsTools.Heppy.analyzers.core.AutoHandle import AutoHandle
from PhysicsTools.HeppyCore.statistics.counter import Counter, Counters
import PhysicsTools.HeppyCore.framework.config as cfg
from PhysicsTools.HeppyCore.utils.deltar import deltaR

#using https://twiki.cern.ch/twiki/bin/viewauth/CMS/L1ECALPrefiringWeightRecipe

class L1prefiring ( Analyzer ):

    def __init__(self, cfg_ana, cfg_comp, looperName ):
        super(L1prefiring, self).__init__(cfg_ana,cfg_comp,looperName)
        self.dataera = cfg_ana.DataEra
        self.useEMpt = cfg_ana.UseJetEMPt
        self.prefiringRateSystUnc = cfg_ana.PrefiringRateSystematicUncty
        self.fname = cfg_ana.L1Maps

        file_prefiringmaps = ROOT.TFile.Open(self.fname, 'read')
        mapphotonfullname = 'L1prefiring_photonptvseta_'+self.dataera
        self.h_prefmap_photon = file_prefiringmaps.Get(mapphotonfullname)
        self.h_prefmap_photon.SetDirectory(0)
        if (self.useEMpt) : mapjetfullname = 'L1prefiring_jetemptvseta_'+self.dataera
        else : mapjetfullname = 'L1prefiring_jetptvseta_'+self.dataera
        self.h_prefmap_jet = file_prefiringmaps.Get(mapjetfullname)
        self.h_prefmap_jet.SetDirectory(0)
        file_prefiringmaps.Close()

    def declareHandles(self):
        super(L1prefiring, self).declareHandles()
        self.handles['photons'] = AutoHandle( self.cfg_ana.photons,"std::vector<pat::Photon>" )
        self.handles['jets']    = AutoHandle( self.cfg_ana.jets, "std::vector<pat::Jet>" )

    def GetPrefiringRate(self, eta, pt, h_prefmap, fluctuation):
        if (h_prefmap == 0) : return 0.
        nbinsy = h_prefmap.GetNbinsY()
        maxy= h_prefmap.GetYaxis().GetBinLowEdge(nbinsy+1)
        if (pt >= maxy) : pt = maxy-0.01
        thebin = h_prefmap.FindBin(eta,pt)
        prefrate =  h_prefmap.GetBinContent(thebin)
        if (fluctuation == 1) : prefrate = min(max(prefrate +  h_prefmap.GetBinError(thebin), (1.+self.prefiringRateSystUnc)*prefrate),1.)
        if (fluctuation == 2) : prefrate = max(min(prefrate -  h_prefmap.GetBinError(thebin), (1.-self.prefiringRateSystUnc)*prefrate),0.)
        return prefrate

    def beginLoop(self, setup):
        super(L1prefiring, self).beginLoop( setup )

    def process(self, event):
        self.readCollections( event.input )

        photons = self.handles['photons'].product()
        jets    = self.handles['jets'].product()
        fluct   = [0, 1, 2] #central, up, down

        #Probability for the event NOT to prefire, computed with the prefiring maps per object
        #Up and down values correspond to the resulting value when shifting up/down all prefiring rates in prefiring maps
        NonPrefiringProba = [1.]*3

        for f in fluct:

            affectedphotons = []
    
            #Start by applying the prefiring maps to photons in the affected regions
            for pho in photons : 
                if (pho.pt() < 20.) : continue
                if (abs(pho.eta()) < 2.) : continue
                if (abs(pho.eta()) > 3.) : continue
                affectedphotons.append(pho)
                NonPrefiringProba[f] *= (1. - self.GetPrefiringRate(pho.eta(), pho.pt(), self.h_prefmap_photon, f))
            
            #Now applying the prefiring maps to jets in the affected regions
            for j in jets :
                if (j.pt() < 20.) : continue
                if (abs(j.eta()) < 2.) : continue
                if (abs(j.eta()) > 3.) : continue
     
                #Loop over photons to remove overlap
                nonprefiringprobfromoverlappingphotons = 1.
                for apho in affectedphotons:
                    dR = deltaR(j.eta(), j.phi(), apho.eta(), apho.phi())
                    if (dR > 0.4): continue
                    prefiringprob_gam = self.GetPrefiringRate(apho.eta(), apho.pt(), self.h_prefmap_photon, f)
                    nonprefiringprobfromoverlappingphotons  *= (1. - prefiringprob_gam) 
   
                ptem_jet = j.pt()*(j.neutralEmEnergyFraction() + j.chargedEmEnergyFraction())
                if (self.useEMpt) : prefiringprob_jet = self.GetPrefiringRate( j.eta(), ptem_jet, self.h_prefmap_jet, f)
                else : prefiringprob_jet= self.GetPrefiringRate( j.eta(), j.pt(), self.h_prefmap_jet, f)
                #useEMpt = true if one wants to use maps parametrized vs Jet EM pt instead of pt
 
                nonprefiringprobfromoverlappingjet = (1. - prefiringprob_jet)
                #If there are no overlapping photons, just multiply by the jet non prefiring rate
                if (nonprefiringprobfromoverlappingphotons == 1.) :   NonPrefiringProba[f] *= (1. - prefiringprob_jet)
                #If overlapping photons have a non prefiring rate larger than the jet, then replace these weights by the jet one
                elif (nonprefiringprobfromoverlappingphotons > nonprefiringprobfromoverlappingjet) :
                    if (nonprefiringprobfromoverlappingphotons != 0.) : NonPrefiringProba[f] *= (nonprefiringprobfromoverlappingjet/nonprefiringprobfromoverlappingphotons)
                    else : NonPrefiringProba[f] = 0.
 
                elif (nonprefiringprobfromoverlappingphotons < nonprefiringprobfromoverlappingjet) : NonPrefiringProba[f] *= 1.
            

        event.NonPrefiringProb = NonPrefiringProba[0]
        event.NonPrefiringProbUp = NonPrefiringProba[1]
        event.NonPrefiringProbDown = NonPrefiringProba[2]       
                                                 
        return True

setattr(L1prefiring, "defaultConfig", cfg.Analyzer(
        class_object = L1prefiring,
        photons = 'slimmedPhotons',
        jets = 'slimmedJets',   
        L1Maps = '$CMSSW_BASE/src/CMGTools/TTHAnalysis/data/L1PrefiringMaps_new.root',
        DataEra = '2017BtoF',
        UseJetEMPt = False,
        PrefiringRateSystematicUncty = 0.2, 
    )
) 
