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


#ray is origin + t *
def left_h_to_theta(i, ray, H_i, width_sums):
    x_0 = 0 #left start of strips
    x = ray.origin.x
    d = ray.direction
    theta = H_i - (d.y/d.x)*((x_0 - x + width_sums[i]))

    return theta


def left_theta_to_h(i, ray, theta, widths):
    x_0 = 1 #left start of strips
    x = ray.origin.x
    d = ray.direction
    
    H_i = theta - (d.y/d.x)*((x_0 - x + (i+1)*widths[i]))

    return H_i


def get_thetas(H, ray, widths, ids):
  thetas = torch.empty(len(ids), dtype = torch.float)
  origin = ray.origin
  d = ray.direction

  for i in range(len(ids)):
    id = ids[i]
    theta = left_h_to_theta(i, ray, H[int(id[0]), int(id[1])], widths)
    thetas[i] = theta

  return thetas

def left_monotonize_thetas(thetas):
  #cumulative maximum accross thetas
  return torch.cummax(thetas, dim=0)[0]


def points_from_thetas(thetas, ray):
  theta_points = []
  for theta in thetas:
    theta_point = np.array([ray.origin.x, theta])
    theta_point = Point(theta_point)
    theta_points.append(theta_point)
  return theta_points


def left_ray_to_color(ray, thetas, C, ids, heaviside_fn = None, heaviside_k = 0.1):
  n = len(thetas)
  size = (1, n)
  y = ray.origin.y

  #Calculate H(y - theta_i)
  y_tensor = torch.full(size, y).double()
  #thetas = torch.tensor(thetas)
  inputs = y_tensor - thetas
  values = torch.tensor([0, 0, 0, 0, 0]).double()
  #heaviside = norse.torch.functional.heavi_erfc_fn(inputs, 0.0)

  heaviside = happrox.heavi_erfc_fn(inputs, heaviside_k)

  if heaviside_fn == "erfc":
    heaviside = happrox.heavi_erfc_fn(inputs, heaviside_k)
  if heaviside_fn == "tan":
    heaviside = happrox.heavi_tanh_fn(inputs, heaviside_k)
  if heaviside_fn == "log":
    heaviside = happrox.logistic_fn(inputs, heaviside_k)
  if heaviside_fn == "circ":
    heaviside = happrox.heavi_circ_fn(inputs, heaviside_k)
  if heaviside_fn == "circdist":
    heaviside = happrox.circ_dist_fn(inputs, heaviside_k)

  
  sum = C[int(ids[0][0]), int(ids[0][1])]
  for i in range(n-1):
    sum = sum + heaviside[0][i]*(C[int(ids[i+1][0]), int(ids[i+1][1])] - C[int(ids[i][0]), int(ids[i][1])])

  return sum




def forward_left(H, COL, ray, width_sums, ids, heaviside_fn = None, heaviside_k = 0.1):


  thetas = get_thetas(H, ray, width_sums, ids)

  new_thetas = left_monotonize_thetas(thetas)

  col = left_ray_to_color(ray, new_thetas, COL, ids, heaviside_fn = heaviside_fn, heaviside_k=heaviside_k)
  
  return col


def project_onto_plane(x, n):
    d = utils.dot_product(x, n) / utils.norm(n)
    p = [d * utils.normalize(n)[i] for i in range(len(n))]
    return [x[i] - p[i] for i in range(len(x))]

def get_height_at_first_intersection(sorted_intersections, origin, direction):

    first_intersection = sorted_intersections[0]
    first_intersection_x = first_intersection[0]
    
    #find z value of ray for that x
    #origin[0] + t * direction[0] = first_intersection_x
    t = (first_intersection_x - origin[0])/direction[0]
    
    first_intersection_z = origin[2] + t * direction[2]
    return first_intersection_z

def get_2D_ray(origin, direction, sorted_intersections):

    new_2D_dir_x = np.linalg.norm([direction[0:2]])
    new_2D_direction = (new_2D_dir_x, direction[2])
    new_2D_direction = new_2D_direction/np.linalg.norm(new_2D_direction)
    first_intersection_z = get_height_at_first_intersection(sorted_intersections, origin, direction)
    origin_2D = np.array([0, first_intersection_z])

    return origin_2D, new_2D_direction
  
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

def find_ids_and_lengths(sorted_intersections, num_strips):

  ids = []
  lengths = []
  # remember to ignore element 0 and last element (reason for range)
  
  for i in range(0, len(sorted_intersections)-1):
    midpoint = (sorted_intersections[i] + sorted_intersections[i+1])/2
    scaled_midpoint = midpoint*num_strips
    ids.append(np.floor(scaled_midpoint))
    lengths.append(np.linalg.norm(sorted_intersections[i+1]-sorted_intersections[i]))
    
  return ids, lengths


def ray3D_to_ids_width_ray2D(origin, direction, num_strips):

    projected_direction = np.array([direction[0], direction[1], 0])

    projected_origin = np.array([origin[0], origin[1], 0])
    sorted_intersections = find_intersections(projected_origin, projected_direction, num_strips)
    ids, widths = find_ids_and_lengths(sorted_intersections, num_strips)
    origin_2D, direction_2D = get_2D_ray(origin, direction, sorted_intersections)
    origin_point = Point(origin_2D)
    direction_point = Point(direction_2D)
    ray = Ray(origin_point, direction_point)
    return ids, widths, ray
    


def get_width_sums(widths):

    curr_sum = widths[0]
    width_sums = [curr_sum]
    for i in range(1, len(widths)):
        curr_sum += widths[i]
        width_sums.append(curr_sum)

    return width_sums


def get_ray_packs(ray_origins, cam_direction, num_strips):
    ray_packs = []
    

    for z in range(len(ray_origins)):
        origin  = ray_origins[z]

        ids, widths, ray = ray3D_to_ids_width_ray2D(origin, cam_direction, num_strips)
        width_sums = get_width_sums(widths)
        ray_packs.append([ids, widths, width_sums, ray])
    return ray_packs

def forward(H, COL, ray_packs, num_cams, num_repeats = 2, count = 0, heaviside_fn = None, heaviside_k = 0.1):  
    result_cols = []
    for i in range(len(ray_packs)):
      result_cols.append(heightfield.get_black_img_flat(len(ray_packs[i])))
    #result_cols = [get_black_img_flat(len(ray_packs[0])), get_black_img_flat(len(ray_packs[1])), get_black_img_flat(len(ray_packs[2])), get_black_img_flat(len(ray_packs[3]))] 
    repeated_H = H.repeat(num_repeats, num_repeats)
    repeated_COL = COL.repeat(1, 1, 1)


    for y in range(num_cams):
      cam_packs = ray_packs[y]
      for i, (ids, widths, width_sums, ray) in enumerate(cam_packs):

        result_col = forward_left(repeated_H, repeated_COL, ray, width_sums, ids, heaviside_fn = heaviside_fn, heaviside_k = heaviside_k)
        result_cols[y][i] = result_col

    return result_cols
  