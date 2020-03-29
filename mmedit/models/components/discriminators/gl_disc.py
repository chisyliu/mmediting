import torch
import torch.nn as nn
from mmcv.runner import load_checkpoint
from mmedit.models.registry import COMPONENTS
from mmedit.utils import get_root_logger

from .multi_layer_disc import MultiLayerDiscriminator


@COMPONENTS.register_module
class GLDiscs(nn.Module):
    """Discriminators in Global&Local

    This discriminator contains a local discriminator and a global
    discriminator as described in the original paper:
    Globally and locally Consistent Image Completion

    Args:
        global_disc_cfg (dict): Config dict to build global discriminator.
        local_disc_cfg (dict): Config dict to build local discriminator.
    """

    def __init__(self, global_disc_cfg, local_disc_cfg):
        super(GLDiscs, self).__init__()
        self.global_disc = MultiLayerDiscriminator(**global_disc_cfg)
        self.local_disc = MultiLayerDiscriminator(**local_disc_cfg)

        self.fc = nn.Linear(2048, 1, bias=True)

    def forward(self, g_img, l_img):

        g_pred = self.global_disc(g_img)
        l_pred = self.local_disc(l_img)

        pred = self.fc(torch.cat([g_pred, l_pred], dim=1))

        return pred

    def init_weights(self, pretrained=None):
        if isinstance(pretrained, str):
            logger = get_root_logger()
            load_checkpoint(self, pretrained, strict=False, logger=logger)
        elif pretrained is None:
            for m in self.modules():
                # Here, we only initialize the module with fc layer since the
                # conv and norm layers has been intialized in `ConvModule`.
                if isinstance(m, nn.Linear):
                    nn.init.normal_(m.weight.data, 0.0, 0.02)
                    nn.init.constant_(m.bias.data, 0.0)
        else:
            raise TypeError('pretrained must be a str or None')