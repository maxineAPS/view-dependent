#Post-optimization projection and mesh export (no Blender needed).
#Author: Maxine Perroni-Scharf
#
#As in the paper, each bar is split into vertical segments and the desired images are projected back onto
#the optimized heightfield. A segment takes the images of the cameras that see it (visibility is decided per
#segment, at its center), weighted by how directly each camera sees it (the cosine between the segment normal
#and the viewing direction). This weighted average minimizes the color error summed over all camera images.
#Segments that no camera sees keep the optimized bar color.
#
#Before projecting, the surface is sliced thin: all bars are lowered by the same amount so that the shortest
#bar sits on a thin base. Lowering every bar (and the cameras' pixel plane) by the same amount does not change
#which bars hide which from any camera; it only removes the solid block underneath and the tall outer walls. The result is written as a closed mesh (.obj) with
#a texture atlas (.png) and material file (.mtl) that can be imported into a slicer for full-color printing.
#
#Usage (from inside src, after optimize_surface.py):
#   python reproject.py models/<timestamp>
#which reads <timestamp>_heights.npy, _colors.npy and _cameras.json and writes <timestamp>_surface.obj/.mtl/.png.

import argparse
import json
import os
import numpy as np
import matplotlib.pyplot as plt
import cv2


'''
Load an image as an RGB float array in [0, 1] (same handling as image.py), resized to size x size.
Rows of the image correspond to x and columns to y on the heightfield, as in the optimizer.
:param path: image path
:param size: output resolution
:return: size x size x 3 array
'''
def load_image(path, size=512):
    im = plt.imread(path)
    if np.issubdtype(im.dtype, np.integer):
        im = im.astype(np.float32)/255.0
    if im.ndim == 2:
        im = np.stack((im,)*3, axis=-1)
    elif im.shape[-1] == 4:
        im = im[:, :, :3]
    return cv2.resize(np.ascontiguousarray(im, dtype=np.float32), (size, size), interpolation=cv2.INTER_AREA)


'''
Check which points are visible from a viewing direction, by walking the bar grid towards the camera.
:param H: S x S bar heights
:param P: N x 3 points (slightly offset from their faces)
:param d: viewing direction (pointing from the camera towards the surface)
:return: boolean array of length N
'''
def visible_from(H, P, d):
    S = H.shape[0]
    L = np.hypot(d[0], d[1])
    ux, uy, rise = -d[0]/L, -d[1]/L, -d[2]/L
    cx = np.floor(P[:, 0]*S).astype(int)
    cy = np.floor(P[:, 1]*S).astype(int)
    stx, sty = (1 if ux > 0 else -1), (1 if uy > 0 else -1)
    tdx = 1/(abs(ux)*S) if abs(ux) > 1e-12 else np.inf
    tdy = 1/(abs(uy)*S) if abs(uy) > 1e-12 else np.inf
    tmx = ((cx + (stx > 0))/S - P[:, 0])/ux if abs(ux) > 1e-12 else np.full(len(P), np.inf)
    tmy = ((cy + (sty > 0))/S - P[:, 1])/uy if abs(uy) > 1e-12 else np.full(len(P), np.inf)
    t = np.zeros(len(P))
    visible = np.ones(len(P), dtype=bool)
    active = np.ones(len(P), dtype=bool)
    for _ in range(4*S + 4):
        inside = (cx >= 0) & (cy >= 0) & (cx < S) & (cy < S)
        active &= inside
        if not active.any():
            break
        idx = np.where(active)[0]
        z = P[idx, 2] + rise*t[idx]
        blocked = z < H[cx[idx], cy[idx]] - 1e-7
        visible[idx[blocked]] = False
        active[idx[blocked]] = False
        step_x = tmx < tmy
        t = np.where(step_x, tmx, tmy)
        cx = np.where(step_x, cx + stx, cx)
        cy = np.where(step_x, cy, cy + sty)
        tmx = np.where(step_x, tmx + tdx, tmx)
        tmy = np.where(step_x, tmy, tmy + tdy)
    return visible


'''
Color points of segments by projecting the desired images, given each segment's camera weights.
:param COL: S x S x 3 optimized bar colors (used where no camera sees the segment)
:param P: N x 3 points, W: N x num_cams camera weights of the segment each point belongs to, bars: N x 2 bar indices
:param cams: list of viewing directions, images: list of RGB arrays, camera_z: list of pixel-plane heights
:return: N x 3 colors
'''
def project_colors(COL, P, W, bars, cams, images, camera_z):
    acc = np.zeros((len(P), 3))
    wsum = np.zeros(len(P))
    for q, (d, im, zc) in enumerate(zip(cams, images, camera_z)):
        d = np.asarray(d, dtype=float)
        d = d/np.linalg.norm(d)
        t = (zc - P[:, 2])/d[2]
        px, py = P[:, 0] + t*d[0], P[:, 1] + t*d[1]
        ok = (W[:, q] > 0) & (px >= 0) & (px < 1) & (py >= 0) & (py < 1)
        r = np.clip(np.floor(px*im.shape[0]).astype(int), 0, im.shape[0] - 1)
        c = np.clip(np.floor(py*im.shape[1]).astype(int), 0, im.shape[1] - 1)
        acc[ok] += W[ok, q, None]*im[r[ok], c[ok]]
        wsum[ok] += W[ok, q]
    out = np.clip(COL[bars[:, 0], bars[:, 1]], 0, 1).astype(float)
    seen = wsum > 0
    out[seen] = acc[seen]/wsum[seen, None]
    return out


'''
Camera weights of each segment: visible from the camera at the segment's center, times how directly the
camera sees it.
:param H: S x S bar heights, faces: list of faces from build_faces, cams: viewing directions
:return: num_faces x num_cams weights
'''
def segment_weights(H, faces, cams):
    centers = np.array([np.array(o) + 0.5*np.array(eu) + 0.5*np.array(ev) + 1e-6*np.array(n) for o, eu, ev, n, ab in faces])
    normals = np.array([n for o, eu, ev, n, ab in faces], dtype=float)
    W = np.zeros((len(faces), len(cams)))
    for q, d in enumerate(cams):
        d = np.asarray(d, dtype=float)
        d = d/np.linalg.norm(d)
        w = -(normals @ d)
        ok = w > 0
        ok[ok] = visible_from(H, centers[ok], d)
        W[ok, q] = w[ok]
    return W


'''
Build the closed heightfield mesh: bar tops, the exposed parts of the bar sides split into vertical segments
(at multiples of segment_height, as in the paper), and the bottom.
Each face is a rectangle with an origin, two edge vectors (u along the face, v along the face), a normal and
its bar index.
:param H: S x S bar heights
:return: list of faces (origin, edge_u, edge_v, normal, (a, b))
'''
def build_faces(H, segment_height=0.1):
    S = H.shape[0]
    w = 1/S
    faces = []
    for a in range(S):
        for b in range(S):
            h = H[a, b]
            x0, y0 = a*w, b*w
            faces.append(((x0, y0, h), (w, 0, 0), (0, w, 0), (0, 0, 1), (a, b)))
            #sides: only the part above the neighboring bar is exposed (down to 0 at the border)
            for nx, ny, (na, nb) in [(-1, 0, (a - 1, b)), (1, 0, (a + 1, b)), (0, -1, (a, b - 1)), (0, 1, (a, b + 1))]:
                low = H[na, nb] if 0 <= na < S and 0 <= nb < S else 0.0
                if h <= low:
                    continue
                z0 = low
                while z0 < h - 1e-9:
                    z1 = min(h, (np.floor(z0/segment_height + 1e-9) + 1)*segment_height)
                    if nx != 0:
                        xs = x0 if nx < 0 else x0 + w
                        faces.append(((xs, y0, z0), (0, w, 0), (0, 0, z1 - z0), (nx, 0, 0), (a, b)))
                    else:
                        ys = y0 if ny < 0 else y0 + w
                        faces.append(((x0, ys, z0), (w, 0, 0), (0, 0, z1 - z0), (0, ny, 0), (a, b)))
                    z0 = z1
    faces.append(((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, -1), (0, 0)))  #bottom
    return faces


'''
Project the images onto the surface and write a textured mesh.
:param H: S x S bar heights, COL: S x S x 3 bar colors
:param cams: viewing directions, image_paths: desired images, camera_z: pixel-plane height(s) used by the optimizer
:param out_prefix: output path prefix (writes .obj, .mtl and .png)
:param texels: texture samples per bar width
:param base: height of the shortest bar after slicing (None: do not slice)
:return: None
'''
def export_surface(H, COL, cams, image_paths, camera_z, out_prefix, texels=6, image_size=512, base=0.05):
    if np.isscalar(camera_z):
        camera_z = [float(camera_z)]*len(cams)
    if base is not None:
        #slice: lower every bar (and the pixel planes) so that the shortest bar is `base` tall
        shift = max(0.0, float(H.min()) - base)
        H = H - shift
        camera_z = [z - shift for z in camera_z]
    images = [load_image(p, image_size) for p in image_paths]
    S = H.shape[0]
    faces = build_faces(H)
    #texel grid for every face (bottom face: a single texel), packed row by row into an atlas
    sizes = []
    for o, eu, ev, nrm, ab in faces:
        lu, lv = np.linalg.norm(eu), np.linalg.norm(ev)
        if nrm[2] == -1:
            sizes.append((1, 1))
        else:
            sizes.append((max(1, int(round(lu*S*texels))), max(1, int(np.ceil(lv*S*texels)))))
    atlas_w = 2048
    pos, x, y, row_h = [], 0, 0, 0
    for tw, th in sizes:
        if x + tw + 2 > atlas_w:
            x, y, row_h = 0, y + row_h + 2, 0
        pos.append((x + 1, y + 1))
        x += tw + 2
        row_h = max(row_h, th)
    atlas_h = y + row_h + 2
    W_seg = segment_weights(H, faces, cams)
    #sample points at texel centers (plus a 1-texel border so texture filtering does not bleed)
    P, N, B, where = [], [], [], []
    for (o, eu, ev, nrm, ab), (tw, th), (px, py) in zip(faces, sizes, pos):
        o, eu, ev = np.array(o, float), np.array(eu, float), np.array(ev, float)
        iu = np.clip((np.arange(-1, tw + 1) + 0.5)/tw, 0, 1)
        iv = np.clip((np.arange(-1, th + 1) + 0.5)/th, 0, 1)
        U, V = np.meshgrid(iu, iv)
        pts = o + U.reshape(-1, 1)*eu + V.reshape(-1, 1)*ev
        P.append(pts)
        N.append(np.repeat(np.arange(len(P) - 1, len(P)), len(pts)))
        B.append(np.tile(ab, (len(pts), 1)))
        gx, gy = np.meshgrid(np.arange(-1, tw + 1) + px, np.arange(-1, th + 1) + py)
        where.append(np.stack([gy.reshape(-1), gx.reshape(-1)], 1))
    P, face_of, B, where = np.concatenate(P), np.concatenate(N), np.concatenate(B), np.concatenate(where)
    colors = project_colors(COL, P, W_seg[face_of], B, cams, images, camera_z)
    atlas = np.ones((atlas_h, atlas_w, 3))
    atlas[where[:, 0], where[:, 1]] = colors
    #mesh
    name = os.path.basename(out_prefix)
    obj = ["# view-dependent heightfield with projected images (reproject.py)", f"mtllib {name}.mtl", "usemtl surface"]
    vt, fl = [], []
    k = 1
    for (o, eu, ev, nrm, ab), (tw, th), (px, py) in zip(faces, sizes, pos):
        o, eu, ev = np.array(o, float), np.array(eu, float), np.array(ev, float)
        corners = [o, o + eu, o + eu + ev, o + ev]
        uvs = [(px, py), (px + tw, py), (px + tw, py + th), (px, py + th)]
        #counter-clockwise when seen from outside
        if np.dot(np.cross(eu, ev), nrm) < 0:
            corners, uvs = corners[::-1], uvs[::-1]
        for c, (ux, uy) in zip(corners, uvs):
            obj.append(f"v {c[0]:.6f} {c[2]:.6f} {-c[1] + 0.0:.6f}")  #OBJ convention: y up (as written by Blender)
            vt.append(f"vt {ux/atlas_w:.6f} {1 - uy/atlas_h:.6f}")
        fl.append(f"f {k}/{k} {k+1}/{k+1} {k+2}/{k+2} {k+3}/{k+3}")
        k += 4
    with open(out_prefix + ".obj", "w") as f:
        f.write("\n".join(obj + vt + fl) + "\n")
    with open(out_prefix + ".mtl", "w") as f:
        f.write(f"newmtl surface\nKa 1 1 1\nKd 1 1 1\nmap_Kd {name}.png\n")
    plt.imsave(out_prefix + ".png", np.clip(atlas, 0, 1))
    print("Wrote " + out_prefix + ".obj/.mtl/.png (" + str(len(faces)) + " faces, " + str(atlas_w) + "x" + str(atlas_h) + " texture)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project the desired images onto an optimized heightfield and write a printable textured mesh.")
    parser.add_argument('prefix', type=str, help="output prefix written by optimize_surface.py, e.g. models/06_13_2023_18-48-48")
    parser.add_argument('--texels', type=int, default=6, help="texture samples per bar width (default 6)")
    parser.add_argument('--base', type=float, default=0.05, help="height of the shortest bar after slicing the surface thin (default 0.05; negative: do not slice)")
    args = parser.parse_args()
    #accept any of the files written by optimize_surface.py in place of the prefix
    for suffix in ("_heights.npy", "_colors.npy", "_cameras.json", "_heights.pt", "_colors.pt"):
        if args.prefix.endswith(suffix):
            args.prefix = args.prefix[:-len(suffix)]
    for suffix in ("_heights.npy", "_colors.npy", "_cameras.json"):
        if not os.path.isfile(args.prefix + suffix):
            parser.error("%s not found (give the prefix written by optimize_surface.py, e.g. models/06_13_2023_18-48-48)" % (args.prefix + suffix))
    if not 1 <= args.texels <= 32:
        parser.error("--texels must be between 1 and 32")
    H = np.load(args.prefix + "_heights.npy")
    COL = np.load(args.prefix + "_colors.npy")
    meta = json.load(open(args.prefix + "_cameras.json"))
    #relative image paths are looked up from the current folder, then next to the saved files
    for i, p in enumerate(meta["image_paths"]):
        beside = os.path.join(os.path.dirname(args.prefix), p)
        if not os.path.isfile(p) and os.path.isfile(beside):
            meta["image_paths"][i] = beside
        elif not os.path.isfile(p):
            parser.error("desired image %s not found" % p)
    export_surface(H, COL, meta["camera_directions"], meta["image_paths"], meta["camera_z"], args.prefix + "_surface", texels=args.texels, base=(args.base if args.base >= 0 else None))
