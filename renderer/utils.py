import math
from typing import Optional
import torch
from torch import Tensor
from torch.nn import functional as F
import numpy as np
import cv2


def convert_spherical_to_cartesian(
    shperical_coordinates: Tensor,
    degrees: bool = True,
) -> torch.Tensor:
    """Converts spherical coordinates to cartesian coordinates.

    Args:
        shperical_coordinates (Tensor): Tensor of shape (N, 3) containing spherical coordinates. r, theta, phi.
        degrees (bool, optional): Use degrees instead of radians. Defaults to True.

    Returns:
        torch.Tensor: _description_
    """    
    assert shperical_coordinates.dim() == 2
    assert shperical_coordinates.shape[1] == 3

    if degrees:
        shperical_coordinates[:, 1:] = math.pi / 180.0 * shperical_coordinates[:, 1:]

    dist = shperical_coordinates[:, 0]
    elev = shperical_coordinates[:, 1]
    azim = shperical_coordinates[:, 2]

    x = dist * torch.sin(elev) * torch.cos(azim)
    y = dist * torch.sin(elev) * torch.sin(azim)
    z = dist * torch.cos(elev)

    return torch.stack([x, y, z], dim=-1)


def look_at_rotation(
    camera_position: Tensor,
    at_point: Optional[Tensor] = None,
    up_axis: Optional[Tensor] = None
) -> Tensor:
    """
    This function takes a vector 'camera_position' which specifies the location
    of the camera in world coordinates and two vectors `at` and `up` which
    indicate the position of the object and the up directions of the world
    coordinate system respectively. The object is assumed to be centered at
    the origin.

    The output is a rotation matrix representing the transformation
    from world coordinates -> view coordinates.

    Args:
        camera_position: position of the camera in world coordinates
        at: position of the object in world coordinates
        up: vector specifying the up direction in the world coordinate frame.

    The inputs camera_position, at and up can each be a
        - 3 element tuple/list
        - torch tensor of shape (1, 3)
        - torch tensor of shape (N, 3)

    The vectors are broadcast against each other so they all have shape (N, 3).

    Returns:
        R: (N, 3, 3) batched rotation matrices
    """
    assert camera_position.dim() == 2
    assert camera_position.shape[-1] == 3
    
    if up_axis is None:
        up_axis = torch.tensor([[0, 0, 1]], device=camera_position.device, dtype=camera_position.dtype)
    
    if at_point is None:
        at_point = torch.tensor([[0, 0, 0]], device=camera_position.device, dtype=camera_position.dtype)

    z_axis = F.normalize(at_point - camera_position, eps=1e-5)
    x_axis = F.normalize(torch.cross(up_axis, z_axis, dim=1), eps=1e-5)
    y_axis = F.normalize(torch.cross(z_axis, x_axis, dim=1), eps=1e-5)
    is_close = torch.isclose(x_axis, torch.tensor(0.0, device=camera_position.device, dtype=camera_position.dtype), atol=5e-3).all(
        dim=1, keepdim=True
    )
    if is_close.any():
        replacement = F.normalize(torch.cross(y_axis, z_axis, dim=1), eps=1e-5)
        x_axis = torch.where(is_close, replacement, x_axis)
    R = torch.cat((x_axis[:, None, :], y_axis[:, None, :], z_axis[:, None, :]), dim=1)
    return R.transpose(1, 2)

def silly_rasterizer(vertices_screen: np.ndarray, z_values: np.ndarray, faces: np.ndarray, width: int, height: int) -> np.ndarray:
    """Rasterizes a mesh using the vertices and faces.

    Args:
        vertices_screen (np.ndarray): Vertices in screen space.
        z_values (np.ndarray): Z values of the vertices.
        faces (np.ndarray): Faces of the mesh.
        width (int): Width of the image.
        height (int): Height of the image.
        channels (int, optional): Number of channels. Defaults to 1.

    Returns:
        np.ndarray: Rasterized mesh.
    """    
    assert vertices_screen.shape[0] == z_values.shape[0]
    assert vertices_screen.shape[1] == 2
    assert vertices_screen.shape[2] == 3
    assert faces.shape[1] == 3
    assert faces.shape[0] == z_values.shape[0]

    z_values /= z_values.max()
    z_order = np.argsort([(z_values[i] + z_values[j] + z_values[k]) / -3 for i,j,k in np.asarray(faces)])

    image = np.zeros((height, width, 3), dtype=np.uint32)

    for face in faces[z_order]:
        v0, v1, v2 = vertices_screen[face]
        z0, z1, z2 = z_values[face]
        avg_z = (z0 + z1 + z2) / 3
        color = np.asarray([255 * (1 - avg_z)] * 3, dtype=np.uint32)∏

        cv2.fillConvexPoly(image, np.int32([v0, v1, v2]), color)

    return image
