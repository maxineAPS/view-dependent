# Constructing Printable Surfaces with View-Dependent Appearance
### [Project Page](https://maxineaps.github.io/view-dependent-project-site/) | [Paper](https://arxiv.org/pdf/2306.07449.pdf)

This repo provides the code for the paper "Constructing Printable Surfaces with View-Dependent Appearance." This code allows users to optimize and create 3D printable colored heightfields that have view-dependent appearance, given a series of viewing angles and desired appearance images.

```
  @inproceedings{Perroni-Scharf:2023:CPS,
        author = "Maxine Perroni-Scharf and Szymon Rusinkiewicz",
        title = "Constructing Printable Surfaces with View-Dependent Appearance",
        booktitle = "Proc. SIGGRAPH",
        year = "2023",
        month = aug}
```

## Setup

### Setup computing environment

From the repository root:
```
conda create -n viewdependent python=3.9
conda activate viewdependent
pip install -r src/requirements.txt
```

`requirements.txt` lists the package versions of the original release. Where those versions are not available (e.g. on Apple-silicon Macs), the code also runs with current versions; we tested Python 3.12 with PyTorch 2.5, NumPy 2.4 and OpenCV 4.13, which give the same results.

## Create surfaces
### Run the surface optimizer

First, you need to optimize the heights and colors of a heightfield given camera directions and desired appearance images. For best results, our recommendation is to use up to four cameras and images, with at least 60 degrees between the azimuth and elevation of any pair of cameras. Each camera direction is the 3D direction the camera looks in (x, y, z, with negative z pointing down at the surface). Images can be PNG (RGB, RGBA or grayscale) or JPEG. You can run the optimizer from inside the `src` directory as follows:

```
optimize_surface.py [-h] [-c X Y Z] [-i IMAGE_PATHS [IMAGE_PATHS ...]] [-o OUTPUT_DIR] [--no_mesh] [--paper_settings]

e.g. python optimize_surface.py -c 1 0 -1 -c -1 0 -1 -i my_view1.png my_view2.png
```

Use one `-c` per camera and give one image per camera (your own images), in the same order. Add `--paper_settings` to use the behavior of the original release (see Changes in v2.0). This will create output heights and colors files in the `models` directory (or the directory given with `-o`), named by the date and time of the run, e.g. `models/06_13_2023_18-48-48_heights.npy` and `models/06_13_2023_18-48-48_colors.npy` (the same arrays are also saved as PyTorch `.pt` tensors). The files are updated every 50 steps and at the end of the optimization.

### Project the images onto the surface and export a printable mesh

At the end of the optimization, `optimize_surface.py` projects the desired images back onto the optimized surface and writes a closed, textured mesh: `models/<timestamp>_surface.obj`, `.mtl` and `.png`. Each point of the surface is colored from the cameras that see it, weighted by how directly each camera sees it; points that no camera sees keep their optimized color. To redo this step (for example with a finer texture), run:

```
python reproject.py models/<timestamp> [--texels 6] [--base 0.05]
```

`--texels` sets the texture samples per bar width and `--base` the height of the shortest bar after the surface is sliced thin (a negative value keeps the full heights).

Use `--no_mesh` with `optimize_surface.py` to skip it.

### Print the surface

Import the obj file (with its mtl and png files) into GrabCAD. The surface is 1 x 1 units; scale it to the size you want to print. Happy printing!

## Changes in v2.0

The code release has been updated for improved performance. The original release remains available as `v1.0`.

**Projection without Blender.** The post-optimization projection is now done in Python (`reproject.py`) and runs automatically at the end of `optimize_surface.py`, writing a closed, textured mesh ready for printing. As before, each bar is split into vertical segments and the images are projected onto the segments each camera sees. Blender is no longer needed, and `create_mesh.py` has been removed (it remains available in v1.0).

**Thin surfaces.** Before projecting, the surface is sliced thin: all bars are lowered by the same amount so that the shortest bar sits on a thin base (`--base`, default 0.05). This does not change which bars hide which from any camera; it removes the solid block underneath and the tall outer walls, and saves material.

**Projection weighting.** Where several cameras see the same segment, their images are now blended, weighted by how directly each camera sees the segment, instead of the last projected image replacing the others. This treats all views equally and reduces color mixing across views, especially with three or more views.

**Camera placement.** Camera rays are now cast from a plane at the current mean surface height, re-centered every 10 steps, instead of a fixed plane at z = 1. This keeps each camera's image aligned with the part of the surface that camera sees, which improves results when the optimized bar colors are used directly, especially for non-repeating images and lower camera elevations.

**Neighbor loss and height range.** The neighbor loss now compares every bar with its four neighbors, including across the edges of the repeating unit (the surface is tiled, so the bars on one edge sit next to those on the opposite edge), and is averaged over the bars instead of summed, so its strength no longer grows as the heightfield is subdivided during coarse-to-fine optimization (weight 1.0 on the average; previously 0.5 on the sum). Previously the bars on the edges of the unit were not compared with their neighbors, so thin spikes could form along the seams between repeats. The maximum bar height allowed by the barrier loss is now 1.0 (was 1.5), which gives shallower surfaces.

`--paper_settings` (or `paper_settings=True` in `grad_descent`) restores the optimization behavior of the original release (`v1.0`): camera rays start on the fixed plane z = 1, the neighbor loss is summed over the interior bars with weight 0.5, and the maximum height is 1.5.

**Other fixes.** None of these change the results of a run that completed with the original release and the package versions in `requirements.txt`.

- Hard-coded file paths are removed: the output folder is created automatically and can be set with `-o`. The final result is now saved at the end of the run, together with the camera directions, image paths and camera plane (`<timestamp>_cameras.json`), and heights and colors are also saved as `.npy` files.
- RGB PNG and JPEG images are now read correctly (previously only RGBA or grayscale PNGs worked).
- Camera directions can be non-integer values. The inputs are checked before the optimization starts: one image per camera, every image readable, and every camera looking down at the surface (negative z). Image paths are saved as absolute paths, so `reproject.py` works from any folder (relative paths are also looked up next to the saved files); it also accepts any of the saved files (e.g. `<timestamp>_heights.npy`) in place of the prefix. PyTorch no longer prints copy warnings during the run.
- Fixed an occasional crash (`IndexError: index ... is out of bounds`) around step 195, when the number of camera rays doubles: a ray passing within 0.0001 of a bar corner on the far edge of the surface was given a bar index one past the edge. Such rays now wrap around to the first bar, as rays near the opposite edge already did.
- Added a missing `numpy` import used by the `erfc` smooth Heaviside option.
- Rare cases where a height could reach the bounds of the barrier loss (making the loss NaN or infinite) are handled: heights are kept within the barrier bounds after each optimizer step and during simulated annealing.
- The optimizer gives the same results on PyTorch 2.x as on the PyTorch version in `requirements.txt` (PyTorch 2.0 changed the default of `zero_grad`; the code now sets it explicitly).

## License

MIT (see [LICENSE](LICENSE)). `src/happrox.py` is from [Norse](https://github.com/norse/norse) and stays under LGPL-3.0-or-later; see [NOTICE](NOTICE).
