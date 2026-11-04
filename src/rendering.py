#Differentiable heightfield rendering process functions
#Author: Maxine Perroni-Scharf
#Date: June 2023


import utils
import torch
import numpy as np
import happrox
import heightfield


class Point:
    def __init__(self, array):
        self.x = array[0]
        self.y = array[1]
        self.array = array
        
    def __str__(self):
      return str(self.array)
    
class Ray:
    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = direction
        
    def __str__(self):
      return "RAY with origin: " + str(self.origin) + "\tand direction: " + str(self.direction)


'''
Convert height of bar in field to backtraced camera ray origin boundary.
:param i: bar index
:param ray: current ray
:return: backtraced boundary value
'''
def h_to_boundary(i, ray, H_i, width_sums):
    x_0 = 0 #start of strips offset
    x = ray.origin.x
    d = ray.direction
    theta = H_i - (d.y/d.x)*((x_0 - x + width_sums[i]))
    return theta


'''
Get all backtraced boundary points for specific camera direction as specified by a camera ray.
:param H: heightfield tensor
:param ray: camera ray object
:param widths: list of widths between the heights for the 2D heightfield slice
:param ids: ids of bars in heightfield that are in current slice
:return: list of backtraced boundary height points
'''
def get_backtraced_boundaries(H, ray, widths, ids):
  thetas = torch.empty(len(ids), dtype = torch.float)
  for i in range(len(ids)):
    id = ids[i]
    theta = h_to_boundary(i, ray, H[int(id[0]), int(id[1])], widths)
    thetas[i] = theta
  return thetas


'''
Ensure boundary points are monotonically increasing.
:param thetas: list of boundary points
:return: list of monotonically increasing boundary points
'''
def monotonize_boundary_points(thetas):
  #cumulative maximum accross thetas
  return torch.cummax(thetas, dim=0)[0]


'''
Obtain pixel color for specified camera ray pointing at heightfield, given backtraced boundary values.
:param ray: camera ray object
:param thetas: list of boundary points
:param COL: heightfield colors tensor
:param ids: list of heightfield indices corresponding to bars for 2D heightfield slice for the given ray
:param heaviside_fn: optional heaviside function argument (choices: erfc, tan, log, circ, circdist, see happrox.py)
:param heaviside_k: optional parameter for use in heaviside functions
:return: rgb color for given ray
'''
def render_ray_given_boundaries(ray, thetas, COL, ids, heaviside_fn = None, heaviside_k = 0.1):
  n = len(thetas)
  size = (1, n)
  y = ray.origin.y

  #Calculate H(y - theta_i)
  y_tensor = torch.full(size, y).double()
  #thetas = torch.tensor(thetas)
  inputs = y_tensor - thetas
  
  if heaviside_fn == "erfc":
    heaviside = happrox.heavi_erfc_fn(inputs, heaviside_k)
  elif heaviside_fn == "tan":
    heaviside = happrox.heavi_tanh_fn(inputs, heaviside_k)
  elif heaviside_fn == "log":
    heaviside = happrox.logistic_fn(inputs, heaviside_k)
  elif heaviside_fn == "circ":
    heaviside = happrox.heavi_circ_fn(inputs, heaviside_k)
  elif heaviside_fn == "circdist":
    heaviside = happrox.circ_dist_fn(inputs, heaviside_k)
  else: 
     heaviside = happrox.heavi_erfc_fn(inputs, heaviside_k) #default
    
  sum = COL[int(ids[0][0]), int(ids[0][1])]
  for i in range(n-1):
    sum = sum + heaviside[0][i]*(COL[int(ids[i+1][0]), int(ids[i+1][1])] - COL[int(ids[i][0]), int(ids[i][1])])

  return sum


'''
Obtain pixel color for specified camera ray pointing at heightfield, given heightfield heights and colors (render pixel).
:param H: heightfield heights tensor
:param COL: heightfield colors tensor
:param ray: camera ray object
:param width_sums: widths between heightfield bars for given slice
:param ids: list of heightfield indices corresponding to bars for 2D heightfield slice for the given ray
:param heaviside_fn: optional heaviside function argument (choices: erfc, tan, log, circ, circdist, see happrox.py)
:param heaviside_k: optional parameter for use in heaviside functions
:return: rgb color for given ray
'''
def render_ray(H, COL, ray, width_sums, ids, heaviside_fn = None, heaviside_k = 0.1):
  thetas = get_backtraced_boundaries(H, ray, width_sums, ids)
  new_thetas = monotonize_boundary_points(thetas)
  col = render_ray_given_boundaries(ray, new_thetas, COL, ids, heaviside_fn = heaviside_fn, heaviside_k=heaviside_k)
  return col


'''
Project 3D vector onto plane
:param x: vector specifying plane
:param n: vector specifying plane
:return: projected vector
'''
def project_onto_plane(x, n):
    d = utils.dot_product(x, n) / utils.norm(n)
    p = [d * utils.normalize(n)[i] for i in range(len(n))]
    return [x[i] - p[i] for i in range(len(x))]


'''
Get z value (height) of camera ray for x,y value of the first bar in heightfield slice.
:param sorted_intersections: list of sorted intsections with edges of bars in heightfield slice
:param origin: origin of camera ray
:param direction: direction of camera ray
:return: first intersection z value
'''
def get_height_at_first_intersection(sorted_intersections, origin, direction):
    first_intersection = sorted_intersections[0]
    first_intersection_x = first_intersection[0]
    #find z value of ray for given x
    t = (first_intersection_x - origin[0])/direction[0]
    first_intersection_z = origin[2] + t * direction[2]
    return first_intersection_z


'''
Convert 3D ray vector to 2D ray vector for a 2D heightfield slice
:param origin: origin of camera ray
:param direction: direction of camera ray
:param sorted_intersections: list of sorted intsections with edges of bars in heightfield slice
:return: 2D ray origin and direction with coordinates local to heightfield slice
'''
def get_2D_ray(origin, direction, sorted_intersections):
    new_2D_dir_x = np.linalg.norm([direction[0:2]])
    new_2D_direction = (new_2D_dir_x, direction[2])
    new_2D_direction = new_2D_direction/np.linalg.norm(new_2D_direction)
    first_intersection_z = get_height_at_first_intersection(sorted_intersections, origin, direction)
    origin_2D = np.array([0, first_intersection_z])
    return origin_2D, new_2D_direction


'''
Obtain x,y values of intersections of heightfield bar edges with a specific ray
:param projected_origin: origin of projected 3D camera ray onto horizontal plane
:param direction: direction of projected camera ray onto horizontal plane
:param num_strips: dimension of heightfield
:return: list of intersections
'''
def find_intersections(projected_origin, projected_direction, num_strips):
  A = np.array([[projected_origin[0], projected_origin[1]], [projected_origin[0] + 100*projected_direction[0], projected_origin[1] + 100*projected_direction[1]]])
  intersections = []

  for i in range(0, int(num_strips) + 1):
    B = np.array([[i/num_strips, 0], [i/num_strips, 5]])
    t, s = np.linalg.solve(np.array([A[1]-A[0], B[0]-B[1]]).T, B[0]-A[0])
    intersection = ((1-t)*A[0] + t*A[1])
    if -0.0001<=intersection[0]<= 1.0001 and -0.0001 <=intersection[1]<=1.0001:
      intersections.append(intersection)

  for j in range(0, int(num_strips) + 1):
    B = np.array([[0, j/num_strips], [5, j/num_strips]])
    t, s = np.linalg.solve(np.array([A[1]-A[0], B[0]-B[1]]).T, B[0]-A[0])
    intersection = (1-t)*A[0] + t*A[1]
    if -0.0001<=intersection[0]<=1.0001 and -0.0001<=intersection[1]<=1.0001:
      intersections.append(intersection)

  if projected_direction[0] >= 0: #ray facing northeast or southeast
    sorted_intersections = utils.Sort_Tuple(intersections)
  else: #ray facing northhwest or southwest
    sorted_intersections = utils.Sort_Tuple(intersections, reverse = 1)
  return sorted_intersections


'''
Get indices for heightfield tensor of heightfield bars intersecting with projected camera ray, and distances between these intersections.
:param sorted_intersections: list of sorted intsections with edges of bars in heightfield slice
:param num_strips: dimension of heightfield
:return: list of indices and distances
'''
def find_ids_and_lengths(sorted_intersections, num_strips):
  ids = []
  lengths = []
  # remember to ignore element 0 and last element
  for i in range(0, len(sorted_intersections)-1):
    midpoint = (sorted_intersections[i] + sorted_intersections[i+1])/2
    scaled_midpoint = midpoint*num_strips
    ids.append(np.floor(scaled_midpoint) % num_strips) #wrap -1 and num_strips around (intersections up to 1e-4 outside are accepted)
    lengths.append(np.linalg.norm(sorted_intersections[i+1]-sorted_intersections[i]))
  return ids, lengths


'''
Slice heightfield using a 3D ray, and get information for the resulting 2D slice (corresponding indices for the heightfield tensor, distances between these intersections and 2D ray).
:param origin: 3D ray origin
:param direction: 3D ray direction
:param num_strips: dimension of heightfield
:return: list of indices, list of distances and 2D ray for the 2D heightfield slice
'''
def get_2D_ray_info(origin, direction, num_strips):

    projected_direction = np.array([direction[0], direction[1], 0])

    projected_origin = np.array([origin[0], origin[1], 0])
    sorted_intersections = find_intersections(projected_origin, projected_direction, num_strips)
    ids, widths = find_ids_and_lengths(sorted_intersections, num_strips)
    origin_2D, direction_2D = get_2D_ray(origin, direction, sorted_intersections)
    origin_point = Point(origin_2D)
    direction_point = Point(direction_2D)
    ray = Ray(origin_point, direction_point)
    return ids, widths, ray
    

'''
Get cumulative sum of widths of 2D heightfield slice bars
:param widths: bar widths
:return: cumulative sum of bar widths
'''
def get_width_sums(widths):
    curr_sum = widths[0]
    width_sums = [curr_sum]
    for i in range(1, len(widths)):
        curr_sum += widths[i]
        width_sums.append(curr_sum)
    return width_sums


'''
Process all rays for a given camera, obtaining heightfield slice info.
:param ray origins: list of 3D ray origins
:param cam_direction: direction of camera
:num strips: dimensions of 3D heightfield
:return: list of lists of heightfield indices, widths of bars in 2D heightfield slice, cumulative sum of widths, and 2D ray objects.
'''
def process_rays(ray_origins, cam_direction, num_strips):
    ray_packs = []
    for z in range(len(ray_origins)):
        origin  = ray_origins[z]
        ids, widths, ray = get_2D_ray_info(origin, cam_direction, num_strips)
        width_sums = get_width_sums(widths)
        ray_packs.append([ids, widths, width_sums, ray])
    return ray_packs


'''
Render image for a camera.
:param H: heightfield heights tensor
:param COL: heightfield colors tensor
:param ray_packs: processed ray info (list of lists of [heightfield indices, widths of bars in 2D heightfield slice, cumulative sum of widths, and 2D ray object])
:param num_repeats: number of repeats for the heightfield
:param heaviside_fn: optional heaviside function argument (choices: erfc, tan, log, circ, circdist, see happrox.py)
:param heaviside_k: optional parameter for use in heaviside functions
:return: resulting rgb colors rendered by camera
'''
def render_camera(H, COL, ray_packs, num_cams, num_repeats = 2, heaviside_fn = None, heaviside_k = 0.1):  
    result_cols = []
    for i in range(len(ray_packs)):
      result_cols.append(heightfield.get_black_img_flat(len(ray_packs[i])))
    repeated_H = H.repeat(num_repeats, num_repeats)
    repeated_COL = COL.repeat(1, 1, 1)
    for y in range(num_cams):
      cam_packs = ray_packs[y]
      for i, (ids, widths, width_sums, ray) in enumerate(cam_packs):
        result_col = render_ray(repeated_H, repeated_COL, ray, width_sums, ids, heaviside_fn = heaviside_fn, heaviside_k = heaviside_k)
        result_cols[y][i] = result_col
    return result_cols
  