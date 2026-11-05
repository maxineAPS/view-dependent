# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (c) the Norse contributors (https://github.com/norse/norse).
# This file combines code from Norse's threshold.py, superspike.py and heaviside.py
# (norse/torch/functional/) and is licensed under the GNU LGPL v3.0 or later;
# see licenses/LGPL-3.0.txt. The rest of this repository is MIT-licensed (see NOTICE).
#Functions to provide smooth heaviside function approximations compatible with torch.
#Author: Code in this script is from the Norse library (threshold.py, superspike.py, heaviside.py): https://github.com/norse/norse/tree/main/norse/torch/functional
#Date: June 2023


import numpy as np
import torch


@torch.jit.script
def heaviside(data):
    r"""
    A `heaviside step function <https://en.wikipedia.org/wiki/Heaviside_step_function>`_
    that truncates numbers <= 0 to 0 and everything else to 1.
    .. math::
        H[n]=\begin{cases} 0, & n <= 0 \\ 1, & n \gt 0 \end{cases}
    """
    return torch.gt(data, torch.as_tensor(0.0)).to(data.dtype)  # pragma: no cover

class SuperSpike(torch.autograd.Function):
    r"""SuperSpike surrogate gradient as described in Section 3.3.2 of
    F. Zenke, S. Ganguli, **"SuperSpike: Supervised Learning in Multilayer Spiking Neural Networks"**,
    Neural Computation 30, 1514–1541 (2018),
    `doi:10.1162/neco_a_01086 <https://www.mitpressjournals.org/doi/full/10.1162/neco_a_01086>`_
    """
    @staticmethod
    @torch.jit.ignore
    def forward(ctx, input_tensor: torch.Tensor, alpha: float) -> torch.Tensor:
        ctx.save_for_backward(input_tensor)
        ctx.alpha = alpha
        return heaviside(input_tensor)

    @staticmethod
    @torch.jit.ignore
    def backward(ctx, grad_output):
        (inp,) = ctx.saved_tensors
        alpha = ctx.alpha
        grad_input = grad_output.clone()
        grad = grad_input / (alpha * torch.abs(inp) + 1.0).pow(
            2
        )  # section 3.3.2 (beta -> alpha)
        return grad, None

@torch.jit.ignore
def super_fn(x: torch.Tensor, alpha: float = 100.0) -> torch.Tensor:
    return SuperSpike.apply(x, alpha)

superspike_fn = super_fn

class HeaviErfc(torch.autograd.Function):
    r"""Approximation of the heaviside step function as

    .. math::
        h(x,k) = \frac{1}{2} + \frac{1}{2} \text{erfc}(k x)

    where erfc is the error function.
    """

    @staticmethod
    def forward(ctx, x, k):
        ctx.save_for_backward(x)
        ctx.k = k
        return heaviside(x)  # 0 + 0.5 * torch.erfc(k * x)

    @staticmethod
    def backward(ctx, dy):
        (x,) = ctx.saved_tensors
        derfc = (2 * torch.exp(-(ctx.k * x).pow(2))) / (torch.as_tensor(np.pi).sqrt())
        return derfc * dy, None

@torch.jit.ignore
def heavi_erfc_fn(x: torch.Tensor, k: float):
    return HeaviErfc.apply(x, k)

class HeaviTanh(torch.autograd.Function):
    r"""Approximation of the heaviside step function as

    .. math::
        h(x,k) = \frac{1}{2} + \frac{1}{2} \text{tanh}(k x)
    """

    @staticmethod
    def forward(ctx, x, k):
        ctx.save_for_backward(x)
        ctx.k = k
        return heaviside(x)  # 0.5 + 0.5 * torch.tanh(k * x)

    @staticmethod
    def backward(ctx, dy):
        (x,) = ctx.saved_tensors
        dtanh = 1 - (x * ctx.k).tanh().pow(2)
        return dy * dtanh, None

@torch.jit.ignore
def heavi_tanh_fn(x: torch.Tensor, k: float):
    return HeaviTanh.apply(x, k)

class Logistic(torch.autograd.Function):
    r"""Probalistic approximation of the heaviside step function as

    .. math::
        z \sim p(\frac{1}{2} + \frac{1}{2} \text{tanh}(k x))
    """

    @staticmethod
    def forward(ctx, x, k):
        ctx.k = k
        ctx.save_for_backward(x)
        p = 0.5 + 0.5 * torch.tanh(k * x)
        return torch.distributions.bernoulli.Bernoulli(probs=p).sample()

    @staticmethod
    def backward(ctx, dy):
        (x,) = ctx.saved_tensors
        dtanh = 1 - (x * ctx.k).tanh().pow(2)
        return dy * dtanh, None


@torch.jit.ignore
def logistic_fn(x: torch.Tensor, k: float):
    return Logistic.apply(x, k)

class HeaviCirc(torch.autograd.Function):
    r"""Approximation of the heaviside step function as

    .. math::
        h(x,\alpha) = \frac{1}{2} + \frac{1}{2} \
        \frac{x}{(x^2 + \alpha^2)^{1/2}}
    """

    @staticmethod
    def forward(ctx, x, alpha):
        ctx.save_for_backward(x)
        ctx.alpha = alpha
        return heaviside(x)  # 0.5 + 0.5 * (x / (x.pow(2) + alpha ** 2).sqrt())

    @staticmethod
    def backward(ctx, dy):
        (x,) = ctx.saved_tensors
        alpha = ctx.alpha

        return (
            dy
            * (
                -(x.pow(2) / (2 * (alpha**2 + x.pow(2)).pow(1.5)))
                + 1 / (2 * (alpha**2 + x.pow(2)).sqrt())
            )
            * 2
            * alpha,
            None,
        )

@torch.jit.ignore
def heavi_circ_fn(x: torch.Tensor, k: float):
    return HeaviCirc.apply(x, k)

class CircDist(torch.autograd.Function):
    r"""Approximation of the heaviside step function as

    .. math::
        h(x,\alpha) = 0.5 + 0.5 * \frac{x}{\sqrt{x^2 + alpha^2}}
    """

    @staticmethod
    def forward(ctx, x, alpha):
        ctx.save_for_backward(x)
        ctx.alpha = alpha

        return torch.distributions.bernoulli.Bernoulli(
            0.5 + 0.5 * (x / (x.pow(2) + alpha**2).sqrt())
        ).sample()

    @staticmethod
    def backward(ctx, dy):
        (x,) = ctx.saved_tensors
        alpha = ctx.alpha
        return (
            dy
            * (
                -(x.pow(2) / (2 * (alpha**2 + x.pow(2)).pow(1.5)))
                + 1 / (2 * (alpha**2 + x.pow(2)).sqrt())
            )
            * 2
            * alpha,
            None,
        )

@torch.jit.ignore
def circ_dist_fn(x: torch.Tensor, k: float):
    return CircDist.apply(x, k)

class Triangle(torch.autograd.Function):
    r"""Triangular/piecewise linear surrogate gradient as in

    S.K. Esser et al., **"Convolutional networks for fast, energy-efficient neuromorphic computing"**,
    Proceedings of the National Academy of Sciences 113(41), 11441-11446, (2016),
    `doi:10.1073/pnas.1604850113 <https://www.pnas.org/content/113/41/11441.short>`_
    G. Bellec et al., **"A solution to the learning dilemma for recurrent networks of spiking neurons"**,
    Nature Communications 11(1), 3625, (2020),
    `doi:10.1038/s41467-020-17236-y <https://www.nature.com/articles/s41467-020-17236-y>`_
    """

    @staticmethod
    @torch.jit.ignore
    def forward(ctx, x: torch.Tensor, alpha: float) -> torch.Tensor:
        ctx.save_for_backward(x)
        ctx.alpha = alpha
        return heaviside(x)

    @staticmethod
    @torch.jit.ignore
    def backward(ctx, grad_output):
        (x,) = ctx.saved_tensors
        alpha = ctx.alpha
        grad_input = grad_output.clone()
        grad = grad_input * alpha * torch.relu(1 - x.abs())
        return grad, None

@torch.jit.ignore
def triangle_fn(x: torch.Tensor, alpha: float = 0.3) -> torch.Tensor:
    return Triangle.apply(x, alpha)

def threshold(x: torch.Tensor, method: str, alpha: float) -> torch.Tensor:
    if method == "heaviside":
        return heaviside(x)
    elif method == "super":
        return superspike_fn(x, torch.as_tensor(alpha))
    elif method == "triangle":
        return triangle_fn(x, alpha)
    elif method == "tanh":
        return heavi_tanh_fn(x, alpha)
    elif method == "circ":
        return heavi_circ_fn(x, alpha)
    elif method == "heavi_erfc":
        return heavi_erfc_fn(x, alpha)
    else:
        raise ValueError(
            f"Attempted to apply threshold function {method}, but no such "
            + "function exist. We currently support heaviside, super, "
            + "tanh, triangle, circ, and heavi_erfc."
        )


def sign(x: torch.Tensor, method: str, alpha: float) -> torch.Tensor:
    return 2 * threshold(x, method, alpha) - 1
