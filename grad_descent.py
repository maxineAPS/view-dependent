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

def grad_descent(num_epochs, H, cam_directions, image_paths, use_barrier_loss = True, use_neighbor_loss = False, sim_annealing = True, optim_type = "Adam", heaviside_fn = None, heaviside_k = 0.1, num_repeats = 1, num_rays = 32):
  
    COL = heightfield.get_white_COL(H.shape[0]*num_repeats)
    now = datetime.now()
    date_time = now.strftime("%m_%d_%Y_%H-%M-%S")
    num_cams = len(cam_directions)
    num_strips = H.shape[0]*num_repeats
    ray_width = 1/num_rays
  
    original_ray_origins = [[], [], [], []]
    ray_origins = copy.deepcopy(original_ray_origins)
    coords = []
  
    schedule = torch.zeros(50) #update colors for 10 steps, then heights for 20 steps
    schedule[10:20] = 1
    schedule[40:50] = 1

    grad_types = schedule.repeat(20)

    for i in range(num_rays):
        for k in range(num_rays):
            coord = np.array([i*ray_width + ray_width/2, k*ray_width + ray_width/2, 1])
            coords.append(coord)

            for q in range(num_cams):   
                curr_origin = coord - 20*cam_directions[q]
                curr_origin[2] = curr_origin[2].item()
                ray_origins[q].append(curr_origin)

    H = torch.tensor(H, dtype=torch.float, requires_grad = True)
    COL = torch.tensor(COL, dtype=torch.float, requires_grad = True)

    ray_packs = []

    for t in range(num_cams):
        ray_packs.append(rendering.get_ray_packs(ray_origins[t], cam_directions[t], num_strips))

    desired_cols = []
    for i in range(num_cams):
        desired_cols.append(image.get_tensor_from_image(image_paths[i], (64, 64), (num_rays, num_rays)))
  
    if sim_annealing:
        H, COL = simannealing.sim_annealing(H, COL, ray_packs, num_cams, num_repeats, heaviside_fn, heaviside_k, desired_cols)

    print("--------------------------------------------------------- \n Beginning grad descent...\n---------------------------------------------------------")

    if optim_type == "Adam":
        optimizer = torch.optim.AdamW([H, COL],lr=0.1)
    
    if optim_type == "SGD":
        optimizer = torch.optim.SGD([H, COL],lr=0.1, momentum=0.9)

    for j in range(1, num_epochs):
        
        if j%50 == 0:
      
            repeated_H = H.repeat(num_repeats, num_repeats)
            torch.save(repeated_H, 'models/' + date_time + '_heights.pt')
            torch.save(COL, 'models/' + date_time + '_colors.pt')
            print("--------------------------------------------------------- \n Saving surface heights and colors to models directory...\n---------------------------------------------------------")
        
        change = False
    
        if j%100 == 0:
            H = heightfield.double_resolution(H)
            COL = heightfield.double_resolution(COL)
            H = torch.tensor(H, dtype=torch.float)
            COL = torch.tensor(COL, dtype=torch.float)
            num_strips = num_strips*2
            desired_cols = []
            
            for q in range(num_cams):
                desired_cols.append(image.get_tensor_from_image(image_paths[q], (64, 64), (num_rays, num_rays)))
            change = True

        if j%100 == 95:
            num_rays = num_rays*2
            ray_width = ray_width/2
            change = True
    
        if j%100 == 95 or j%100 == 0:
            coords = []
            change = True
      
            ray_origins = copy.deepcopy(original_ray_origins) 
            for i in range(num_rays):
                for k in range(num_rays):
                    coord = np.array([i*ray_width + ray_width/2, k*ray_width + ray_width/2, 1])
                    coords.append(coord)
                    
                    for q in range(num_cams):    
                        curr_origin = coord - 20*cam_directions[q] 
                        curr_origin[2] = curr_origin[2].item()
                        ray_origins[q].append(curr_origin)

            ray_packs = []
            for t in range(num_cams):
                ray_packs.append(rendering.get_ray_packs(ray_origins[t], cam_directions[t], num_strips))
        
            H.requires_grad = True
            COL.requires_grad = True
      
            desired_cols = []
            for i in range(num_cams):
                desired_cols.append(image.get_tensor_from_image(image_paths[i], (64, 64), (num_rays, num_rays)))

        if int(grad_types[j].item()) == 0:
      
            H.requires_grad = False
            COL.requires_grad = True
            lr = 0.05
      
        elif int(grad_types[j].item()) == 1:
            H.requires_grad = True
            COL.requires_grad = False 
            COL = COL.detach().numpy()
            COL = torch.tensor(COL, dtype=torch.float, requires_grad = False)
            if j > 49:
                lr = 0.03
      
        elif int(grad_types[j].item()) == 2:
            H.requires_grad = True
            COL.requires_grad = True
            H = torch.tensor(H, dtype=torch.float, requires_grad = True)
            COL = torch.tensor(COL, dtype=torch.float, requires_grad = True)

        if j > 0:
            if int(grad_types[j].item()) != int(grad_types[j-1].item()):
                change = True
        
        if change:
            if optim_type == "Adam":
                optimizer = torch.optim.AdamW([H, COL],lr=lr)
            if optim_type == "SGD":
                optimizer = torch.optim.SGD([H, COL],lr=lr, momentum=0.9)
    
        result_cols = rendering.forward(H, COL, ray_packs, num_cams, num_repeats=num_repeats, heaviside_fn = heaviside_fn, heaviside_k = heaviside_k)
        mse_loss = 0
        for q in range(num_cams):
            mse_loss += torch.nn.functional.mse_loss(result_cols[q].double(), desired_cols[q].double())

        if j % 10 == 0:
            print("STEP " + str(j) + "\t LOSS: " + str(mse_loss.item()/2))

        if use_barrier_loss:
            barrier_loss = opt.barrier_fn(H, min_val = 0.1, max_val = 1.5)
            mse_loss = mse_loss + 0.02*barrier_loss

        if use_neighbor_loss:
            neighbor_loss = opt.neighbor_fn(H)
            mse_loss = mse_loss + 0.5*neighbor_loss
    
        optimizer.zero_grad()
        mse_loss.backward()
        optimizer.step()

    repeated_H = H.repeat(num_repeats, num_repeats)
    return repeated_H, COL, result_cols, desired_cols
