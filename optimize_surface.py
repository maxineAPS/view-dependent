#Main function for optimizing heightfields
#Author: Maxine Perroni-Scharf
#Date: June 2023


import numpy as np
import torch
import torch
import heightfield
import sys
import grad_descent
import argparse

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='...')
    parser.add_argument('-c','--cam_directions', type=int, nargs='+', action='append', 
    help="list of camera direction vectors. Use a new -c for each camera, e.g. -c 1, 0, -1 -c -1, 0, -1")
    
    parser.add_argument('-i','--image_paths', type=str, nargs='+',
    help="list of image paths of desired surface appearances, e.g. -i image1.png image2.png")
    
    args = parser.parse_args()
    cam_directions = np.array(args.cam_directions)
    epsilon = np.random.random((len(cam_directions), 3))/100
    cam_directions = cam_directions+epsilon #prevent singular matrix (e.g. ray parallel to edges of bars in heightfield)
    image_paths = args.image_paths

    init_H = heightfield.get_uniform_H(4, 4, center=0.5)
    print("Running with " + str(sys.version))
   
    num_epochs = 295
    H1, COL1, result_cols, desired_cols = grad_descent.grad_descent(num_epochs, init_H, cam_directions, image_paths, sim_annealing = True, use_barrier_loss = True, use_neighbor_loss = True, optim_type="Adam", heaviside_fn = "tan", num_rays = 16, num_repeats=2)
