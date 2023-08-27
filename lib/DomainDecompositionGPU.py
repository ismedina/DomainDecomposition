import numpy as np
import torch
# from . import MultiScaleOT
from .LogSinkhorn import LogSinkhorn as LogSinkhorn
import LogSinkhornGPU
from . import DomainDecomposition as DomDec
import time

#########################################################
# Bounding box utils
# Cast all cell problems to a common size and coordinates
#########################################################


def pad_array(a, padding, pad_value=0):
    """
    Pad array `a` with a margin of `padding` width, filled with `pad_value`. 
    """
    shape = a.shape
    new_shape = tuple(s + 2*padding for s in shape)
    original_locations = tuple(slice(padding, s+padding) for s in shape)
    b = np.full(new_shape, pad_value, dtype=a.dtype)
    b[original_locations] = a
    return b


def pad_tensor(a, padding, pad_value=0):
    """
    Pad tensor `a` with a margin of `padding` width, filled with `pad_value`. 
    """
    shape = a.shape
    new_shape = tuple(s + 2*padding for s in shape)
    original_locations = tuple(slice(padding, s+padding) for s in shape)
    b = torch.full(new_shape, pad_value, dtype=a.dtype, device=a.device)
    b[original_locations] = a
    return b

def pad_replicate_2D(a, padding):
    """
    Pad tensor `a` replicating values at boundary `paddding` times.
    """
    shape = a.shape
    new_shape = tuple(s + 2*padding for s in shape)
    original_locations = tuple(slice(padding, s+padding) for s in shape)
    b = torch.zeros(new_shape, dtype=a.dtype, device=a.device)
    b[original_locations] = a
    # TODO: from here is specific for 2D
    s1, s2 = shape
    for i in range(padding):
        # Copy closest slice in the direction of the true array
        b[padding-1-i,:] = b[padding-i,:]
        b[s1+padding+i,:] = b[s1+padding-1+i,:]
        b[:,padding-1-i] = b[:,padding-i]
        b[:,s2+padding+i] = b[:,s2+padding-1+i]
    return b

def reformat_indices_2D(index, shapeY):
    """
    Takes linear indices and tuple of the total shapeY, and returns parameters 
    encoding the bounding box.
    """
    # TODO: generalize to 3D

    _, n = shapeY
    idx, idy = index // n, index % n
    if len(index) == 0:
        left, bottom = shapeY
        width = height = 0
    else:
        left = np.min(idx)
        right = np.max(idx)
        bottom = np.min(idy)
        top = np.max(idy)
        width = right - left + 1  # box width
        height = top - bottom + 1  # box height
        # Turn idx and idy into relative indices
        idx = idx - left
        idy = idy - bottom

    return left, bottom, width, height, idx, idy


def batch_cell_marginals_2D(marg_indices, marg_data, shapeY, muY):
    """
    Reshape marginals to a rectangle, find the biggest of all of these and 
    concatenate all marginals along a batch dimension. 
    Copy reference measure `muY` to these bounding boxes.
    """
    # TODO: generalize to 3D
    # Initialize structs to hold the data of all marginals
    B = len(marg_indices)
    left = np.zeros(B, dtype=np.int32)
    bottom = np.zeros(B, dtype=np.int32)
    width = np.zeros(B, dtype=np.int32)
    height = np.zeros(B, dtype=np.int32)
    idx = []
    idy = []

    # Get bounding boxes for all marginals
    for (i, indices) in enumerate(marg_indices):
        left[i], bottom[i], width[i], height[i], idx_i, idy_i = \
            reformat_indices_2D(indices, shapeY)
        idx.append(idx_i)
        idy.append(idy_i)

    # Compute common bounding box
    max_width = np.max(width)
    max_height = np.max(height)

    # Init batched marginal
    Nu_box = np.zeros((B, max_width, max_height))
    # Init batched nuref
    muY = muY.reshape(shapeY)
    Nuref_box = np.zeros((B, max_width, max_height))

    # Fill NuJ
    for (k, data) in enumerate(marg_data):
        Nu_box[k, idx[k], idy[k]] = data
        # Copy reference measure
        i0, w = left[k], width[k]
        j0, h = bottom[k], height[k]
        Nuref_box[k, :w, :h] = muY[i0:i0+w, j0:j0+h]

    # Return NuJ together with bounding box data (they will be needed for unpacking)
    return Nu_box, Nuref_box, left, bottom, max_width, max_height


def unpack_cell_marginals_2D(Nu_basic, left, bottom, shapeY, threshold=1e-15):
    """
    Un-batch all the cell marginals and truncate entries below `threshold`.
    """
    # TODO: generalize to 3D
    # TODO: incorporate balancing
    # Nu_basic is of size (B, 4, w, h), because there are 4 basic cells per
    # composite cell
    _, n = shapeY
    # Do all the process in the cpu
    B = Nu_basic.shape[0]
    sizeJ = Nu_basic.shape[1]
    marg_indices = []
    marg_data = []
    # NOTE: extraction could be done for the whole Nu_basic at once,
    # but then how to distinguish between slices.
    for k in range(B):
        for i in range(sizeJ):  # TODO: allow different dimension
            # idx, idy = np.nonzero(Nu_basic[k, i])
            idx, idy = np.nonzero(Nu_basic[k, i] > threshold)
            linear_id = (idx+left[k])*n + idy + bottom[k]
            marg_indices.append(linear_id)
            marg_data.append(Nu_basic[k, i, idx, idy])
    return marg_indices, marg_data

# TODO: complete this if possible
# def unpack_cell_marginals_2D_gpu(Nu_basic, left, bottom, shapeY, threshold=1e-15):
#     """
#     Un-batch all the cell marginals and truncate entries below `threshold`.
#     """
#     # TODO: generalize to 3D
#     # Assumes Nu_basic still in GPU
#     # Nu_basic is of size (B, 4, w, h), because there are 4 basic cells per
#     # composite cell
#     _, n = shapeY
#     # Do all the process in the cpu
#     B = Nu_basic.shape[0]
#     sizeJ = Nu_basic.shape[1]
#     marg_indices = []
#     marg_data = []
#     idB, idx, idy = torch.where(Nu_basic > threshold)
#     nu_entries = Nu_basic[idB, idx, idy]
#     # Where batch index changes slice
#     steps = torch.where(torch.diff(idB))[0]+1
#     # Add start and end
#     steps = np.hstack(([0], steps.cpu().numpy(), [len(idB)]))
#     # TODO: continue here

#     # -------
#     # NOTE: extraction could be done for the whole Nu_basic at once,
#     # but then how to distinguish between slices.
#     for k in range(B):
#         for i in range(sizeJ):  # TODO: allow different dimension
#             # idx, idy = np.nonzero(Nu_basic[k, i])
#             idx, idy = np.nonzero(Nu_basic[k, i] > threshold)
#             linear_id = (idx+left[k])*n + idy + bottom[k]
#             marg_indices.append(linear_id)
#             marg_data.append(Nu_basic[k, i, idx, idy])
#     return marg_indices, marg_data


# def batch_balance(muXCell, Nu_basic):
#     B, M, _ = muXCell.shape
#     s = M//2
#     atomic_mass = muXCell.view(B, 2, s, 2, s).permute(
#         (0, 1, 3, 2, 4)).contiguous().sum(dim=(3, 4))
#     atomic_mass = atomic_mass.view(B, -1).cpu().numpy()
#     for k in range(B):
#         status, Nu_basic[k] = DomDec.BalanceMeasuresMulti(
#             Nu_basic[k], atomic_mass[k], 1e-12, 1e-7
#         )
#         print(status, end = " ")
#     return Nu_basic

# More straightforward version
def batch_balance(muXCell, Nu_basic):
    B, M, _ = muXCell.shape
    s = M//2
    atomic_mass = muXCell.view(B, 2, s, 2, s).sum(dim=(2, 4))
    atomic_mass = atomic_mass.view(B, -1).cpu().numpy()
    Nu_basic_shape = Nu_basic.shape
    Nu_basic = Nu_basic.reshape(B, 4, -1)

    # TODO: Here we turn arrays to double so that LogSinkhorn.balanceMeasures
    # accepts them. This can be done cleaner
    for k in range(B):
        # print(atomic_mass[k])
        # print(Nu_basic[k].sum(axis = (-1)))
        nu_basick_double = np.array(Nu_basic[k], dtype=np.float64)
        atomic_massk_double = np.array(atomic_mass[k], dtype=np.float64)
        status, Nu_basic[k] = DomDec.BalanceMeasuresMulti(
            nu_basick_double, atomic_massk_double, 1e-12, 1e-7
        )
        # print(atomic_mass[k] - Nu_basic[k].sum(axis = (-1)))
        # print(status, end = " ")
    # print("")

    return Nu_basic.reshape(*Nu_basic_shape)


def get_grid_cartesian_coordinates(left, bottom, w, h, dx):
    """
    Generate the cartesian coordinates of the boxes with bottom-left corner 
    given by (left, bottom) (vectors), with width w, height h and spacing dx.
    i0 : torch.tensor
    j0 : torch.tensor
    w : int
    h : int
    dx : float
    """
    # TODO: generalize to 3D
    B = len(left)
    device = left.device
    x1_template = torch.arange(0, w*dx, dx, device=device)
    x2_template = torch.arange(0, h*dx, dx, device=device)
    x1 = left.view(-1, 1)*dx + x1_template.view(1, -1)
    x2 = bottom.view(-1, 1)*dx + x2_template.view(1, -1)
    return x1, x2


def batch_shaped_cartesian_prod(xs):
    """
    For xs = (x1, ..., xd) a tuple of tensors of shape (B, M1), ... (B, Md), 
    form the tensor X of shape (B, M1, ..., Md, d) such that
    `X[i] = torch.cartesian_prod(xs[i],...,xs[i]).view(M1, ..., Md, d)`
    """
    B = xs[0].shape[0]
    for x in xs:
        assert B == x.shape[0], "All xs must have the same batch dimension"
        assert len(x.shape) == 2, "xi must have shape (B, Mi)"
    Ms = tuple(x.shape[1] for x in xs)
    dim = len(xs)
    device = xs[0].device

    shapeX = (B, ) + Ms + (dim,)
    X = torch.empty(shapeX, device=device)
    for i in range(dim):
        shapexi = (B,) + (1,)*i + (Ms[i],) + (1,)*(dim-i-1)
        X[..., i] = xs[i].view(shapexi)
    return X


def compute_offsets_sinkhorn_grid(xs, ys, eps):
    """
    Compute offsets
    xs and ys are d-tuples of tensors with shape (B, Mi) where B is the batch 
    dimension and Mi the size of the grid in that coordinate
    # TODO: ref
    """
    # Get cartesian prod
    X = batch_shaped_cartesian_prod(xs)
    Y = batch_shaped_cartesian_prod(ys)
    shapeX = X.shape
    B, Ms, dim = shapeX[0], shapeX[1:-1], shapeX[-1]
    Ns = Y.shape[1:-1]

    # Get "bottom left" corner coordinates: select slice (:, 0, ..., 0, :)
    X0 = X[(slice(None),) + (0,)*dim + (slice(None),)] \
        .view((B,) + (1,)*dim + (dim,))  # NOTE alternatively: use unpack op.
    Y0 = Y[(slice(None),) + (0,)*dim + (slice(None),)] \
        .view((B,) + (1,)*dim + (dim,))  # NOTE alternatively: use unpack op.

    # Use the formulas in [TODO: ref] to compute the offset
    offsetX = torch.sum(2*(X-X0)*(Y0-X0), dim=-1)/eps
    offsetY = torch.sum(2*(Y-Y0)*(X0-Y0), dim=-1)/eps
    offset_constant = -torch.sum((X0-Y0)**2, dim=-1)/eps
    return offsetX, offsetY, offset_constant


def get_refined_marginals_gpu(muYL, muYL_old, parentsYL,
                              atomic_masses, atomic_masses_old,
                              atomic_cells, atomic_cells_old,
                              atomic_data_old, atomic_indices_old,
                              meta_cell_shape, meta_cell_shape_old):
    # Get "physical" basic cells, where mass actually sits
    # For old cells
    cell_indices_old = np.arange(np.prod(meta_cell_shape_old))
    true_indices_old = cell_indices_old.reshape(meta_cell_shape_old)
    # print(cell_indices_old, true_indices_old)
    # print(len(atomic_data_old), len(atomic_indices_old))
    # TODO: this is 2D
    true_indices_old = true_indices_old[1:-1, 1:-1].ravel()
    true_atomic_cells_old = [atomic_cells_old[i] for i in true_indices_old]
    # TODO: reconcile sparse and gpu versions
    if len(atomic_data_old) == len(true_indices_old):
        true_atomic_data_old = atomic_data_old
        true_atomic_indices_old = atomic_indices_old
    else:
        true_atomic_data_old = [atomic_data_old[i] for i in true_indices_old]
        true_atomic_indices_old = [atomic_indices_old[i] for i in true_indices_old]

    true_atomic_masses_old = atomic_masses_old[true_indices_old]

    # For new cells
    cell_indices = np.arange(np.prod(meta_cell_shape))
    true_indices = cell_indices.reshape(meta_cell_shape)
    true_indices = true_indices[1:-1, 1:-1].ravel()
    true_atomic_cells = [atomic_cells[i] for i in true_indices]
    true_atomic_masses = atomic_masses[true_indices]
    true_meta_cell_shape = tuple(s-2 for s in meta_cell_shape)

    # Invoke domdec function
    true_atomic_data, true_atomic_indices = \
        DomDec.GetRefinedAtomicYMarginals_SparseY(
            muYL, muYL_old, parentsYL,
            true_atomic_masses, true_atomic_masses_old,
            true_atomic_cells, true_atomic_cells_old,
            true_atomic_data_old, true_atomic_indices_old,
            true_meta_cell_shape
        )
    dtype = true_atomic_data[0].dtype
    atomic_data = [np.array([], dtype=dtype) for _ in cell_indices]
    atomic_indices = [np.array([], dtype=np.int32) for _ in cell_indices]
    for (i, k) in enumerate(true_indices):
        atomic_data[k] = true_atomic_data[i]
        atomic_indices[k] = true_atomic_indices[i]

    return atomic_data, atomic_indices

##############################################################
# Dedicated CUDA solver for DomDec:
# Assumes B rectangular problems with same size
##############################################################


class LogSinkhornCudaImageOffset(LogSinkhornGPU.AbstractSinkhorn):
    """
    Online Sinkhorn solver for standard OT on images with separable cost, 
    custom CUDA implementation. 
    Each Sinkhorn iteration has complexity N^(3/2), instead of the usual N^2. 

    Attributes
    ----------
    mu : torch.Tensor 
        of size (B, M1, M2)
        First marginals
    nu : torch.Tensor 
        of size (B, N1, N2)
        Second marginals 
    C : tuple 
        of the form ((x1, x2), (y1, y2))
        Grid coordinates
    eps : float
        Regularization strength
    muref : torch.Tensor 
        with same dimensions as mu (except axis 0, which can have len = 1)
        First reference measure for the Gibbs energy, 
        i.e. K = muref \otimes nuref exp(-C/eps)
    nuref : torch.Tensor 
        with same dimensions as nu (except axis 0, which can have len = 1)
        Second reference measure for the Gibbs energy, 
        i.e. K = muref \otimes nuref exp(-C/eps)
    alpha_init : torch.Tensor 
        with same dimensions as mu, or None
        Initialization for the first Sinkhorn potential
    """

    def __init__(self, mu, nu, C, eps, **kwargs):
        (xs, ys) = C
        zs = xs + ys  # Have all coordinates in one tuple
        x1 = zs[0]
        B = LogSinkhornGPU.batch_dim(mu)
        # Check whether xs have a batch dimension
        if len(x1.shape) == 1:
            for z in zs:
                assert len(z) == 1, \
                    "dimensions of grid coordinates must be consistent"
            C = tuple(tuple(xi.view(1, -1) for xi in X) for X in C)
        else:
            for z in zs:
                assert len(z.shape) == 2, \
                    "coordinates can just have one spatial dimension"
                assert z.shape[0] == B, \
                    "batch dimension of all coordinates must coincide"

        # Now all coordinates have a batch dimension of either B or 1.
        # Check that all coordinates have same grid spacing
        dx = x1[0, 1]-x1[0, 0]
        for z in zs:
            assert torch.max(torch.abs(torch.diff(z, dim=-1)-dx)) < 1e-6, \
                "Grid is not equispaced"

        # Check geometric dimensions
        Ms = LogSinkhornGPU.geom_dims(mu)
        Ns = LogSinkhornGPU.geom_dims(nu)
        assert len(Ms) == len(Ns) == 2, "Shapes incompatible with images"

        # Compute the offsets
        self.offsetX, self.offsetY, self.offset_const = \
            compute_offsets_sinkhorn_grid(xs, ys, eps)

        # Save xs and ys in case they are needed later
        self.xs = xs
        self.ys = ys

        C = (dx, Ms, Ns)

        super().__init__(mu, nu, C, eps, **kwargs)

    def get_new_alpha(self):
        dx, Ms, Ns = self.C
        h = self.beta / self.eps + self.lognuref + self.offsetY
        return - self.eps * (
            LogSinkhornGPU.softmin_cuda_image(h, Ms, Ns, self.eps, dx)
            + self.offsetX + self.offset_const + self.logmuref - self.logmu
        )

    def get_new_beta(self):
        dx, Ms, Ns = self.C
        h = self.alpha / self.eps + self.logmuref + self.offsetX
        return - self.eps * (
            LogSinkhornGPU.softmin_cuda_image(h, Ns, Ms, self.eps, dx)
            + self.offsetY + self.offset_const + self.lognuref - self.lognu
        )

    def get_dense_cost(self, ind=None):
        """
        Get dense cost matrix of given problems. If no argument is given, all 
        costs are computed. Can be memory intensive, so it is recommended to do 
        small batches at a time.
        `ind` must be slice or iterable, not int.
        """

        if ind == None:
            ind = slice(None,)

        xs = tuple(x[ind] for x in self.xs)
        ys = tuple(y[ind] for y in self.ys)
        X = batch_shaped_cartesian_prod(xs)
        Y = batch_shaped_cartesian_prod(ys)
        B = X.shape[0]
        dim = X.shape[-1]
        C = ((X.view(B, -1, 1, dim) - Y.view(B, 1, -1, dim))**2).sum(dim=-1)
        return C, X, Y

    def get_dense_plan(self, ind=None, C=None):
        """
        Get dense plans of given problems. If no argument is given, all plans 
        are computed. Can be memory intensive, so it is recommended to do small 
        batches at a time.
        `ind` must be slice or iterable, not int.
        """
        if ind == None:
            ind = slice(None,)

        if C == None:
            C, _, _ = self.get_dense_cost(ind)

        B = C.shape[0]
        alpha, beta = self.alpha[ind], self.beta[ind]
        muref, nuref = self.muref[ind], self.nuref[ind]

        pi = torch.exp(
            (alpha.view(B, -1, 1) + beta.view(B, 1, -1) - C) / self.eps
        ) * muref.view(B, -1, 1) * nuref.view(B, 1, -1)
        return pi

    def change_eps(self, new_eps):
        """
        Change the regularization strength `self.eps`.
        In this solver this also involves renormalizing the offsets.
        """
        self.Niter = 0
        self.current_error = self.max_error + 1.
        scale = self.eps / new_eps
        self.offsetX = self.offsetX * scale
        self.offsetY = self.offsetY * scale
        self.offset_const = self.offset_const * scale
        self.eps = new_eps

    def get_dx(self):
        return self.C[0]


def convert_to_basic_2D(A, basic_grid_shape, cellsize):
    """
    A is a tensor of shape (B, m1, m2, *(rem_shape)), where
    B = prod(basic_grid_shape)/4
    m1 = m2 = 2*cellsize
    """
    B, m1, m2 = A.shape[:3]
    rem_shape = A.shape[3:]  # Rest of the shape, that we will not change
    sb1, sb2 = basic_grid_shape
    assert 4*B == sb1*sb2, "Batchsize does not match basic grid"
    assert m1 == m2 == 2*cellsize, "Problem size does not mach cellsize"
    new_shape = (sb1, sb2, cellsize, cellsize, *rem_shape)
    # Permute dimensions to make last X dimension that inner to cell
    A_res = A.view(sb1//2, sb2//2, 2, cellsize, 2,
                   cellsize, -1).permute(0, 2, 1, 4, 3, 5, 6)
    A_res = A_res.reshape(new_shape)
    return A_res


def convert_to_batch_2D(A):
    """
    A is a tensor of shape (sb1, sb2, cellsize, cellsize, *(rem_shape))
    """
    sb1, sb2, cellsize = A.shape[:3]
    rem_shape = A.shape[4:]
    new_shape = (sb1*sb2//4, 2*cellsize, 2*cellsize, *rem_shape)
    A_res = A.view(sb1//2, 2, sb2//2, 2, cellsize, cellsize, -1)
    A_res = A_res.permute(0, 2, 1, 4, 3, 5, 6).reshape(new_shape)
    return A_res


def get_cell_marginals(muref, nuref, alpha, beta, xs, ys, eps):
    """
    Get cell marginals directly using duals and logsumexp reductions, 
    without building the transport plans. 
    The mathematical formulation is covered in [TODO: ref]
    Returns tensor of size (B, n_basic, Ns), where B is the batch dimension and 
    n_basic the number of basic cells per composite cell.
    """
    Ms = LogSinkhornGPU.geom_dims(muref)
    Ns = LogSinkhornGPU.geom_dims(nuref)

    # Deduce cellsize
    s = Ms[0]//2
    dim = len(xs)
    assert dim == 2, "Not implemented for dimension rather than 2"
    n_basic = 2**dim  # number of basic cells per composite cell, depends on dim
    dx = (xs[0][0, 1] - xs[0][0, 0]).item()  # TODO: check consistency

    # Perform permutations and reshapes in X data to turn them
    # into B*n_cells problems of size (s,s)
    alpha_b = alpha.view(-1, 2, s, 2, s) \
        .permute((0, 1, 3, 2, 4)).reshape(-1, s, s)
    mu_b = muref.view(-1, 2, s, 2, s) \
        .permute((0, 1, 3, 2, 4)).reshape(-1, s, s)
    new_Ms = (s, s)
    logmu_b = LogSinkhornGPU.log_dens(mu_b)

    x1, x2 = xs
    x1_b = torch.repeat_interleave(x1.view(-1, 2, s, 1), 2, dim=3)
    x1_b = x1_b.permute((0, 1, 3, 2)).reshape(-1, s)
    x2_b = torch.repeat_interleave(x2.view(-1, 1, 2, s), 2, dim=1)
    x2_b = x2_b.reshape(-1, s)
    xs_b = (x1_b, x2_b)

    # Duplicate Y data to match X data
    y1, y2 = ys
    y1_b = torch.repeat_interleave(y1, n_basic, dim=0)
    y2_b = torch.repeat_interleave(y2, n_basic, dim=0)
    xs_b = (x1_b, x2_b)
    ys_b = (y1_b, y2_b)

    # Perform a reduction to get a second dual for each basic cell
    offsetX, offsetY, offset_const = compute_offsets_sinkhorn_grid(
        xs_b, ys_b, eps)
    h = alpha_b / eps + logmu_b + offsetX
    beta_hat = - eps * (
        LogSinkhornGPU.softmin_cuda_image(h, Ns, new_Ms, eps, dx)
        + offsetY + offset_const
    )

    # Turn to double to improve accuracy
    # beta = beta.double()
    # beta_hat = beta_hat.double()
    # nuref = nuref.double()

    # Build cell marginals
    nu_basic = nuref[:, None] * torch.exp(
        (beta[:, None] - beta_hat.view(-1, n_basic, *Ns))/eps
    )
    return nu_basic


def BatchIterate(
    muY, posY, dx, eps,
    # TODO: remove this unnecesary input
    partitionDataCompCells, partitionDataCompCellIndices,
    muYAtomicDataList, muYAtomicIndicesList,
    muXJ, posXJ, alphaJ, betaDataList, betaIndexList, shapeY,
    SinkhornError=1E-4, SinkhornErrorRel=False, SinkhornMaxIter=None,
    SinkhornInnerIter=100, BatchSize=np.inf
):

    BatchTotal = muXJ.shape[0]
    if BatchSize == np.inf:
        BatchSize = BatchTotal

    # Divide problem data into batches of size BatchSize
    for i in range(0, BatchTotal, BatchSize):
        # Prepare batch of problem data
        muXBatch = muXJ[i:i+BatchSize]
        # posXJ is list of coordinates along dimensions
        posXBatch = tuple(x[i:i+BatchSize] for x in posXJ)
        alphaBatch = alphaJ[i:i+BatchSize]
        muYData = muYAtomicDataList
        # partitionDataCompCellIndicesBatch = partitionDataCompCellIndices[i:i+BatchSize]
        partitionDataCompCellsBatch = partitionDataCompCells[i:i+BatchSize]
        current_batch = len(partitionDataCompCellsBatch)

        # Solve batch
        resultAlpha, resultBeta, resultMuYAtomicDataList, \
            resultMuYCellIndicesList, info = BatchDomDecIteration_CUDA(
                SinkhornError, SinkhornErrorRel, muY, posY, dx, eps, shapeY,
                muXBatch, posXBatch, alphaBatch,
                [(muYAtomicDataList[j] for j in J)
                 for J in partitionDataCompCellsBatch],
                [(muYAtomicIndicesList[j] for j in J)
                 for J in partitionDataCompCellsBatch],
                # partitionDataCompCellIndicesBatch[i],
                SinkhornMaxIter, SinkhornInnerIter, current_batch
            )

        # Extract results
        alphaJ[i:i+BatchSize] = resultAlpha
        # TODO: how to extract beta
        # betaDataList[i*BatchSize+k]=resultBeta[k]
        # betaIndexList[i*BatchSize+k]=muYCellIndices.copy()[k]
        # Extract basic cell marginals
        # All composite cells have same size
        lenJ = len(partitionDataCompCellsBatch[0])
        assert lenJ * current_batch == len(resultMuYAtomicDataList)
        # Iterate over composite cells...
        for (k, J) in enumerate(partitionDataCompCellsBatch):
            # ...and then over basic cells inside each composite cell
            for (j, b) in enumerate(J):
                muYAtomicDataList[b] = resultMuYAtomicDataList[lenJ*k + j]
                muYAtomicIndicesList[b] = resultMuYCellIndicesList[lenJ*k + j]

    return alphaJ, muYAtomicIndicesList, muYAtomicDataList, info
    # for jsub,j in enumerate(partitionDataCompCellsBatch):
    #     muYAtomicDataList[j]=resultMuYAtomicDataList[jsub]
    #     muYAtomicIndicesList[j]=muYCellIndices.copy()


def BatchDomDecIteration_CUDA(
        SinkhornError, SinkhornErrorRel, muY, posYCell, dx, eps, shapeY,
        # partitionDataCompCellIndices,
        muXCell, posXCell, alphaCell, muYAtomicListData, muYAtomicListIndices,
        SinkhornMaxIter, SinkhornInnerIter, BatchSize, balance=True):

    # 1: compute composite cell marginals
    info = dict()
    muYCellData = []
    muYCellIndices = []
    t0 = time.time()
    for i in range(BatchSize):
        arrayAdder = LogSinkhorn.TSparseArrayAdder()
        for x, y in zip(muYAtomicListData[i], muYAtomicListIndices[i]):
            arrayAdder.add(x, y)
        muYCellData.append(arrayAdder.getDataTuple()[0])
        muYCellIndices.append(arrayAdder.getDataTuple()[1])

    # 2: compute bounding box and copy data to it. Also get reference measure
    # in boxes
    # TODO: for Sang: muYCell are not relevant for unbalanced domdec, what one
    # needs here are the nu_minus. subMuY is the reference measure
    muYCell, subMuY, left, bottom, width, height = batch_cell_marginals_2D(
        muYCellIndices, muYCellData, shapeY, muY
    )
    info["time_bounding_box"] = time.time() - t0
    info["bounding_box"] = (width, height)
    # Turn muYCell, left, bottom and subMuY into tensor
    device = muXCell.device
    dtype = muXCell.dtype
    muYCell = torch.tensor(muYCell, device=device, dtype=dtype)
    subMuY = torch.tensor(subMuY, device=device, dtype=dtype)
    left_cuda = torch.tensor(left, device=device)
    bottom_cuda = torch.tensor(bottom, device=device)

    # 3: get physical coordinates of bounding box for each batched problem
    posYCell = get_grid_cartesian_coordinates(
        left_cuda, bottom_cuda, width, height, dx
    )

    # 4. Solve problem

    t0 = time.time()
    resultAlpha, resultBeta, Nu_basic, info_solver = BatchSolveOnCell_CUDA(
        muXCell, muYCell, posXCell, posYCell, eps, alphaCell, subMuY,
        SinkhornError, SinkhornErrorRel, SinkhornMaxIter=SinkhornMaxIter,
        SinkhornInnerIter=SinkhornInnerIter
    )
    info["time_sinkhorn"] = time.time() - t0
    # Renormalize Nu_basic
    Nu_basic = Nu_basic * \
        (muYCell / (Nu_basic.sum(dim=1) + 1e-30))[:, None, :, :]

    # # 5. Turn back to numpy
    # Nu_basic = Nu_basic.cpu().numpy()

    # # 6. Balance. Plain DomDec code works here
    # t0 = time.time()
    # if balance:
    #     batch_balance(muXCell, Nu_basic)
    # info["time_balance"] = time.time() - t0

    # 5. CUDA balance
    t0 = time.time()
    if balance:
        CUDA_balance(muXCell, Nu_basic)
    info["time_balance"] = time.time() - t0

    # 6. Turn back to numpy
    Nu_basic = Nu_basic.cpu().numpy()

    # 7. Extract new atomic muY and truncate
    t0 = time.time()
    MuYAtomicIndicesList, MuYAtomicDataList = unpack_cell_marginals_2D(
        Nu_basic, left, bottom, shapeY
    )
    info["time_truncation"] = time.time() - t0

    # resultMuYAtomicDataList = []
    # # The batched version always computes directly the cell marginals
    # for i in range(BatchSize):
    #     resultMuYAtomicDataList.append([np.array(pi[i,j]) for j in range(pi.shape[1])])
    info = {**info, **info_solver}
    return resultAlpha, resultBeta, MuYAtomicDataList, MuYAtomicIndicesList, info


def BatchSolveOnCell_CUDA(
    muXCell, muYCell, posX, posY, eps, alphaInit, muYref,
    SinkhornError=1E-4, SinkhornErrorRel=False, YThresh=1E-14, verbose=True,
    SinkhornMaxIter=10000, SinkhornInnerIter=10
):

    # Retrieve BatchSize
    B = muXCell.shape[0]
    dim = len(posX)
    assert dim == 2, "Not implemented for dimension != 2"

    # Retrieve cellsize
    s = muXCell.shape[-1] // 2

    # Define cost for solver
    C = (posX, posY)
    # Solve problem
    solver = LogSinkhornCudaImageOffset(
        muXCell, muYCell, C, eps, alpha_init=alphaInit, nuref=muYref,
        max_error=SinkhornError, max_error_rel=SinkhornErrorRel,
        max_iter=SinkhornMaxIter, inner_iter=SinkhornInnerIter
    )

    msg = solver.iterate_until_max_error()

    alpha = solver.alpha
    beta = solver.beta
    # Compute cell marginals directly
    pi_basic = get_cell_marginals(
        muXCell, muYref, alpha, beta, posX, posY, eps
    )

    # Wrap solver and possibly runtime info into info dictionary
    info = {
        "solver": solver,
        "msg": msg
    }

    return alpha, beta, pi_basic, info

#######
# Duals
#######


def get_alpha_field_gpu(alpha, shape, cellsize):
    # TODO: generalize to 3D
    comp_shape = tuple(s // (2*cellsize) for s in shape)
    alpha_field = alpha.view(*comp_shape, 2*cellsize, 2*cellsize) \
                       .permute(0, 2, 1, 3).contiguous().view(shape)
    return alpha_field


def get_alpha_field_even_gpu(alphaA, alphaB, shapeXL, shapeXL_pad,
                             cellsize, meta_cell_shape, muX=None,
                             requestAlphaGraph=False):
    """
    Uses alphaA, alphaB and getAlphaGraph to compute one global dual variable
    alpha from alphaAList and alphaBList."""
    dim = len(alphaA.shape)-1
    alphaA_field = get_alpha_field_gpu(alphaA, shapeXL, cellsize)
    alphaB_field = get_alpha_field_gpu(alphaB, shapeXL_pad, cellsize)
    # Remove padding
    # TODO: generalize to 3D
    s1, s2 = shapeXL
    alphaB_field = alphaB_field[cellsize:s1+cellsize, cellsize:s2+cellsize]
    alphaDiff = (alphaA_field-alphaB_field).cpu().numpy().ravel()
    alphaGraph = DomDec.getAlphaGraph(
        alphaDiff, meta_cell_shape, cellsize, muX
    )

    # Each offset in alphaGraph is for one of the batched problems in alphaA
    alphaGraphGPU = torch.tensor(
        alphaGraph, device=alphaA.device, dtype=alphaA.dtype
    )
    alphaAEven = alphaA - alphaGraphGPU.view(-1, *np.ones(dim, dtype=np.int))
    # alphaFieldEven = alphaA_field.cpu().numpy()
    # for a, c in zip(alphaGraph.ravel(), cellsA):
    #     print(c)
    #     alphaFieldEven[np.array(c)] -= a
    alphaFieldEven = get_alpha_field_gpu(alphaAEven, shapeXL, cellsize)
    alphaFieldEven = alphaFieldEven.cpu().numpy().ravel()

    if requestAlphaGraph:
        return (alphaFieldEven, alphaGraph)

    return alphaFieldEven


###################################################
# Try to do everything in the bounding box format
###################################################

# CUDA version of balancing
def CUDA_balance(muXCell, Nu_basic):
    B, M, _ = muXCell.shape
    s = M//2
    atomic_mass = muXCell.view(B, 2, s, 2, s).sum(dim=(2, 4))
    atomic_mass = atomic_mass.view(B, -1)
    Nu_basic_shape = Nu_basic.shape
    Nu_basic = Nu_basic.view(B, 4, -1)
    atomic_mass_nu = Nu_basic.sum(-1)
    mass_delta = atomic_mass_nu - atomic_mass
    if Nu_basic.dtype == torch.float64:
        LogSinkhornGPU.BalanceCUDA_64(Nu_basic, mass_delta, 1e-12)
    elif Nu_basic.dtype == torch.float32:
        LogSinkhornGPU.BalanceCUDA_32(Nu_basic, mass_delta, 1e-12)
    else:
        raise NotImplementedError()
    return Nu_basic.view(*Nu_basic_shape)

# CUDA functionality to get relative extents of bounding boxes


def get_axis_bounds(Nu_basic, mask, global_minus, axis):
    B, C = Nu_basic.shape[:2]
    geom_shape = Nu_basic.shape[2:]
    n = geom_shape[axis]
    # Put in the position of every point with mass its index along axis
    index_axis = torch.arange(n, device=Nu_basic.device, dtype=torch.int)
    new_shape_index = [n if i == 2 +
                       axis else 1 for i in range(len(Nu_basic.shape))]
    index_axis = index_axis.view(new_shape_index)
    mask_index = mask*index_axis
    # Get positive extreme
    basic_plus = mask_index.view(B, C, -1).amax(-1)
    # Turn zeros to upper bound so that we can get the minimum
    mask_index[~mask] = n
    basic_minus = mask_index.view(B, C, -1).amin(-1)
    basic_extent = basic_plus - basic_minus + 1
    # Add global offsets
    global_basic_minus = global_minus + basic_minus
    global_basic_plus = global_minus + basic_plus
    # Reduce to composite cell
    global_composite_minus = global_basic_minus.amin(-1)
    global_composite_plus = global_basic_plus.amax(-1)
    composite_extent = global_composite_plus - global_composite_minus + 1
    # Get dim of bounding box
    max_composite_extent = torch.max(composite_extent).item()
    relative_basic_minus = global_basic_minus - \
        global_composite_minus.view(-1, 1)
    return relative_basic_minus, basic_minus, basic_extent, global_composite_minus, max_composite_extent

# TODO: code for 3D


def basic_to_composite_CUDA_2D(Nu_basic, global_left, global_bottom):
    B, C = Nu_basic.shape[:2]
    mask = Nu_basic > 0.0
    # Get bounding box parameters
    relative_basic_left, basic_left, basic_width, \
        global_composite_left, composite_width = \
        get_axis_bounds(Nu_basic, mask, global_left, 0)
    relative_basic_bottom, basic_bottom, basic_height, \
        global_composite_bottom, composite_height = \
        get_axis_bounds(Nu_basic, mask, global_bottom, 1)

    Nu_comp = LogSinkhornGPU.BasicToCompositeCUDA_2D(
        Nu_basic, composite_width, composite_height,
        relative_basic_left, basic_left, basic_width,
        relative_basic_bottom, basic_bottom, basic_height
    )
    return Nu_comp, global_composite_left, global_composite_bottom


def unpack_cell_marginals_2D_box(Nu_basic, left, bottom, shapeY):
    """
    Un-batch all the cell marginals and truncate entries below `threshold`.
    """
    # TODO: generalize to 3D
    # Nu_basic is of size (B, 4, w, h), because there are 4 basic cells per
    # left and bottom are of size (B, 4)
    _, n = shapeY
    # Do all the process in the cpu
    B = Nu_basic.shape[0]
    marg_indices = []
    marg_data = []
    # NOTE: extraction could be done for the whole Nu_basic at once,
    # but then how to distinguish between slices.
    for k in range(B):
        # idx, idy = np.nonzero(Nu_basic[k, i])
        idx, idy = np.nonzero(Nu_basic[k] > 0)
        linear_id = (idx+left[k])*n + idy + bottom[k]
        marg_indices.append(linear_id)
        marg_data.append(Nu_basic[k, idx, idy])
    return marg_indices, marg_data


def BatchIterateBox(
    muY, posY, dx, eps,
    muXJ, posXJ, alphaJ,
    nu_basic, left, bottom, shapeY,
    partition="A",
    SinkhornError=1E-4, SinkhornErrorRel=False, SinkhornMaxIter=None,
    SinkhornInnerIter=100, BatchSize=np.inf
):

    # assert BatchSize == np.inf, "not implemented for partial BatchSize"
    if partition == "A":
        # Global nu_basic has shape (b1, b2, w, h)
        # TODO: generalize for 3D
        nu_basic_part = nu_basic
        left_part = left
        bottom_part = bottom
    else:
        (b1, b2, w, h) = nu_basic.shape
        torch_options = dict(device = nu_basic.device, dtype = nu_basic.dtype)
        nu_basic_part = torch.zeros((b1+2, b2+2, w, h), **torch_options)
        nu_basic_part[1:-1,1:-1] = nu_basic
        # Pad left and bottom with extension of actual values
        left_part = pad_replicate_2D(left,1)
        bottom_part = pad_replicate_2D(bottom,1)

    # Solve batch
    alphaJ, betaJ, nu_basic_part, left_part, bottom_part, info = \
        BatchDomDecIterationBox_CUDA(
            SinkhornError, SinkhornErrorRel, muY, posY, dx, eps, shapeY,
            muXJ, posXJ, alphaJ,
            nu_basic_part, left_part, bottom_part,
            SinkhornMaxIter, SinkhornInnerIter
        )
    if partition == "A":
        # TODO: generalize for 3D
 
        nu_basic = nu_basic_part
        left = left_part
        bottom = bottom_part
    else:
        nu_basic = nu_basic_part[1:-1,1:-1]
        left = left_part[1:-1,1:-1]
        bottom = bottom_part[1:-1,1:-1]

    return alphaJ, nu_basic, left, bottom, info
    # for jsub,j in enumerate(partitionDataCompCellsBatch):
    #     muYAtomicDataList[j]=resultMuYAtomicDataList[jsub]
    #     muYAtomicIndicesList[j]=muYCellIndices.copy()


# TODO: finish this
# def BatchIterateBox(
#     muY, posY, dx, eps,
#     muXJ, posXJ, alphaJ,
#     nu_basic, left, bottom, shapeY,
#     partition="A",
#     SinkhornError=1E-4, SinkhornErrorRel=False, SinkhornMaxIter=None,
#     SinkhornInnerIter=100, BatchSize=np.inf
# ):
#     torch_options = dict(device = nu_basic.device, dtype = nu_basic.dtype)
#     # assert BatchSize == np.inf, "not implemented for partial BatchSize"
#     if partition == "A":
#         # Global nu_basic has shape (b1, b2, w, h)
#         # TODO: generalize for 3D
#         nu_basic_part = nu_basic
#         left_part = left
#         bottom_part = bottom
#     else:
#         (b1, b2, w, h) = nu_basic.shape
#         nu_basic_part = torch.zeros((b1+2, b2+2, w, h), **torch_options)
#         nu_basic_part[1:-1,1:-1] = nu_basic
#         # Pad left and bottom with extension of actual values
#         left_part = pad_replicate_2D(left,1)
#         bottom_part = pad_replicate_2D(bottom,1)

#     BatchTotal = muXJ.shape[0]
#     if BatchSize == np.inf:
#         BatchSize = BatchTotal

#     else:
#         # Make sure that BatchSize is an integer number of nu_basic rows
#         print(nu_basic_part.shape)
#         b1, b2 = nu_basic_part.shape[:2]
#         BatchSize = (2*b2)* BatchSize // (2*b2)
#     nu_basic_results = []

#     # Divide problem data into batches of size BatchSize
#     for i in range(0, BatchTotal, BatchSize):
#         print(BatchSize, (i+BatchSize)//b2)
#         muXBatch = muXJ[i:i+BatchSize]
#         posXBatch = tuple(x[i:i+BatchSize] for x in posXJ)
#         alphaBatch = alphaJ[i:i+BatchSize]
#         nu_basic_batch = nu_basic_part[i//b2:(i+BatchSize)//b2]
#         left_batch = left_part[i//b2:(i+BatchSize)//b2].clone()
#         bottom_batch = bottom_part[i//b2:(i+BatchSize)//b2].clone()
#         # Solve batch
#         resultAlpha, resultBeta, nu_basic_batch, left_batch, bottom_batch, info = \
#             BatchDomDecIterationBox_CUDA(
#                 SinkhornError, SinkhornErrorRel, muY, posY, dx, eps, shapeY,
#                 muXBatch, posXBatch, alphaBatch,
#                 nu_basic_batch, left_batch, bottom_batch,
#                 SinkhornMaxIter, SinkhornInnerIter
#             )
#         alphaJ[i:i+BatchSize] = resultAlpha
#         nu_basic_results.append(nu_basic_batch) # must match shape later
#         left_part[i//b2:(i+BatchSize)//b2] = left_batch
#         bottom_part[i//b2:(i+BatchSize)//b2] = bottom_batch

#     # Joint all partial results together
#     max_width = max(nu_i.shape[2] for nu_i in nu_basic_results)
#     max_height = max(nu_i.shape[3] for nu_i in nu_basic_results)
#     nu_result_part = torch.zeros((b1, b2, max_width, max_height), **torch_options)
#     for i in range(0, BatchTotal, BatchSize):
#         nu_result_part[i//b2:(i+BatchSize)//b2] = nu_basic_results[i//BatchSize]

#     if partition == "A":
#         # TODO: generalize for 3D
 
#         nu_basic = nu_basic_part
#         left = left_part
#         bottom = bottom_part
#     else:
#         nu_basic = nu_basic_part[1:-1,1:-1]
#         left = left_part[1:-1,1:-1]
#         bottom = bottom_part[1:-1,1:-1]

#     return resultAlpha, nu_basic, left, bottom, info
#     # for jsub,j in enumerate(partitionDataCompCellsBatch):
#     #     muYAtomicDataList[j]=resultMuYAtomicDataList[jsub]
#     #     muYAtomicIndicesList[j]=muYCellIndices.copy()


def BatchDomDecIterationBox_CUDA(
        SinkhornError, SinkhornErrorRel, muY, posYCell, dx, eps, shapeY,
        # partitionDataCompCellIndices,
        muXCell, posXCell, alphaCell,
        nu_basic, left, bottom,
        SinkhornMaxIter, SinkhornInnerIter, balance=True):

    info = dict()
    # 1: compute composite cell marginals
    # Get basic shape size

    t0 = time.time()
    b1, b2, w0, h0 = nu_basic.shape
    torch_options = dict(device=nu_basic.device, dtype=nu_basic.dtype)
    torch_options_int = dict(device=nu_basic.device, dtype=torch.int32)
    c1, c2 = b1//2, b2//2
    nu_basic = nu_basic.reshape(c1, 2, c2, 2, w0, h0).permute(0, 2, 1, 3, 4, 5) \
        .reshape(c1*c2, 4, w0, h0)
    left = left.reshape(c1, 2, c2, 2).permute(0, 2, 1, 3).reshape(c1*c2, 4)
    bottom = bottom.reshape(c1, 2, c2, 2).permute(0, 2, 1, 3).reshape(c1*c2, 4)
    # Get composite marginals as well as new left and right
    muYCell, left, bottom = basic_to_composite_CUDA_2D(
        nu_basic, left, bottom)
    info["time_bounding_box"] = time.time() - t0

    # TODO: get subMuY; for now just copy muYCell
    subMuY = muYCell

    # 2. Get bounding box dimensions
    w, h = muYCell.shape[1:]
    info["bounding_box"] = (w, h)

    # 3: get physical coordinates of bounding box for each batched problem
    posYCell = get_grid_cartesian_coordinates(
        left, bottom, w, h, dx
    )

    # 4. Solve problem

    t0 = time.time()
    # print(muXCell.shape, muYCell.shape, posXCell[0].shape, posYCell[0].shape)
    resultAlpha, resultBeta, nu_basic, info_solver = \
        BatchSolveOnCell_CUDA(
            muXCell, muYCell, posXCell, posYCell, eps, alphaCell, subMuY,
            SinkhornError, SinkhornErrorRel, SinkhornMaxIter=SinkhornMaxIter,
            SinkhornInnerIter=SinkhornInnerIter
    )
    # Renormalize nu_basic 
    nu_basic = nu_basic * \
        (muYCell / (nu_basic.sum(dim=1) + 1e-40))[:, None, :, :]
    info["time_sinkhorn"] = time.time() - t0

    # # 5. Turn back to numpy
    # nu_basic = nu_basic.cpu().numpy()

    # # 6. Balance. Plain DomDec code works here
    # t0 = time.time()
    # if balance:
    #     batch_balance(muXCell, nu_basic)
    # info["time_balance"] = time.time() - t0

    # 5. CUDA balance
    t0 = time.time()
    if balance:
        CUDA_balance(muXCell, nu_basic)
    info["time_balance"] = time.time() - t0

    # 7. Truncate
    t0 = time.time()
    # TODO: if too slow or too much memory turn to dedicated cuda function
    nu_basic[nu_basic <= 1e-15] = 0.0
    info["time_truncation"] = time.time() - t0

    # Turn back to rectangular shape
    nu_basic = nu_basic.reshape(c1, c2, 2, 2, w, h).permute(0, 2, 1, 3, 4, 5) \
        .reshape(b1, b2, w, h)

    basic_expander = torch.ones((1, 2, 1, 2), **torch_options_int)
    left = left.reshape(c1, 1, c1, 1) * basic_expander
    left = left.view(b1, b2)
    bottom = bottom.reshape(c1, 1, c1, 1) * basic_expander
    bottom = bottom.view(b1, b2)

    # resultMuYAtomicDataList = []
    # # The batched version always computes directly the cell marginals
    # for i in range(BatchSize):
    #     resultMuYAtomicDataList.append([np.array(pi[i,j]) for j in range(pi.shape[1])])
    info = {**info, **info_solver}
    return resultAlpha, resultBeta, nu_basic, left, bottom, info
