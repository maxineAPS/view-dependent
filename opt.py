import torch

def barrier_fn(H, min_val, max_val):

  max = torch.full(H.shape, max_val, dtype=torch.float)
  min = torch.full(H.shape, min_val, dtype=torch.float)
  max_minus_H = max - H
  H_minus_min = H - min
  logmax = torch.log(max_minus_H)
  logmin = torch.log(H_minus_min)
  loss = (-torch.sum(logmax) - torch.sum(logmin))/H.shape[0]
  return loss

def neighbor_fn(H):

  diff = 0
  for i in range(1, H.shape[0] -1):
    for j in range(1, H.shape[1] -1):
      val = H[i][j]
      above = H[i][j-1]
      below = H[i][j+1]
      left = H[i-1][j]
      right = H[i+1][j]

      diff += abs(val - above)
      diff += abs(val - below)
      diff += abs(val - left)
      diff += abs(val - right)

  return diff/len(H)*len(H)