#Image processing for view-dependent heightfield optimization.
#Author: Maxine Perroni-Scharf
#Date: June 2023


import matplotlib.pyplot as plt
import cv2
import torch
import numpy as np


'''
Convert image into usable tensor.
:param path: image path
:param dim: how much to warp image by
:param final_size: final image resolution
:return: image tensor
'''
def get_tensor_from_image(path, dim = (32, 32), final_size = (32, 32)):

    image_mat = plt.imread(path)
    
    #deal with grayscale image read
    if image_mat.shape[-1] != 4:
        image_mat = np.stack((image_mat,)*3, axis=-1)
    else:
        image_mat = image_mat[:, :, :-1]
    
    min_dim = min(dim)
    top_left_corner_x = (dim[0] - min_dim)//2
    top_left_corner_y = (dim[1] - min_dim)//2
    warped_image_mat = cv2.resize(image_mat, dim, interpolation = cv2.INTER_NEAREST)
    cropped_image_mat = warped_image_mat[top_left_corner_y:top_left_corner_y + min_dim, top_left_corner_x:top_left_corner_x + min_dim, :]
    image_mat = cv2.resize(cropped_image_mat, final_size, interpolation = cv2.INTER_NEAREST)
    image_tensor = torch.tensor(image_mat, dtype=torch.float).reshape(image_mat.shape[1]*image_mat.shape[1], 3)          
    return image_tensor




    
