import torch
from torch import nn

from layers import SirenLayer, ComplexExpLayer
from layers.initializers import SirenInitializer, SirenUniformInitializer
from models.sdf import SDF


class Siren(nn.Sequential, SDF):
    def __init__(
        self,
        in_features: int,
        hidden_dim: int,
        hidden_layers: int,
        out_features: int,
        outermost_linear: bool = False,
        first_layer_init: SirenInitializer = SirenUniformInitializer(
            omega=30.0, is_first=True
        ),
        hidden_layer_init: SirenInitializer = SirenUniformInitializer(
            omega=30.0, is_first=False
        ),
    ):
        """
            Siren model described in paper: https://arxiv.org/abs/2006.09661

        Args:
            in_features (int): Number of input features.
            hidden_dim (int): Number of hidden features.
            hidden_layers (int): Number of hidden layers.
            out_features (int): Number of output features.
            outermost_linear (bool, optional): Is final layer linear?. Defaults to False.
            init_scheme (SirenInitializer, optional): See 3.2 of the paper. Defaults to SirenUniformInitializer.
        """
        super().__init__()
        layers = []

        for i in range(hidden_layers):
            is_first = i == 0
            layers.append(
                SirenLayer(
                    in_features if is_first else hidden_dim,
                    hidden_dim,
                    init_scheme=first_layer_init if is_first else hidden_layer_init,
                )
            )
        final_layer = SirenLayer(
            hidden_dim, out_features, add_bias=True, disable_activation=outermost_linear
        )
        nn.init.zeros_(final_layer.bias)
        layers.append(final_layer)

        super().__init__(*layers)


class ComplexSiren(Siren):
    def __init__(
        self,
        in_features: int,
        hidden_dim: int,
        hidden_layers: int,
        out_features: int,
        outermost_linear: bool = False,
        first_layer_init: SirenInitializer = SirenUniformInitializer(
            omega=30.0, is_first=True
        ),
        hidden_layer_init: SirenInitializer = SirenUniformInitializer(
            omega=30.0, is_first=False
        ),
    ):
        super().__init__(
            in_features,
            hidden_dim,
            hidden_layers,
            out_features,
            outermost_linear,
            first_layer_init,
            hidden_layer_init,
        )

        first_layer = ComplexExpLayer(
            in_features=in_features,
            out_features=hidden_dim,
            init_scheme=first_layer_init,
        )
        self[0] = first_layer
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + 1.0  # TODO: Remove this hack
        return super().forward(x)
