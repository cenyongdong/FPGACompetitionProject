"""Explicit package input selection; defaults cannot silently enable live CSI."""
from pathlib import Path


def input_arguments(root, identity):
    source = identity.get('input_source')
    if source == 'official_dataset':
        if not (Path(root)/'dataset.piwcsi2').is_file():
            raise ValueError('Prepared dataset is missing')
        return ['--dataset', str(Path(root)/'dataset.piwcsi2'), '--input-port', '0',
                '--dataset-repetitions', str(identity.get('dataset_repetitions',1))]
    if source == 'live_csi':
        return ['--csi', str(Path(root)/'csi.conf'), '--input-port', '0']
    raise ValueError('New package must explicitly select official_dataset or live_csi')
