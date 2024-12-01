# This script shuffles the lines of Explore text files 

import random

def shuffle_lines(input_file, output_file):
    with open(input_file, 'r') as f:
        lines = f.readlines()
        random.shuffle(lines)
    
    with open(output_file, 'w') as f:
        f.writelines(lines)

# Original file, then shuffled file
input_file = 'explore-all.txt'
output_file = 'explore-all-randomized.txt'
shuffle_lines(input_file, output_file)
