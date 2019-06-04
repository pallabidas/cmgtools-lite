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
    tag = re.match(r'.*\_([\dpm]+).*\.card\.(txt|root)', os.path.basename(card))
    if tag == None:
        print "Couldn't figure out this one: %s" % card
        return

    tag = tag.groups()[0]
    tagf = tag.replace('p', '.').replace('m','-')
    cp = float(tagf)
    if printout:
        print "%-40s CP=%5.2f : " % (os.path.basename(card), cp),
    return cp, tag

def getLimits(card, unblind=False, printCommand=False):
    """
    Run combine on a single card, return a tuple of 
    (cp,twosigdown,onesigdown,exp,onesigup,twosigup)
    """
    cp,tag = parseName(card, printout=False)
    printout = "%-40s CP=%5.2f : " % (os.path.basename(card), cp)

    combinecmd =  "combine -M AsymptoticLimits"
    if not unblind:
        combinecmd += " --run blind"
    combinecmd += " -m 125 --verbose 0 -n cp%s"%tag
    #combinecmd += " --rMin=0 --rMax=20 --X-rtd ADDNLL_RECURSIVE=0 --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.01 --cminPreScan "

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

    return cp, liminfo

def getFitValues(card, unblind=False, printCommand=False):
    """
    Run combine on a single card, return a tuple of fitvalues
    (cp,median,downerror,uperror)
    """
    cp,tag = parseName(card)
    if printCommand: print ""

    combinecmd =  "combine -M MaxLikelihoodFit"
    combinecmd += " -m 125 --verbose 0 -n cp%s"%tag
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
    return cp, fitinfo

def getSignificance(card, unblind=False, printCommand=False):
    """
    Run combine on a single card, return significance
    """
    cp,tag = parseName(card)
    if printCommand: print ""

    combinecmd =  "combine -M Significance --signif"
    combinecmd += " -m 125 --verbose 0 -n cp%s"%tag
    #combinecmd += " --rMin=0 --rMax=20 --X-rtd ADDNLL_RECURSIVE=0 --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.01 --cminPreScan "
    comboutput = runCombineCommand(combinecmd, card, verbose=printCommand)

    significance = {}
    for line in comboutput.split('\n'):
        if line.startswith('Significance'):
            print(line)
            significance['value'] = float(line.rsplit(':', 1)[1].strip())

    print "\033[92m%5.2f\033[0m" %( significance['value'])
    return cp, significance


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
        csvfname = 'limits_CP.csv'
        with open(csvfname, 'w') as csvfile:
            if options.unblind:
                csvfile.write('fname,cp,twosigdown,onesigdown,exp,onesigup,twosigup,obs\n')
            else:
                csvfile.write('fname,cp,twosigdown,onesigdown,exp,onesigup,twosigup\n')

            for card in cards:
                cp, liminfo = getLimits(card, unblind=options.unblind, printCommand=options.printCommand) 
                values = [card, cp]
                values += [liminfo[x] for x in ['twosigdown','onesigdown','exp','onesigup','twosigup']]
                if options.unblind:
                    values += [liminfo['obs']]
                csvfile.write(','.join(map(str, values)) + '\n')

        print "All done. Wrote limits to: %s" % csvfname


    if options.runmode.lower() == 'fit':
        fitdata = {} # (cp) -> (fit, down, up)
        for card in cards:
            cp, fitinfo = getFitValues(card, unblind=options.unblind, printCommand=options.printCommand)
            fitdata[cp] = fitinfo

        fnames = []
        csvfname = 'fits_CP.csv'
        with open(csvfname, 'w') as csvfile:
            csvfile.write('cp,median,downerror,uperror\n')
            for cp in sorted(fitdata.keys()):
                values = [cp]
                values += [fitdata[cp][x] for x in ['median','downerror','uperror']]
                csvfile.write(','.join(map(str, values)) + '\n')
        fnames.append(csvfname)
    
        print "Wrote limits to: %s" % (" ".join(fnames))

    if options.runmode.lower() == 'sig':
        sigdata = {}
        for card in cards:
            cp, significance = getSignificance(card, unblind=options.unblind, printCommand=options.printCommand)
            sigdata[cp] = significance

        fnames = []
        csvfname = 'significance_CP.csv'
        with open(csvfname, 'w') as csvfile:
            csvfile.write('cp,significance\n')
            for cp in sorted(sigdata.keys()):
                values = [cp]
                values += [sigdata[cp][x] for x in ['value']]
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
    them together with the cp values (extracted from the filename)
    in a .csv file.

    Note that you need to have 'combine' in your path. Try:
    cd /afs/cern.ch/user/s/stiegerb/combine/ ; cmsenv ; cd -
    """
    parser = OptionParser(usage=usage)
    parser.add_option("-r","--run", dest="runmode", type="string", default="limits",
                      help="What to run (limits|fit|sig)")
    parser.add_option("-j","--jobs", dest="jobs", type="int", default=1,
                      help="Number of jobs to run in parallel")
    parser.add_option("-t","--tag", dest="tag", type="string", default=None,
                      help="Tag to put in name of output csv files")
    parser.add_option("-u","--unblind", dest="unblind", action='store_true',
                      help="For limits mode: add the observed limit")
    parser.add_option("-p","--printCommand", dest="printCommand", action='store_true',
                      help="Print the combine command that is run")
    (options, args) = parser.parse_args()

    sys.exit(main(args, options))
