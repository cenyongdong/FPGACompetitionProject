"""Isolated 2026 pose-only variant of Person-in-WiFi 3D.

The paper does not specify the differentiation MLP depth or initialization
variance.  The two-layer residual MLP and 1e-3 standard deviation below are
documented reproduction choices, not a claim about unpublished author code.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from mmcv.cnn import Linear
from mmcv.runner import force_fp32
from mmdet.core import reduce_mean
from opera.core.keypoint import bbox_kpt2result
from opera.models.transfer_support import migrate

from opera.models.builder import DETECTORS, HEADS
from opera.models.dense_heads.petr_head import PETRHead
from opera.models.detectors.petr import PETR
from opera.models.utils.builder import (TRANSFORMER,
                                        TRANSFORMER_LAYER_SEQUENCE)
from opera.models.utils.transformer import (PETRTransformer,
                                           PetrRefineTransformerDecoder)


class _CSIProjectionWithSTE(nn.Module):
    def __init__(self, projection, num_tokens=180, embed_dims=256):
        super().__init__()
        self.projection = projection
        self.ste = nn.Parameter(torch.empty(num_tokens, embed_dims))
        nn.init.normal_(self.ste, std=0.02)

    def forward(self, tokens):
        if tokens.ndim != 3 or tokens.size(1) != self.ste.size(0):
            raise ValueError('CSI input must contain exactly 180 tokens')
        return self.projection(tokens) + self.ste.unsqueeze(0)


@DETECTORS.register_module()
class PETR2026Transfer(PETR):
    """Keep the original detector path while adding learnable CSI STE."""

    def __init__(self, *args, transfer_checkpoint, **kwargs):
        super().__init__(*args, **kwargs)
        self.head = _CSIProjectionWithSTE(self.head)
        self.transfer_checkpoint = transfer_checkpoint

    def init_weights(self):
        super().init_weights()
        migrate(self, self.transfer_checkpoint)

    def simple_test(self, img, img_metas, rescale=False):
        legacy = super().simple_test(img, img_metas, rescale=rescale)
        return [dict(legacy=legacy[0],
                     stages=self.bbox_head.last_eval_stages.detach().cpu().numpy())]


@TRANSFORMER_LAYER_SEQUENCE.register_module()
class PetrRefineTransformerDecoder2026Transfer(PetrRefineTransformerDecoder):
    """Keep an identity token in attention, regress only joint tokens."""

    def forward(self, query, *args, reference_points=None,
                reg_branches=None, **kwargs):
        if reference_points is None or query.size(0) != reference_points.size(1) + 1:
            raise ValueError('Refine expects one identity and 14 joint tokens')
        output = query
        intermediate = []
        intermediate_references = []
        for lid, layer in enumerate(self.layers):
            output = layer(output, *args, **kwargs)
            if reg_branches is not None:
                joint_states = output[1:].permute(1, 0, 2)
                offset = reg_branches[lid](joint_states)
                reference_points = (reference_points + offset).detach()
            if self.return_intermediate:
                intermediate.append(output)
                intermediate_references.append(reference_points)
        if self.return_intermediate:
            return (torch.stack(intermediate),
                    torch.stack(intermediate_references))
        return output, reference_points


@TRANSFORMER.register_module()
class PETRTransformer2026Transfer(PETRTransformer):
    """Generate person-specific joint queries from the pose hidden state."""

    def init_layers(self):
        super().init_layers()
        # The inherited shared refine query is retained only so its legacy
        # initializer remains valid; it is frozen and never used here.
        self.refine_query_embedding.weight.requires_grad_(False)
        self.joint_differentiators = nn.ModuleList([
            nn.Sequential(
                Linear(self.embed_dims, self.embed_dims),
                nn.LeakyReLU(negative_slope=0.01),
                Linear(self.embed_dims, self.embed_dims))
            for _ in range(self.num_keypoints)
        ])

    def init_weights(self):
        super().init_weights()
        for branch in self.joint_differentiators:
            for layer in branch:
                if isinstance(layer, nn.Linear):
                    nn.init.normal_(layer.weight, std=1e-3)
                    nn.init.normal_(layer.bias, std=1e-3)

    def make_joint_queries(self, identity_tokens):
        if identity_tokens.ndim != 2 or identity_tokens.size(1) != self.embed_dims:
            raise ValueError('Identity tokens must have shape (persons, 256)')
        return torch.stack([
            identity_tokens + branch(identity_tokens)
            for branch in self.joint_differentiators
        ], dim=1)

    def forward_refine(self, memory, reference_points_pose, img_inds,
                       identity_tokens, kpt_branches=None, **kwargs):
        count = reference_points_pose.size(0)
        if (identity_tokens.size(0) != count or
                reference_points_pose.size(1) != self.num_keypoints * 3):
            raise ValueError('Pose and identity selections are not aligned')
        joint_queries = self.make_joint_queries(identity_tokens)
        detached = joint_queries.detach()
        self.query_diagnostics = {
            'residual_rms': (detached - identity_tokens.detach()[:, None]).square().mean().sqrt(),
            'joint_spread_rms': (detached - detached.mean(1, keepdim=True)).square().mean().sqrt(),
            'person_spread_rms': (detached - detached.mean(0, keepdim=True)).square().mean().sqrt()}
        sequence = torch.cat((identity_tokens.unsqueeze(1), joint_queries),
                             dim=1).permute(1, 0, 2)
        references = reference_points_pose.reshape(count, self.num_keypoints, 3)
        person_memory = memory[:, img_inds, :]
        states, inter_references = self.refine_decoder(
            query=sequence,
            key=person_memory,
            value=person_memory,
            reference_points=references,
            reg_branches=kpt_branches,
            **kwargs)
        return states, references, inter_references


@HEADS.register_module()
class PETRHead2026Transfer(PETRHead):
    """Pass pose identity tokens through matching and score selection."""

    def forward(self, mlvl_feats, img_metas):
        query_embeds = self.query_embedding.weight
        (states, init_reference, inter_references, enc_cls, enc_kpts,
         memory) = self.transformer(
            mlvl_feats,
            query_embeds,
            kpt_branches=self.kpt_branches if self.with_kpt_refine else None,
            cls_branches=self.cls_branches if self.as_two_stage else None)
        states = states.permute(0, 2, 1, 3)
        identity_tokens = states[-1]
        classes = []
        keypoints = []
        for level in range(states.size(0)):
            reference = init_reference if level == 0 else inter_references[level - 1]
            classes.append(self.cls_branches[level](states[level]))
            keypoints.append(self.kpt_branches[level](states[level]) + reference)
        return (torch.stack(classes), torch.stack(keypoints), enc_cls,
                enc_kpts, memory, identity_tokens)

    def forward_train(self, x, img_metas, gt_bboxes, gt_labels=None,
                      gt_keypoints=None, gt_areas=None,
                      gt_bboxes_ignore=None, proposal_cfg=None, **kwargs):
        if proposal_cfg is not None:
            raise ValueError('proposal_cfg is not supported')
        classes, keypoints, enc_cls, enc_kpts, memory, identity = self(x, img_metas)
        if gt_labels is None:
            loss_inputs = (classes, keypoints, enc_cls, enc_kpts, gt_bboxes,
                           gt_keypoints, gt_areas, img_metas)
        else:
            loss_inputs = (classes, keypoints, enc_cls, enc_kpts, gt_bboxes,
                           gt_labels, gt_keypoints, gt_areas, img_metas)
        losses, refine_targets = self.loss(
            *loss_inputs, gt_bboxes_ignore=gt_bboxes_ignore)
        return self.forward_refine(memory, refine_targets, losses, identity)

    def forward_refine(self, memory, refine_targets, losses, identity_tokens):
        pose_preds, pose_targets, pose_weights = refine_targets
        selected = pose_weights.sum(dim=-1) > 0
        # Every DDP rank must participate, including a rank with no matched GT.
        normalizer = (torch.clamp(reduce_mean(pose_weights.sum()), min=1).item()
                      if self.training else None)
        if not selected.any():
            if self.training:
                zero = pose_preds.sum() * 0 + identity_tokens.sum() * 0
                for level in range(self.transformer.refine_decoder.num_layers):
                    losses[f'd{level}.loss_kpt_refine'] = zero
                return losses
            return pose_preds.reshape(1, 0, self.num_keypoints, 3)

        flat_identity = identity_tokens.reshape(-1, self.embed_dims)
        person_identity = flat_identity[selected]
        flat_indices = selected.nonzero(as_tuple=True)[0]
        image_indices = torch.div(flat_indices, self.num_query,
                                  rounding_mode='floor')
        selected_poses = pose_preds[selected]
        states, init_reference, inter_references = self.transformer.forward_refine(
            memory, selected_poses.detach(), image_indices, person_identity,
            kpt_branches=self.refine_kpt_branches)
        joint_states = states[:, 1:].permute(0, 2, 1, 3)
        outputs = []
        for level in range(joint_states.size(0)):
            reference = init_reference if level == 0 else inter_references[level - 1]
            outputs.append(reference + self.refine_kpt_branches[level](
                joint_states[level]))
        outputs = torch.stack(outputs)
        if not self.training:
            return outputs

        target = pose_targets[selected]
        weight = pose_weights[selected]
        for level, predicted in enumerate(outputs):
            losses[f'd{level}.loss_kpt_refine'] = self.loss_kpt_refine(
                predicted.reshape(predicted.size(0), -1), target, weight,
                avg_factor=normalizer)
        return losses

    @force_fp32(apply_to=('all_cls_scores', 'all_kpt_preds'))
    def get_bboxes(self, all_cls_scores, all_kpt_preds, enc_cls_scores,
                   enc_kpt_preds, memory, identity_tokens, img_metas,
                   rescale=False):
        if len(img_metas) != 1:
            raise ValueError('Inference supports batch size 1')
        return [self._get_bboxes_single(all_cls_scores[-1, 0],
                                        all_kpt_preds[-1, 0], memory,
                                        identity_tokens[0])]

    def _get_bboxes_single(self, cls_score, kpt_pred, memory,
                           identity_tokens):
        max_per_img = min(self.test_cfg.get('max_per_img', self.num_query),
                          cls_score.numel())
        if self.loss_cls.use_sigmoid:
            scores, ranked = cls_score.sigmoid().reshape(-1).topk(max_per_img)
            labels = ranked % self.num_classes
            pose_indices = ranked // self.num_classes
        else:
            scores, labels = F.softmax(cls_score, dim=-1)[..., :-1].max(-1)
            scores, pose_indices = scores.topk(max_per_img)
            labels = labels[pose_indices]
        selected_poses = kpt_pred[pose_indices]
        selected_identity = identity_tokens[pose_indices]
        refine_targets = (selected_poses, None, torch.ones_like(selected_poses))
        refined_stages = self.forward_refine(memory, refine_targets, None,
                                             selected_identity)
        refined = refined_stages[-1]
        self.last_eval_stages = torch.cat((selected_poses.reshape(1, -1, 14, 3),
                                          refined_stages), dim=0)
        x1 = refined[..., 0].min(dim=1, keepdim=True)[0]
        y1 = refined[..., 1].min(dim=1, keepdim=True)[0]
        x2 = refined[..., 0].max(dim=1, keepdim=True)[0]
        y2 = refined[..., 1].max(dim=1, keepdim=True)[0]
        boxes = torch.cat((x1, y1, x2, y2, scores.unsqueeze(1)), dim=1)
        return boxes, labels, refined
