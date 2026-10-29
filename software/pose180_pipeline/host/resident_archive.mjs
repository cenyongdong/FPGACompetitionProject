import {parentPort, workerData} from 'node:worker_threads';
import fs from 'node:fs/promises';
import path from 'node:path';
let file, segment = 0, records = 64, retryAt = 0;
parentPort.on('message', async bytes => {
	try {
		if (Date.now() < retryAt)
			throw new Error('Archive recovery backoff');
		if (!file || records >= 64) {
			await file?.close();
			file = undefined;
			file = await fs.open(path.join(workerData, `recent-${segment}.full`), 'w');
			segment = (segment + 1) % 4;
			records = 0;
		}
		let offset = 0;
		while (offset < bytes.length) {
			const {bytesWritten} = await file.write(bytes, offset, bytes.length - offset);
			if (!bytesWritten)
				throw new Error('Archive made no progress');
			offset += bytesWritten;
		}
		++records;
		parentPort.postMessage({ok : true});
	} catch (error) {
		retryAt = Date.now() + 5000;
		await file?.close().catch(() => {
								  });
		file = undefined;
		parentPort.postMessage({ok : false, error : error.message});
	}
});
