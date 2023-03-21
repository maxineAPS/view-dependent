import math
import numpy as np
import matplotlib.pyplot as plt

def dot_product(x, y):
    return sum([x[i] * y[i] for i in range(len(x))])

def norm(x):
    return math.sqrt(dot_product(x, x))

def normalize(x):
    return [x[i] / norm(x) for i in range(len(x))]

def Sort_Tuple(tup, reverse = 0):
    return(sorted(tup, key = lambda x: x[0], reverse = reverse)) 
  
# get the x coordinate of the midpoint of each heightfield strip
def get_centers_x(num_strips):
  strip_width = 1/num_strips
  A = np.array([val*strip_width for val in range(num_strips)])
  rectangle_centers = np.repeat(A, num_strips, axis=0)
  return rectangle_centers

# get the y coordinate of the midpoint of each heightfield strip
def get_centers_y(num_strips):
  strip_width = 1/num_strips
  A = np.array([val*strip_width for val in range(num_strips)])
  rectangle_centers = np.tile(A, num_strips)
  return rectangle_centers

