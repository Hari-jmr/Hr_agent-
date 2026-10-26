import assert from 'node:assert/strict';
import test from 'node:test';
import { readNdjsonLines } from '../../frontend/lib/ndjson.ts';

const encoder = new TextEncoder();

async function readEvents(parts) {
  const stream = new ReadableStream({
    start(controller) {
      for (const part of parts) controller.enqueue(part);
      controller.close();
    },
  });
  const events = [];
  for await (const line of readNdjsonLines(stream)) events.push(JSON.parse(line));
  assert.equal(stream.locked, false);
  return events;
}

test('preserves citation metadata and answer text split across network packets', async () => {
  const events = [
    { type: 'start', citations: [{ document_name: 'Employee Handbook.pdf', page_number: 21 }] },
    { type: 'chunk', content: 'Employee’s leave policy [Source 1]' },
    { type: 'end' },
  ];
  const bytes = encoder.encode(events.map(JSON.stringify).join('\n') + '\n');
  // One byte per packet also splits the multibyte apostrophe in the answer.
  assert.deepEqual(await readEvents(Array.from(bytes, (byte) => Uint8Array.of(byte))), events);
});

test('reads combined records, blank lines and a final event without a newline', async () => {
  const text = '\r\n{"type":"start","citations":[]}\r\n\n{"type":"end"}';
  assert.deepEqual(await readEvents([encoder.encode(text)]), [
    { type: 'start', citations: [] },
    { type: 'end' },
  ]);
});
