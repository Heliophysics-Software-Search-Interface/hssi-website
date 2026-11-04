import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { runInNewContext } from 'node:vm';
import { transformSync } from 'esbuild';

const source = readFileSync(new URL('../frontend/simpleEvent.ts', import.meta.url), 'utf8');
const { code } = transformSync(source, { loader: 'ts', format: 'cjs', target: 'es2022' });

function createEvent() {
	const context = { module: { exports: {} } };
	runInNewContext(code, context);
	return new context.module.exports.SimpleEvent();
}

// A homepage load with ?q= has the filter menu and the search both waiting on ResourceView.onReady (#167).
test('one trigger resolves every pending wait()', async () => {
	const event = createEvent();
	const resolved = [];
	event.wait().then(() => resolved.push('filter menu'));
	event.wait().then(() => resolved.push('search'));
	event.triggerEvent();
	await new Promise(resolve => setImmediate(resolve));
	assert.deepEqual(resolved, ['filter menu', 'search']);
	assert.equal(event.listeners.length, 0);
});

test('a listener that removes itself does not skip the next listener', () => {
	const event = createEvent();
	const calls = [];
	const once = event.addListener(() => {
		calls.push('once');
		event.removeListener(once);
	});
	event.addListener(() => calls.push('always'));
	event.triggerEvent();
	event.triggerEvent();
	assert.deepEqual(calls, ['once', 'always', 'always']);
});
