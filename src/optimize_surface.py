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
import json, os, image, reproject

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='...')
    parser.add_argument('-c','--cam_directions', type=float, nargs=3, action='append', 
    help="list of camera direction vectors. Use a new -c for each camera, e.g. -c 1 0 -1 -c -1 0 -1")
    
    parser.add_argument('-i','--image_paths', type=str, nargs='+',
    help="list of image paths of desired surface appearances, e.g. -i image1.png image2.png")
    parser.add_argument('-o','--output_dir', type=str, default="models", help="folder where the optimized heights and colors are saved (default: models)")
    parser.add_argument('--no_mesh', action='store_true', help="do not project the images onto the surface and write the textured mesh at the end")
    parser.add_argument('--paper_settings', action='store_true', help="restore the behavior of the original release (v1.0): camera rays start on the fixed plane z = 1 and the neighbor loss is summed")
    
    args = parser.parse_args()
    if not args.cam_directions or not args.image_paths or len(args.cam_directions) != len(args.image_paths):
        parser.error("please give one image (-i) for every camera direction (-c)")
    for d in args.cam_directions:
        if d[2] >= 0:
            parser.error("camera direction %s does not look down at the surface: its z component must be negative" % " ".join("%g" % v for v in d))
    for p in args.image_paths:
        try:
            image.get_tensor_from_image(p)
        except Exception as e:
            parser.error("could not read image %s (%s)" % (p, e))
    cam_directions = np.array(args.cam_directions)
    epsilon = np.random.random((len(cam_directions), 3))/100
    cam_directions = cam_directions+epsilon #prevent singular matrix (e.g. ray parallel to edges of bars in heightfield)
    image_paths = [os.path.abspath(p) for p in args.image_paths] #absolute, so reproject.py works from any folder

    init_H = heightfield.get_uniform_H(4, 4, center=0.5)
    print("Running with " + str(sys.version))
   
    num_epochs = 295
    H1, COL1, result_cols, desired_cols = grad_descent.grad_descent(num_epochs, init_H, cam_directions, image_paths, sim_annealing = True, use_barrier_loss = True, use_neighbor_loss = True, optim_type="Adam", heaviside_fn = "tan", num_rays = 16, num_repeats=2, output_dir=args.output_dir, paper_settings=args.paper_settings)
    if not args.no_mesh:
        prefix = grad_descent.grad_descent.last_output
        meta = json.load(open(prefix + "_cameras.json"))
        reproject.export_surface(np.load(prefix + "_heights.npy"), np.load(prefix + "_colors.npy"), meta["camera_directions"], meta["image_paths"], meta["camera_z"], prefix + "_surface")
