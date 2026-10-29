"""Resolve one input adapter before networking or SDK initialization.

The selected source is recorded per run. An unavailable dataset never falls
back to live collection. Older single-source packages keep their own default.
"""
from pathlib import Path


def select_input(root, identity, source=None, repetitions=None):
	source = source or identity.get('input_source')
	available = identity.get('input_sources', [identity.get('input_source')])
	if source not in ('live_csi', 'official_dataset') or source not in available:
		raise ValueError('Requested input is not included in this package')
	selected = dict(input_source=source)
	if source == 'official_dataset':
		from dataset_input import validate_dataset
		manifest = validate_dataset(root)
		passes = repetitions if repetitions is not None else identity.get('dataset_repetitions', 1)
		if type(passes) is not int or not 1 <= passes <= 30 or manifest['count'] * passes > 9000:
			raise ValueError('Dataset requires 1..30 passes and at most 9000 total inputs')
		selected.update(dataset_repetitions=passes, dataset_sha256=manifest['sha256'],
						split=manifest['split'], sequence=manifest['sequence'], count=manifest['count'])
	else:
		if repetitions is not None:
			raise ValueError('Dataset repetitions require official_dataset input')
		if not (Path(root)/'csi.conf').is_file():
			raise ValueError('Live CSI configuration is missing')
	return selected


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
