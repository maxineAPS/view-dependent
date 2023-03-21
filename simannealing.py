import torch
import rendering
import math
import numpy as np

def sim_annealing(H, COL, ray_packs, num_cams, num_repeats, heaviside_fn, heaviside_k, desired_cols, start_temp = 3, num_steps = 50):
  old_loss = 10
  current_temp = start_temp
    
  for i in range(num_steps):

    #randomize_H
    H_NEW = H + 0.05*(torch.rand(H.shape, dtype=torch.float) - 0.5)
    H_NEW = torch.clamp(H_NEW, 0.1, 3.9)
    COL_NEW = COL + 0.05*(torch.rand(COL.shape, dtype=torch.float) - 0.5)
    COL_NEW = torch.clamp(COL_NEW, 0, 1)
     
    result_cols = rendering.forward(H, COL, ray_packs, num_cams, num_repeats=num_repeats, heaviside_fn = heaviside_fn, heaviside_k = heaviside_k)
    mse_loss = 0
    for j in range(num_cams):
      mse_loss += torch.nn.functional.mse_loss(result_cols[j].double(), desired_cols[j].double())

    result_cols_new = rendering.forward(H_NEW, COL_NEW, ray_packs, num_cams, num_repeats=num_repeats, heaviside_fn = heaviside_fn, heaviside_k = heaviside_k)
    mse_loss_new = 0
    for j in range(num_cams):
      mse_loss_new += torch.nn.functional.mse_loss(result_cols_new[j].double(), desired_cols[j].double())


    old_loss = mse_loss.item()
    new_loss = mse_loss_new.item()
    
    if (new_loss > old_loss):
      jumpProb = math.exp((old_loss - new_loss) / current_temp) #computes the probability of accepting a worse point
      
      if (np.random.uniform(0, 1) <= jumpProb): #determines whether we jump to worse point or stay with prior point
        H = H_NEW
        COL = COL_NEW
        old_loss = new_loss
       
    else:
      H = H_NEW
      COL = COL_NEW
      old_loss = new_loss

    current_temp = current_temp * 0.99
      
    print("STEP: " + str(i) + "\t LOSS: " + str(old_loss))
          
  H = H.detach().numpy()  
  COL = COL.detach().numpy()
  H = torch.tensor(H, dtype=torch.float, requires_grad = True)
  COL = torch.tensor(COL, dtype=torch.float, requires_grad = True)

  return H, COL