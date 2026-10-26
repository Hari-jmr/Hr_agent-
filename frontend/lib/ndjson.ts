/** Read complete NDJSON records regardless of how the network splits bytes. */
export async function* readNdjsonLines(stream: ReadableStream<Uint8Array>) {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let pending = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      pending += done ? decoder.decode() : decoder.decode(value, { stream: true });

      let newline;
      while ((newline = pending.indexOf('\n')) !== -1) {
        const line = pending.slice(0, newline).trim();
        pending = pending.slice(newline + 1);
        if (line) yield line;
      }

      if (done) {
        if (pending.trim()) yield pending.trim();
        break;
      }
    }
  } finally {
    reader.releaseLock();
  }
}
