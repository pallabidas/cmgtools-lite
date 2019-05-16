#!/usr/bin/env python
import sys, os, re, shlex
import multiprocessing
from subprocess import Popen, PIPE

## FIXME: This should dump the limits for each card as it is running,
##        not all together at the end.

def runCombineCommand(combinecmd, card, verbose=False, queue=None, submitName=None):
    if queue:
        combinecmd = combinecmd.replace('combine', 'combineTool.py')
        combinecmd += ' --job-mode lxbatch --sub-opts="-q %s"' % queue
        combinecmd += ' --task-name tHq_%s' % submitName
        # combinecmd += ' --dry-run'
    if verbose: 
        print 40*'-'
        print "%s %s" % (combinecmd, card)
        print 40*'-'
    try:
        p = Popen(shlex.split(combinecmd) + [card] , stdout=PIPE, stderr=PIPE)
        comboutput = p.communicate()[0]
    except OSError:
        print "combine command not known"
        comboutput = None
    return comboutput

def parseName(card, printout=True):
    # Turn the tag into floats:
    tag = re.match(r'.*\_([\dpm]+\_[\dpm]+).*\.card\.(txt|root)', os.path.basename(card))
    if tag == None:
        print "Couldn't figure out this one: %s" % card
        return

    tag = tag.groups()[0]
    tagf = tag.replace('p', '.').replace('m','-')
    cv,ct = tuple(map(float, tagf.split('_')))
    if printout:
        print "%-40s CV=%5.2f, Ct=%5.2f : " % (os.path.basename(card), cv, ct),
    return cv, ct, tag

def setParamatersFreezeAll(ct,cv,freezeAlso=None):
    addoptions = " --setParameters kappa_t=%.2f,kappa_V=%.2f" % (ct/cv, 1.0)
    addoptions += " --freezeParameters kappa_t,kappa_V,kappa_tau,kappa_mu,"
    addoptions += "kappa_b,kappa_c,kappa_g,kappa_gam,r_others"
    if freezeAlso:
        addoptions += ','
        addoptions += ','.join(freezeAlso)
    addoptions += " --redefineSignalPOIs r"
    return addoptions

def getLimits(card, model='K6', unblind=False, printCommand=False):
    """
    Run combine on a single card, return a tuple of 
    (cv,ct,twosigdown,onesigdown,exp,onesigup,twosigup)
    """
    cv,ct,tag = parseName(card, printout=False)
    printout = "%-40s CV=%5.2f, Ct=%5.2f : " % (os.path.basename(card), cv, ct)

    combinecmd =  "combine -M AsymptoticLimits"
    if not unblind:
        combinecmd += " --run blind"
    combinecmd += " -m 125 --verbose 0 -n cvct%s"%tag
    if model in ['K4', 'K5', 'K6', 'K7']:
        if model == 'K6': # Rescale to cv = 1, we only care about the ct/cv ratio
            combinecmd += setParamatersFreezeAll(ct/cv,1.0)
        else:
            combinecmd += setParamatersFreezeAll(ct, cv)

    comboutput = runCombineCommand(combinecmd, card, verbose=printCommand)

    liminfo = {}
    for line in comboutput.split('\n'):
        if line.startswith('Observed Limit:'):
            liminfo['obs'] = float(line.rsplit('<', 1)[1].strip())
        if line.startswith('Expected'):
            value = float(line.rsplit('<', 1)[1].strip())
            if   'Expected  2.5%' in line: liminfo['twosigdown'] = value
            elif 'Expected 16.0%' in line: liminfo['onesigdown'] = value
            elif 'Expected 50.0%' in line: liminfo['exp']        = value
            elif 'Expected 84.0%' in line: liminfo['onesigup']   = value
            elif 'Expected 97.5%' in line: liminfo['twosigup']   = value

    printout += "%5.2f, %5.2f, \033[92m%5.2f\033[0m, %5.2f, %5.2f" % (
        liminfo['twosigdown'], liminfo['onesigdown'], liminfo['exp'],
        liminfo['onesigup'], liminfo['twosigup'])
    if 'obs' in liminfo: # Add observed limit to output, in case it's there
        printout += "\033[1m %5.2f \033[0m" % (liminfo['obs'])

    print printout

    return cv, ct, liminfo

def getFitValues(card, model='K6', unblind=False, printCommand=False):
    """
    Run combine on a single card, return a tuple of fitvalues
    (cv,ct,median,downerror,uperror)
    """
    cv,ct,tag = parseName(card)
    if printCommand: print ""

    combinecmd =  "combine -M MaxLikelihoodFit"
    combinecmd += " -m 125 --verbose 0 -n cvct%s"%tag
    if model in ['K4', 'K5', 'K6', 'K7']:
        if model == 'K6': # Rescale to cv = 1, we only care about the ct/cv ratio
            combinecmd += setParamatersFreezeAll(ct/cv,1.0)
        else:
            combinecmd += setParamatersFreezeAll(ct, cv)

        if abs(ct/cv) > 3:        
            combinecmd += " --robustFit 1 --setParameterRanges r=0,1"
        else:
            # Note that these ranges don't work well for some points
            # e.g.: -3.0/1.0, -1.5/0.5, -1.25/0.5
            combinecmd += " --robustFit 1 --setParameterRanges r=-5,10"
    comboutput = runCombineCommand(combinecmd, card, verbose=printCommand)

    fitinfo = {}
    for line in comboutput.split('\n'):
        if line.startswith('Best'):
            fitinfo['median'] = float((line.split(': ')[1]).split('  ')[0])
            fitinfo['downerror'] = float((line.split('  ')[1]).split('/')[0])
            fitinfo['uperror'] = float((line.split('+')[1]).split('  (')[0])

    print "\033[92m%5.2f\033[0m, %5.2f, %5.2f" %( fitinfo['median'],
                                                  fitinfo['downerror'],
                                                  fitinfo['uperror'])
    return cv, ct, fitinfo

def getSignificance(card, model='K6', unblind=False, printCommand=False):
    """
    Run combine on a single card, return significance
    """
    cv,ct,tag = parseName(card)
    if printCommand: print ""

    combinecmd =  "combine -M Significance --signif"
    combinecmd += " -m 125 --verbose 0 -n cvct%s"%tag
    if model in ['K4', 'K5', 'K6', 'K7']:
        if model == 'K6': # Rescale to cv = 1, we only care about the ct/cv ratio
            combinecmd += setParamatersFreezeAll(ct/cv,1.0)
        else:
            combinecmd += setParamatersFreezeAll(ct, cv)
    comboutput = runCombineCommand(combinecmd, card, verbose=printCommand)

    significance = {}
    for line in comboutput.split('\n'):
        if line.startswith('Significance'):
            print(line)
            significance['value'] = float(line.rsplit(':', 1)[1].strip())

    print "\033[92m%5.2f\033[0m" %( significance['value'])
    return cv, ct, significance


def processInputs(args, options):
    cards = []
    if os.path.isdir(args[0]):
        inputdir = args[0]

        if options.tag is not None:
            tag = "_" + options.tag
        elif options.tag == "":
            tag = ""
        else:
            # Try to get the tag from the input directory
            if inputdir.endswith('/'):
                inputdir = inputdir[:-1]
            tag = "_" + os.path.basename(inputdir)
            assert('/' not in tag)

        cards = [os.path.join(inputdir, c) for c in os.listdir(inputdir)]

    elif os.path.exists(args[0]):
        tag = options.tag or ""
        if len(tag):
            tag = '_' + tag
        cards = [c for c in args if os.path.exists(c)]

    cards = [c for c in cards if any([c.endswith(ext) for ext in ['card.txt', 'card.root', '.log']])]
    cards = sorted(cards)

    print "Found %d cards to run" % len(cards)
    return cards, tag


def main(args, options):
    cards, tag = processInputs(args, options)

    if options.runmode.lower() == 'limits':
        ## Individual limits, just process all cards and write
        ## the results to a csv file
        csvfname = 'limits_%s.csv'%options.tag
        with open(csvfname, 'w') as csvfile:
            if options.unblind:
                csvfile.write('fname,cv,cf,twosigdown,onesigdown,exp,onesigup,twosigup,obs\n')
            else:
                csvfile.write('fname,cv,cf,twosigdown,onesigdown,exp,onesigup,twosigup\n')

            for card in cards:
                cv, ct, liminfo = getLimits(card, model=options.model,
                                            unblind=options.unblind,
                                            printCommand=options.printCommand)
    
                values = [card, cv, ct]
                values += [liminfo[x] for x in ['twosigdown','onesigdown','exp','onesigup','twosigup']]
                if options.unblind:
                    values += [liminfo['obs']]
                csvfile.write(','.join(map(str, values)) + '\n')

        print "All done. Wrote limits to: %s" % csvfname

    if options.runmode.lower() == 'ctcvlimits':
        pool = multiprocessing.Pool(processes=options.jobs)
        futures = []
        for card in cards:

            future = pool.apply_async(getLimits, (card, options.model,
                                                  options.unblind,
                                                  options.printCommand))
            futures.append((card, future))

        limdata = {} # (cv,ct) -> (2sd, 1sd, lim, 1su, 2su, [obs])
        for card, future in futures:
            cv, ct, liminfo = future.get() # catch timeout?
            limdata[(cv,ct)] = liminfo

        fnames = []
        for cv_ in [0.5, 1.0, 1.5]:
            if not cv_ in [v for v,_ in limdata.keys()]: continue
            csvfname = 'limits%s_cv_%s.csv' % (tag, str(cv_).replace('.','p'))
            with open(csvfname, 'w') as csvfile:
                if options.unblind:
                    csvfile.write('cv,cf,twosigdown,onesigdown,exp,onesigup,twosigup,obs\n')
                else:
                    csvfile.write('cv,cf,twosigdown,onesigdown,exp,onesigup,twosigup\n')
                for cv,ct in sorted(limdata.keys()):
                    if not cv == cv_: continue
                    values = [cv, ct]
                    values += [limdata[(cv,ct)][x] for x in ['twosigdown',
                                                             'onesigdown',
                                                             'exp',
                                                             'onesigup',
                                                             'twosigup']]
                    if options.unblind:
                        values += [limdata[(cv,ct)]['obs']]
                    csvfile.write(','.join(map(str, values)) + '\n')
            fnames.append(csvfname)
        print "All done. Wrote limits to: %s" % (" ".join(fnames))

    if options.runmode.lower() == 'fit':
        fitdata = {} # (cv,ct) -> (fit, down, up)
        for card in cards:
            cv, ct, fitinfo = getFitValues(card, model=options.model,
                                           unblind=options.unblind,
                                           printCommand=options.printCommand)
            fitdata[(cv,ct)] = fitinfo

        fnames = []
        for cv_ in [0.5, 1.0, 1.5]:
            if not cv_ in [v for v,_ in fitdata.keys()]: continue
            csvfname = 'fits%s_cv_%s.csv' % (tag, str(cv_).replace('.','p'))
            with open(csvfname, 'w') as csvfile:
                csvfile.write('cv,cf,median,downerror,uperror\n')
                for cv,ct in sorted(fitdata.keys()):
                    if not cv == cv_: continue
                    values = [cv, ct]
                    values += [fitdata[(cv,ct)][x] for x in ['median','downerror','uperror']]
                    csvfile.write(','.join(map(str, values)) + '\n')
            fnames.append(csvfname)
    
        print "Wrote limits to: %s" % (" ".join(fnames))

    if options.runmode.lower() == 'sig':
        sigdata = {}
        for card in cards:
            cv, ct, significance = getSignificance(card, model=options.model,
                                                   unblind=options.unblind,
                                                   printCommand=options.printCommand)
            sigdata[(cv,ct)] = significance

        fnames = []
        for cv_ in [0.5, 1.0, 1.5]:
            if not cv_ in [v for v,_ in sigdata.keys()]: continue
            csvfname = 'significance%s_cv_%s.csv' % (tag, str(cv_).replace('.','p'))
            with open(csvfname, 'w') as csvfile:
                csvfile.write('cv,cf,significance\n')
                for cv,ct in sorted(sigdata.keys()):
                    if not cv == cv_: continue
                    values = [cv, ct]
                    values += [sigdata[(cv,ct)][x] for x in ['value']]
                    csvfile.write(','.join(map(str, values)) + '\n')
            fnames.append(csvfname)

        print "Wrote significance to: %s" % (" ".join(fnames))

    return 0

if __name__ == '__main__':
    from optparse import OptionParser
    usage = """
    %prog [options] dir/
    %prog [options] card.txt
    %prog [options] workspace1.root workspace2.root

    Call combine on all datacards ("*.card.txt") in an input directory.
    Collect the limit, 1, and 2 sigma bands from the output, and store
    them together with the cv and ct values (extracted from the filename)
    in a .csv file.

    Note that you need to have 'combine' in your path. Try:
    cd /afs/cern.ch/user/s/stiegerb/combine/ ; cmsenv ; cd -
    """
    parser = OptionParser(usage=usage)
    parser.add_option("-r","--run", dest="runmode", type="string", default="limits",
                      help="What to run (limits|ctcvlimits|fit|sig)")
    parser.add_option("-j","--jobs", dest="jobs", type="int", default=1,
                      help="Number of jobs to run in parallel")
    parser.add_option("-t","--tag", dest="tag", type="string", default=None,
                      help="Tag to put in name of output csv files")
    parser.add_option("-m","--model", dest="model", type="string", default="K6",
                      help="Toggle to configure combine commands")
    parser.add_option("-u","--unblind", dest="unblind", action='store_true',
                      help="For limits mode: add the observed limit")
    parser.add_option("-p","--printCommand", dest="printCommand", action='store_true',
                      help="Print the combine command that is run")
    (options, args) = parser.parse_args()

    sys.exit(main(args, options))
