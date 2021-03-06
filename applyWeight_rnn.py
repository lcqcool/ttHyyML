import os

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--channel', action='store', choices=['l', 'lep', 'leptonic', 'h', 'had', 'hadronic'], default='l', help='Channel to process')
parser.add_argument('-i', '--input', action='store', required=True, help='Name of input ROOT file to apply weights to')
parser.add_argument('-n', '--name', action='store', required=True, help='Name to be appended to output file') 
args = parser.parse_args()

import math

import ROOT
from root_numpy import root2array

from array import array

import numpy as np

import pickle

from sklearn.preprocessing import StandardScaler

from keras import models

def process_leptonic():
    # load model
    model = models.load_model('models/model_leptonic_rnn_temp.h5')
    
    # open file and get tree
    infile = ROOT.TFile.Open('inputs/%s_RNN.root' % args.input)
    intree = infile.Get('output')

    in_mass_yy = array('f', [0])
    in_weight = array('f', [0])
    in_N_lep = array('i', [0])
    in_N_jet30_cen = array('i', [0])
    in_N_bjet30_fixed70 = array('i', [0])
    in_flag_passedIso = array('i', [0])
    in_flag_passedPID = array('i', [0])

    intree.SetBranchAddress('mass_yy', in_mass_yy)
    intree.SetBranchAddress('weight', in_weight)
    intree.SetBranchAddress('N_lep', in_N_lep)
    intree.SetBranchAddress('N_jet30_cen', in_N_jet30_cen)
    intree.SetBranchAddress('N_bjet30_fixed70', in_N_bjet30_fixed70)
    intree.SetBranchAddress('flag_passedIso', in_flag_passedIso)
    intree.SetBranchAddress('flag_passedPID', in_flag_passedPID)

    # create new tree
    outtree = ROOT.TTree(args.name, args.name)
    outtree.SetDirectory(0)

    # create branches for tree
    out_mass_yy = array('f', [0])
    out_weight = array('f', [0])
    out_flag_passedIso = array('i', [0])
    out_flag_passedPID = array('i', [0])
    out_nnweight = array('f', [0])
    outtree.Branch('mass_yy', out_mass_yy, 'mass_yy/F')
    outtree.Branch('weight', out_weight, 'weight/F')
    outtree.Branch('flag_passedIso', out_flag_passedIso, 'flag_passedIso/I')
    outtree.Branch('flag_passedPID', out_flag_passedPID, 'flag_passedPID/I')
    outtree.Branch('nnweight', out_nnweight, 'nnweight/F')

    jets = np.load('arrays/%s_leptonic_jets.npy' % args.input)
    photons = np.load('arrays/%s_leptonic_photons.npy' % args.input)
    lepmets = np.load('arrays/%s_leptonic_lepmets.npy' % args.input)
    
    scalers = pickle.load(open('scalers_leptonic.p', 'rb'))
    
    pts = jets[:, :, 0].flatten()
    mask = pts != -999
    pts[mask] = scalers['pt'].transform(pts[mask])
    jets[:, :, 0] = pts.reshape(-1, 7)
    
    Es = jets[:, :, 3].flatten()
    Es[mask] = scalers['E'].transform(Es[mask])
    jets[:, :, 3] = Es.reshape(-1, 7)
    
    pts = photons[:, :, 0].flatten()
    pts = scalers['pt'].transform(pts)
    photons[:, :, 0] = pts.reshape(-1, 2)
    
    Es = photons[:, :, 3].flatten()
    Es = scalers['E'].transform(Es)
    photons[:, :, 3] = Es.reshape(-1, 2)

    pts = lepmets[:, :, 0].flatten()
    pts = scalers['pt'].transform(pts)
    lepmets[:, :, 0] = pts.reshape(-1, 2)
    
    Es = lepmets[:, :, 3].flatten()
    Es = scalers['E'].transform(Es)
    lepmets[:, :, 3] = Es.reshape(-1, 2)

    if args.input[0:4] == 'data':
        if (intree.GetEntries('N_lep > 0 && N_bjet30_fixed70 == 0 && N_jet30_cen > 0 && mass_yy > 80000') != len(jets) or intree.GetEntries('N_lep > 0 && N_bjet30_fixed70 == 0 && N_jet30_cen > 0 && mass_yy > 80000') != len(photons) or intree.GetEntries('N_lep > 0 && N_bjet30_fixed70 == 0 && N_jet30_cen > 0 && mass_yy > 80000') != len(lepmets)):
            print('Not the same number of events! Exiting!!!')
            return
    else:
        if (intree.GetEntries('N_lep > 0 && N_bjet30_fixed70 > 0 && mass_yy > 80000') != len(jets) or intree.GetEntries('N_lep > 0 && N_bjet30_fixed70 > 0 && mass_yy > 80000') != len(photons) or intree.GetEntries('N_lep > 0 && N_bjet30_fixed70 > 0 && mass_yy > 80000') != len(lepmets)):
            print('Not the same number of events! Exiting!!!')
            return

    events = np.concatenate((photons, lepmets, jets), axis=1)
    score = model.predict(events)

    j = 0
    for i in range(intree.GetEntries()):
        intree.GetEntry(i)
        if args.input[0:4] == 'data':
            if not (in_N_lep[0] > 0 and in_N_bjet30_fixed70[0] == 0 and in_N_jet30_cen[0] > 0 and in_mass_yy[0] > 80000): continue
        else:
            if not (in_N_lep[0] > 0 and in_N_bjet30_fixed70[0] > 0 and in_mass_yy[0] > 80000): continue
        out_mass_yy[0] = in_mass_yy[0]
        out_weight[0] = in_weight[0]
        out_flag_passedIso[0] = in_flag_passedIso[0]
        out_flag_passedPID[0] = in_flag_passedPID[0]
        out_nnweight[0] = score[j]
        outtree.Fill()
        j += 1

    # save new tree
    outfile = ROOT.TFile('outputs/%s_leptonic_%s.root' % (args.input, args.name), 'RECREATE')
    outtree.Write()
    outfile.Close()

    return

def process_hadronic():
    # load model
    model = models.load_model('models/model_hadronic_rnn_temp.h5')
    
    # open file and get tree
    infile = ROOT.TFile.Open('inputs/%s_RNN.root' % args.input)
    intree = infile.Get('output')

    in_mass_yy = array('f', [0])
    in_weight = array('f', [0])
    in_N_lep = array('i', [0])
    in_N_jet30 = array('i', [0])
    in_N_bjet30_fixed70 = array('i', [0])
    in_flag_passedIso = array('i', [0])
    in_flag_passedPID = array('i', [0])

    intree.SetBranchAddress('mass_yy', in_mass_yy)
    intree.SetBranchAddress('weight', in_weight)
    intree.SetBranchAddress('N_lep', in_N_lep)
    intree.SetBranchAddress('N_jet30', in_N_jet30)
    intree.SetBranchAddress('N_bjet30_fixed70', in_N_bjet30_fixed70)
    intree.SetBranchAddress('flag_passedIso', in_flag_passedIso)
    intree.SetBranchAddress('flag_passedPID', in_flag_passedPID)

    # create new tree
    outtree = ROOT.TTree(args.name, args.name)
    outtree.SetDirectory(0)

    # create branches for tree
    out_mass_yy = array('f', [0])
    out_weight = array('f', [0])
    out_flag_passedIso = array('i', [0])
    out_flag_passedPID = array('i', [0])
    out_nnweight = array('f', [0])
    outtree.Branch('mass_yy', out_mass_yy, 'mass_yy/F')
    outtree.Branch('weight', out_weight, 'weight/F')
    outtree.Branch('flag_passedIso', out_flag_passedIso, 'flag_passedIso/I')
    outtree.Branch('flag_passedPID', out_flag_passedPID, 'flag_passedPID/I')
    outtree.Branch('nnweight', out_nnweight, 'nnweight/F')

    jets = np.load('arrays/%s_hadronic_jets.npy' % args.input)
    photons = np.load('arrays/%s_hadronic_photons.npy' % args.input)
    
    scalers = pickle.load(open('scalers_hadronic.p', 'rb'))
    
    pts = jets[:, :, 0].flatten()
    mask = pts != -999
    pts[mask] = scalers['pt'].transform(pts[mask])
    jets[:, :, 0] = pts.reshape(-1, 9)
    
    Es = jets[:, :, 3].flatten()
    Es[mask] = scalers['E'].transform(Es[mask])
    jets[:, :, 3] = Es.reshape(-1, 9)
    
    pts = photons[:, :, 0].flatten()
    pts = scalers['pt'].transform(pts)
    photons[:, :, 0] = pts.reshape(-1, 2)
    
    Es = photons[:, :, 3].flatten()
    Es = scalers['E'].transform(Es)
    photons[:, :, 3] = Es.reshape(-1, 2)

    if (intree.GetEntries('N_lep == 0 && N_jet30 >= 3 && N_bjet30_fixed70 > 0 && mass_yy > 80000') != len(jets) or intree.GetEntries('N_lep == 0 && N_jet30 >= 3 && N_bjet30_fixed70 > 0 && mass_yy > 80000') != len(photons)):
        print('Not the same number of events! Exiting!!!')
        return

    photons = np.concatenate((photons, np.ones((photons.shape[0], photons.shape[1], 1))), axis=2)
    events = np.concatenate((photons, jets), axis=1)
    score = model.predict(events)

    j = 0
    for i in range(intree.GetEntries()):
        intree.GetEntry(i)
        if not (in_N_lep[0] == 0 and in_N_jet30[0] >= 3 and in_N_bjet30_fixed70[0] > 0): continue
        out_mass_yy[0] = in_mass_yy[0]
        out_weight[0] = in_weight[0]
        out_flag_passedIso[0] = in_flag_passedIso[0]
        out_flag_passedPID[0] = in_flag_passedPID[0]
        out_nnweight[0] = score[j]
        outtree.Fill()
        j += 1

    # save new tree
    outfile = ROOT.TFile('outputs/%s_hadronic_%s.root' % (args.input, args.name), 'RECREATE')
    outtree.Write()
    outfile.Close()

    return

def main():
    if args.channel[0] == 'l':
        process_leptonic()
    else:
        process_hadronic()

    return

if __name__ == '__main__':
    main()
