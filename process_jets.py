import os

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-n', '--name', action='store', required=True, help='File to process')
parser.add_argument('-d', '--data', action='store_true', default=False, help='Apply NTNI cuts for training background')
parser.add_argument('-c', '--channel', action='store', choices=['l', 'lep', 'leptonic', 'h', 'had', 'hadronic'], default='l', help='Channel to process')
args = parser.parse_args()

import ROOT

import numpy as np

from array import array

def main():
    f = ROOT.TFile.Open('inputs/%s_RNN.root' % args.name)
    t = f.Get('output')

    N_lep = array('i', [0])
    N_jet30 = array('i', [0])
    N_bjet30_fixed70 = array('i', [0])
    flag_passedIso = array('i', [0])
    flag_passedPID = array('i', [0])
    j1 = ROOT.vector('float')()
    j2 = ROOT.vector('float')()
    j3 = ROOT.vector('float')()
    j4 = ROOT.vector('float')()
    j5 = ROOT.vector('float')()
    j6 = ROOT.vector('float')()
    j7 = ROOT.vector('float')()
    j8 = ROOT.vector('float')()
    j9 = ROOT.vector('float')()

    t.SetBranchAddress('N_lep', N_lep)
    t.SetBranchAddress('N_jet30', N_jet30)
    t.SetBranchAddress('N_bjet30_fixed70', N_bjet30_fixed70)
    t.SetBranchAddress('flag_passedIso', flag_passedIso)
    t.SetBranchAddress('flag_passedPID', flag_passedPID)
    t.SetBranchAddress('jet_1', j1)
    t.SetBranchAddress('jet_2', j2)
    t.SetBranchAddress('jet_3', j3)
    t.SetBranchAddress('jet_4', j4)
    t.SetBranchAddress('jet_5', j5)
    t.SetBranchAddress('jet_6', j6)
    t.SetBranchAddress('jet_7', j7)
    t.SetBranchAddress('jet_8', j8)
    t.SetBranchAddress('jet_9', j9)

    jets = []
    
    for i in range(t.GetEntries()):
        if (i % 10000 == 0): print('Event %d/%d' % (i, t.GetEntries()))
        t.GetEntry(i)
        if args.channel[0] == 'l':
            if not (N_lep[0] > 0 and N_bjet30_fixed70[0] > 0): continue
        else:
            if not (N_lep[0] == 0 and N_jet30[0] >= 3 and N_bjet30_fixed70[0] > 0): continue
        if (args.data and flag_passedIso[0] and flag_passedPID[0]): continue
        ej = []
        if (len(j1) > 0): ej.append([j1[0], j1[1], j1[2], j1[3], j1[4]])
        if (len(j2) > 0): ej.append([j2[0], j2[1], j2[2], j2[3], j2[4]])
        if (len(j3) > 0): ej.append([j3[0], j3[1], j3[2], j3[3], j3[4]])
        if (len(j4) > 0): ej.append([j4[0], j4[1], j4[2], j4[3], j4[4]])
        if (len(j5) > 0): ej.append([j5[0], j5[1], j5[2], j5[3], j5[4]])
        if (len(j6) > 0): ej.append([j6[0], j6[1], j6[2], j6[3], j6[4]])
        if (len(j7) > 0): ej.append([j7[0], j7[1], j7[2], j7[3], j7[4]])
        if (len(j8) > 0): ej.append([j8[0], j8[1], j8[2], j8[3], j8[4]])
        if (len(j9) > 0): ej.append([j9[0], j9[1], j9[2], j9[3], j9[4]])
        ej = sorted(ej, key=lambda x: x[4], reverse=True)
        for j in range(9 - len(ej)): ej.append([-999] * 5)
        jets.append(ej)
        pass

    jets = np.array(jets)

    np.save('arrays/%s%s_%s_jets.npy' % (args.name, '_IsoPID' if args.data else '', 'leptonic' if args.channel[0] == 'l' else 'hadronic'), jets)

    return

if __name__ == '__main__':
    main()
