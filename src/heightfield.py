#Functions to perform operations on heightfields.
#Author: Maxine Perroni-Scharf
#Date: June 2023


import torch


'''
Initialize random heightfield surface.
:param width: width of heightfield (number of bars across)
:param height: height of heightfield (number of bars across)
:param center: value to center random heights around.
:return: random heightfield heights tensor
'''
def get_random_H(width, height, center = 0.5):
  H = torch.rand(width, height)
  H = H - 0.5 + center
  return H


'''
Initialize uniform heightfield surface.
:param width: width of heightfield (number of bars across)
:param height: height of heightfield (number of bars across)
:param center: height of all bars in heightfield
:return: uniform heightfield heights tensor
'''
def get_uniform_H(width, height, center = 0.5):
  H = torch.full((width, height), center)
  return H


'''
Get flattened tensor of black rgb values.
:param n: length of tensor.
:return: tensor
'''
def get_black_img_flat(n):
    image = torch.zeros(n, 3, dtype=torch.float)
    return image


'''
Get nxnx3 tensor of black rgb values.
:param n: width/height of image.
:return: black image tensor
'''
def get_black_COL(n):
    image = torch.zeros(n, n, 3, dtype=torch.float)
    return image


'''
Get nxnx3 tensor of white rgb values.
:param n: width/height of image.
:return: white image tensor
'''
def get_white_COL(n):
    image = torch.ones(n, n, 3, dtype=torch.float)
    return image


'''
Get nxnx3 tensor of random rgb values.
:param n: width/height of image.
:return: random image tensor
'''
def get_random_COL(n):
    image = torch.rand(n, n, 3, dtype=torch.float)
    return image


'''
Subdivide input tensor A.
:param A: tensor to subdivide
:return: subdivided tensor
'''
def double_resolution(A):
    A = torch.repeat_interleave(A, 2, dim=1)
    return torch.repeat_interleave(A, 2, dim=0)


'''
Randomly pertubate input tensor T.
:param T: tensor to pertubate
:param scale: amount to pertubate by
:return: randomly pertubated tensor
'''
def randomize(T, scale):
    extra = torch.rand(T.shape, dtype=torch.float, requires_grad = True)
    T = T + extra*scale
    return T
    