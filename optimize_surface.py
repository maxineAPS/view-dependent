import numpy as np
import torch
import time
import copy
import torch
import rendering
import heightfield
import image
import opt
import sys
import simannealing
from datetime import datetime
import grad_descent


if __name__ == '__main__':

    print("Running with " + str(sys.version))

    init_H = heightfield.get_uniform_H(4, 4, center=0.5)

    cam_direction_1 = np.array([1, 0.000001, -1])

    cos = [1, 0.94, 0.766, 0.5, 0.174, -0.174, -0.5, -0.766, -0.94, -1]
    sin = [0.001, 0.34, 0.643, 0.866, 0.984, 0.984, 0.866, 0.643, 0.34, 0.001]

    np.set_printoptions(threshold=1000)
    torch.set_printoptions(threshold = 1000)

    cam_direction_1 = np.array([1, 0.0001, -2])
    cam_direction_2 = np.array([1, 0.0001, -10])
    cam_direction_3 = np.array([-1, 0.00001, -2])

    cam_directions = np.array([cam_direction_1, cam_direction_3])#, cam_direction_2, cam_direction_3])

    num_epochs = 260
    p1 = "test_images/forest.png"
    p2 = "test_images/cat.png"
    p3 = "test_images/clouds.png"
    image_paths = [p1, p3]
    H1, COL1, result_cols, desired_cols = grad_descent.grad_descent(num_epochs, init_H, cam_directions, image_paths, sim_annealing = True, use_barrier_loss = True, use_neighbor_loss = True, optim_type="Adam", heaviside_fn = "tan", num_rays = 16, num_repeats=2)


