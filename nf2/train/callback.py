import numpy as np
import wandb
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
from mpl_toolkits.axes_grid1 import make_axes_locatable
from pytorch_lightning import Callback
import torch

from nf2.data.util import cartesian_to_spherical, vector_cartesian_to_spherical


class SphericalSlicesCallback(Callback):

    def __init__(self, name, cube_shape, gauss_per_dB, Mm_per_ds):
        self.name = name
        self.cube_shape = cube_shape
        self.gauss_per_dB = gauss_per_dB
        self.Mm_per_ds = Mm_per_ds

    def on_validation_epoch_end(self, trainer, pl_module):
        if self.name not in pl_module.validation_outputs:
            return
        outputs = pl_module.validation_outputs[self.name]
        b = outputs['b'] * self.gauss_per_dB
        j = outputs['j'] * self.gauss_per_dB / self.Mm_per_ds
        coords = outputs['coords']

        b_cube = b.reshape([*self.cube_shape, 3]).cpu().numpy()
        j_cube = j.reshape([*self.cube_shape, 3]).cpu().numpy()
        c_cube = coords.reshape([*self.cube_shape, 3]).cpu().numpy()

        # transform to spherical coordinates
        c_cube = cartesian_to_spherical(c_cube)
        b_cube = vector_cartesian_to_spherical(b_cube, c_cube)

        self.plot_b(b_cube, c_cube)
        self.plot_current(j_cube, c_cube)

    def plot_b(self, b, coords):
        n_samples = b.shape[0]
        fig, axs = plt.subplots(3, n_samples, figsize=(n_samples * 4, 12))
        for i in range(3):
            for j in range(n_samples):
                v_min_max = np.max(np.abs(b[j, :, :]))
                extent = [coords[j, 0, 0, 2], coords[j, -1, -1, 2],
                          coords[j, 0, 0, 1], coords[j, -1, -1, 1]]
                extent = np.rad2deg(extent)
                height = coords[j, :, :, 0].mean()
                im = axs[i, j].imshow(b[j, :, :, i], cmap='gray', vmin=-v_min_max, vmax=v_min_max,
                                      origin='upper', extent=extent)
                axs[i, j].set_xlabel('Longitude [deg]')
                axs[i, j].set_ylabel('Latitude [deg]')
                # add locatable colorbar
                divider = make_axes_locatable(axs[i, j])
                cax = divider.append_axes("right", size="5%", pad=0.05)
                plt.colorbar(im, cax=cax, label='B [G]')
                axs[i, j].set_title(f'{height:.02f} - $B_{["r", "t", "p"][i]}$')
        fig.tight_layout()
        wandb.log({f"{self.name} - B": fig})
        plt.close('all')

    def plot_current(self, j, coords):
        j = (j ** 2).sum(-1) ** 0.5
        n_samples = j.shape[0]
        fig, axs = plt.subplots(1, n_samples, figsize=(n_samples * 4, 4))
        for i in range(n_samples):
            extent = [coords[i, 0, 0, 2], coords[i, -1, -1, 2],
                      coords[i, 0, 0, 1], coords[i, -1, -1, 1]]
            extent = np.rad2deg(extent)
            height = coords[i, :, :, 0].mean()
            im = axs[i].imshow(j[i, :, :], cmap='viridis', origin='upper', norm=LogNorm(), extent=extent)
            axs[i].set_xlabel('Longitude [deg]')
            axs[i].set_ylabel('Latitude [deg]')
            # add locatable colorbar
            divider = make_axes_locatable(axs[i])
            cax = divider.append_axes("right", size="5%", pad=0.05)
            plt.colorbar(im, cax=cax, label='J [G/ds]')
            axs[i].set_title(f'{height:.02f} - $|J|$')
        fig.tight_layout()
        wandb.log({f"{self.name} - Current density": fig})
        plt.close('all')
        # plot integrated current density
        j = np.sum(j, axis=0)
        fig, ax = plt.subplots(1, 1, figsize=(8, 8))
        im = ax.imshow(j, cmap='viridis', origin='upper', norm=LogNorm(), extent=extent)
        # add locatable colorbar
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        plt.colorbar(im, cax=cax)
        #
        fig.tight_layout()
        wandb.log({f"{self.name} - Integrated Current density": fig})
        plt.close('all')


class SlicesCallback(Callback):

    def __init__(self, name, cube_shape, gauss_per_dB, Mm_per_ds):
        self.name = name
        self.cube_shape = cube_shape
        self.gauss_per_dB = gauss_per_dB
        self.Mm_per_ds = Mm_per_ds

    def on_validation_epoch_end(self, trainer, pl_module):
        if self.name not in pl_module.validation_outputs:
            return
        outputs = pl_module.validation_outputs[self.name]
        b = outputs['b'] * self.gauss_per_dB
        j = outputs['j'] * self.gauss_per_dB / self.Mm_per_ds
        coords = outputs['coords']

        b_cube = b.reshape([*self.cube_shape, 3]).cpu().numpy()
        j_cube = j.reshape([*self.cube_shape, 3]).cpu().numpy()
        c_cube = coords.reshape([*self.cube_shape, 3]).cpu().numpy()

        self.plot_b(b_cube, c_cube)
        self.plot_current(j_cube, c_cube)

    def plot_b(self, b, coords):
        n_samples = b.shape[2]
        fig, axs = plt.subplots(3, n_samples, figsize=(n_samples * 4, 12))
        for i in range(3):
            for j in range(n_samples):
                v_min_max = np.max(np.abs(b[:, :, j]))
                extent = [coords[0, 0, j, 0], coords[-1, -1, j, 0],
                          coords[0, 0, j, 1], coords[-1, -1, j, 1]]
                extent = np.array(extent) * self.Mm_per_ds
                height = coords[:, :, j, 2].mean() * self.Mm_per_ds
                im = axs[i, j].imshow(b[:, :, j, i].T, cmap='gray', vmin=-v_min_max, vmax=v_min_max,
                                      origin='lower', extent=extent)
                axs[i, j].set_xlabel('X [Mm]')
                axs[i, j].set_ylabel('Y [Mm]')
                # add locatable colorbar
                divider = make_axes_locatable(axs[i, j])
                cax = divider.append_axes("right", size="5%", pad=0.05)
                plt.colorbar(im, cax=cax, label='B [G]')
                axs[i, j].set_title(f'{height:.02f} - $B_{["x", "y", "z"][i]}$')
        fig.tight_layout()
        wandb.log({f"{self.name} - B": fig})
        plt.close('all')

    def plot_current(self, j, coords):
        j = (j ** 2).sum(-1) ** 0.5
        n_samples = j.shape[2]
        fig, axs = plt.subplots(1, n_samples, figsize=(n_samples * 4, 4))
        for i in range(n_samples):
            extent = [coords[0, 0, i, 0], coords[-1, -1, i, 0],
                      coords[0, 0, i, 1], coords[-1, -1, i, 1]]
            extent = np.array(extent) * self.Mm_per_ds
            height = coords[:, :, i, 2].mean() * self.Mm_per_ds
            im = axs[i].imshow(j[:, :, i].T, cmap='plasma', origin='lower', norm=LogNorm(), extent=extent)
            axs[i].set_xlabel('X [Mm]')
            axs[i].set_ylabel('Y [Mm]')
            # add locatable colorbar
            divider = make_axes_locatable(axs[i])
            cax = divider.append_axes("right", size="5%", pad=0.05)
            plt.colorbar(im, cax=cax, label='J [G/ds]')
            axs[i].set_title(f'{height:.02f} - $|J|$')
            axs[i].set_xlabel('X [Mm]')
            axs[i].set_ylabel('Y [Mm]')
        fig.tight_layout()
        wandb.log({f"{self.name} - Current density": fig})
        plt.close('all')
        # plot integrated current density
        j = np.sum(j, axis=2)
        fig, ax = plt.subplots(1, 1, figsize=(8, 8))
        im = ax.imshow(j.T, cmap='plasma', origin='lower', norm=LogNorm(), extent=extent)
        # add locatable colorbar
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        plt.colorbar(im, cax=cax)
        ax.set_xlabel('X [Mm]')
        ax.set_ylabel('Y [Mm]')
        #
        fig.tight_layout()
        wandb.log({f"{self.name} - Integrated Current density": fig})
        plt.close('all')

class BoundaryCallback(Callback):

    def __init__(self, validation_dataset_key, cube_shape, gauss_per_dB):
        self.validation_dataset_key = validation_dataset_key
        self.cube_shape = cube_shape
        self.gauss_per_dB = gauss_per_dB

    def on_validation_epoch_end(self, trainer, pl_module):
        if self.validation_dataset_key not in pl_module.validation_outputs:
            return

        outputs = pl_module.validation_outputs[self.validation_dataset_key]
        b = outputs['b'] * self.gauss_per_dB
        b_true = outputs['b_true'] * self.gauss_per_dB

        # apply transforms
        if 'transform' in outputs:
            transform = outputs['transform']
            b = torch.einsum('ijk,ik->ij', transform, b)

        # compute diff
        b_diff = torch.abs(b - b_true)
        b_diff = torch.nanmean(b_diff.pow(2).sum(-1).pow(0.5))
        evaluation = {'b_diff': b_diff.detach()}

        # compute diff error
        if 'b_err' in outputs:
            b_err = outputs['b_err'] * self.gauss_per_dB
            b_diff_err = torch.clip(torch.abs(b - b_true) - b_err, 0)
            b_diff_err = torch.nanmean(b_diff_err.pow(2).sum(-1).pow(0.5))
            evaluation['b_diff_err'] = b_diff_err.detach()

        wandb.log({"valid": {self.validation_dataset_key: evaluation}})

        b = b.cpu().numpy().reshape([*self.cube_shape, 3])
        b_true = b_true.cpu().numpy().reshape([*self.cube_shape, 3])

        self.plot_b(b, b_true)

    def plot_b(self, b, b_true):
        fig, axs = plt.subplots(3, 2, figsize=(8, 8))

        b_norm = np.nanmax(np.abs(b_true))
        b_norm = min(500, b_norm)

        im = axs[0, 0].imshow(b[..., 0].T, cmap='gray', vmin=-b_norm, vmax=b_norm, origin='lower')
        divider = make_axes_locatable(axs[0, 0])
        cax = divider.append_axes("right", size="5%", pad=0.05)
        plt.colorbar(im, cax=cax, label='B_r [G]')

        im = axs[0, 1].imshow(b_true[..., 0].T, cmap='gray', vmin=-b_norm, vmax=b_norm, origin='lower')
        divider = make_axes_locatable(axs[0, 1])
        cax = divider.append_axes("right", size="5%", pad=0.05)
        plt.colorbar(im, cax=cax, label='B_r [G]')

        im = axs[1, 0].imshow(b[..., 1].T, cmap='gray', vmin=-b_norm, vmax=b_norm, origin='lower')
        divider = make_axes_locatable(axs[1, 0])
        cax = divider.append_axes("right", size="5%", pad=0.05)
        plt.colorbar(im, cax=cax, label='B_t [G]')

        im = axs[1, 1].imshow(b_true[..., 1].T, cmap='gray', vmin=-b_norm, vmax=b_norm, origin='lower')
        divider = make_axes_locatable(axs[1, 1])
        cax = divider.append_axes("right", size="5%", pad=0.05)
        plt.colorbar(im, cax=cax, label='B_t [G]')

        im = axs[2, 0].imshow(b[..., 2].T, cmap='gray', vmin=-b_norm, vmax=b_norm, origin='lower')
        divider = make_axes_locatable(axs[2, 0])
        cax = divider.append_axes("right", size="5%", pad=0.05)
        plt.colorbar(im, cax=cax, label='B_p [G]')

        im = axs[2, 1].imshow(b_true[..., 2].T, cmap='gray', vmin=-b_norm, vmax=b_norm, origin='lower')
        divider = make_axes_locatable(axs[2, 1])
        cax = divider.append_axes("right", size="5%", pad=0.05)
        plt.colorbar(im, cax=cax, label='B_p [G]')

        fig.tight_layout()
        wandb.log({f"{self.validation_dataset_key} - B": fig})
        plt.close('all')


class MetricsCallback(Callback):

    def __init__(self, validation_dataset_key, gauss_per_dB, Mm_per_ds):
        self.validation_dataset_key = validation_dataset_key
        self.gauss_per_dB = gauss_per_dB
        self.Mm_per_ds = Mm_per_ds

    def on_validation_epoch_end(self, trainer, pl_module):
        if self.validation_dataset_key not in pl_module.validation_outputs:
            return
        outputs = pl_module.validation_outputs[self.validation_dataset_key]

        b = outputs['b'] * self.gauss_per_dB
        j = outputs['j'] * self.gauss_per_dB / self.Mm_per_ds

        div = outputs['div'] * self.gauss_per_dB / self.Mm_per_ds

        norm = torch.norm(b, dim=-1) * torch.norm(j, dim=-1)
        sigma = torch.norm(torch.cross(j, b, dim=-1), dim=-1) / norm
        j_weight = torch.norm(j, dim=-1)
        angle = (sigma * j_weight).sum() / j_weight.sum()
        angle = torch.clip(angle, -1. + 1e-7, 1. - 1e-7)
        theta_J = torch.arcsin(angle)
        theta_J = torch.rad2deg(theta_J)

        sigma_J = (torch.norm(torch.cross(j, b, dim=-1), dim=-1) / (torch.norm(b, dim=-1) + 1e-7)).sum() / (torch.norm(j, dim=-1).sum() + 1e-7)

        b_norm = b.pow(2).sum(-1).pow(0.5) + 1e-7
        div_loss = (div / b_norm).mean()

        ff_loss = torch.cross(j, b, dim=-1).pow(2).sum(-1).pow(0.5) / b_norm
        ff_loss = ff_loss.mean()

        wandb.log({"valid": {"divergence": div_loss.cpu().numpy(),
                             "force-free": ff_loss.cpu().numpy(),
                             "sigma_J": sigma_J.cpu().numpy(),
                             "theta_J": theta_J.cpu().numpy()}})
