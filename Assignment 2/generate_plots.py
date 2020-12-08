import matplotlib.pyplot as plt
import sys
import os
import numpy as np

def get_data_dict(directory):
    mining_power = {}
    frac_mined = {}
    for exp in os.listdir(directory):
        if exp != "seed":
            iat = exp.split('_')[1]
            pf = exp.split('_')[3]
            if pf not in frac_mined.keys():
                frac_mined[pf] = {}
                mining_power[pf] = {}
            if iat not  in frac_mined[pf].keys():
                frac_mined[pf][iat] = {}
                mining_power[pf][iat] = {}
            
            for node in os.listdir(os.path.join(directory,exp)):
                if node.startswith('blockchain'):
                    port = node.split('_')[2][:-4]
                    with open(os.path.join(directory,exp,node),'r') as f:
                        lines = f.readlines()
                        for line in lines:
                            if line.startswith('Mining Power Utilization'):
                                mining_power[pf][iat][port]=float(line.split(":")[-1].strip())
                            if line.startswith('Fraction Mined in Longest Chain'):
                                frac_mined[pf][iat][port]=float(line.split(":")[-1].strip())

    return mining_power,frac_mined

def plot_graphs(mining_power,frac_mined,adversary_port):
    pf_list = [int(x) for x in mining_power.keys()]
    iat_list = [int(x) for x in mining_power[str(pf_list[0])]]
    iat_list.sort()
    pf_list.sort()
    #Mining_power
    plt.figure()
    plt.title("Mining Power Utilization vs Inter-Arrival time")
    plt.xlabel("Inter-Arrival time (in sec)")
    plt.ylabel("Mining Power Utilizaiton")
    for pf in pf_list:
        mining_powers = []
        for iat in iat_list:
            mining_powers.append(np.mean(np.array(list(mining_power[str(pf)][str(iat)].values()))))
        plt.plot(iat_list,mining_powers,label=str(pf*10)+'% nodes flooded')
    plt.legend()
    plt.savefig('Mining_Power_Utilization.png')

    #Fraction mined by adversary
    plt.figure()
    plt.title("Fraction of main chain blocks mined by adversary vs Inter-Arrival time")
    plt.xlabel("Inter-Arrival time (in sec)")
    plt.ylabel("Fraction mined by adversary")
    for pf in pf_list:
        fracs = []
        for iat in iat_list:
            fracs.append(frac_mined[str(pf)][str(iat)][adversary_port])
        fracs = np.array(fracs)
        
        plt.plot(iat_list,fracs,label=str(pf*10)+'% nodes flooded')
    plt.legend()
    plt.savefig('Fraction_mined_by_adversary.png')

if __name__ == "__main__":
    directory = sys.argv[1]
    adversary_port = sys.argv[2]
    mining_power,frac_mined = get_data_dict(directory)
    plot_graphs(mining_power,frac_mined,adversary_port)