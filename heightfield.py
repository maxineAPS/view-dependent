import torch

def get_random_H(width, height, center = 0.5):
  H = torch.rand(width, height)
  H = H + -0.5 + center
  return H

def get_uniform_H(width, height, center = 0.5):
  H = torch.full((width, height), center)
  return H

def get_black_img_flat(n):
    image = torch.zeros(n, 3, dtype=torch.float)
    return image

def get_black_COL(n):
    image = torch.zeros(n, n, 3, dtype=torch.float)
    return image

def get_white_COL(n):
    image = torch.ones(n, n, 3, dtype=torch.float)
    return image

def get_random_COL(n):
    image = torch.rand(n, n, 3, dtype=torch.float)
    return image
    
def double_resolution(A):
    A = torch.repeat_interleave(A, 2, dim=1)
    return torch.repeat_interleave(A, 2, dim=0)

def randomize(T, scale):
    extra = torch.rand(T.shape, dtype=torch.float, requires_grad = True)
    T = T + extra*scale
    return T
    