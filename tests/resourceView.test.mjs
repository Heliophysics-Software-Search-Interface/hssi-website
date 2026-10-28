import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { runInNewContext } from 'node:vm';
import { transformSync } from 'esbuild';

const source = readFileSync(new URL('../frontend/resources/resourceView.ts', import.meta.url), 'utf8');
const { code } = transformSync(source, { loader: 'ts', format: 'cjs', target: 'es2022' });

// Exercise the real view methods with controllable network responses and a minimal DOM.
function createView() {
	const requests = [];
	const state = { loading: false, rendered: [], scrolls: 0, historyWrites: 0 };
	const location = { href: 'https://hssi.test/', search: '' };
	const element = () => ({
		style: {}, classList: { add() {}, remove() {} }, appendChild() {},
		scrollIntoView() { state.scrolls++; },
	});
	const context = {
		module: { exports: {} }, URL, URLSearchParams,
		window: { location },
		document: { createElement: element, querySelectorAll: () => [], getElementById: () => null },
		history: {
			pushState(_state, _title, value) {
				const url = new URL(value);
				location.href = url.href;
				location.search = url.search;
				state.historyWrites++;
			},
		},
		require: () => ({
			SimpleEvent: class { triggerEvent() {} },
			Spinner: {
				showSpinner() { state.loading = true; },
				hideSpinner() { state.loading = false; },
			},
			ModelDataCache: {
				fetchPage(_model, offset, _limit, sort) {
					return new Promise(resolve => requests.push({ offset, sort, resolve }));
				},
			},
		}),
	};
	runInNewContext(code, context);
	const view = new context.module.exports.ResourceView();
	view.paginatedMode = true;
	view.paginationTotal = 50;
	view.refreshItems = () => { state.rendered = view.itemData; };
	view.updatePaginationControls = () => {};
	return { view, requests, state, location };
}

function respond(request, name, total = 50) {
	request.resolve({ items: [{ software_name: name }], total });
}

test('a late response cannot overwrite the latest sort or its total', async () => {
	const { view, requests, state, location } = createView();
	const older = view.setSort('name');
	const latest = view.setSort('create');
	assert.deepEqual(requests.map(request => request.sort), ['name', 'create']);
	respond(requests[1], 'Newest publication');
	await latest;
	respond(requests[0], 'Alphabetical first', 75);
	await older;
	assert.equal(state.rendered[0].software_name, 'Newest publication');
	assert.equal(view.paginationTotal, 50);
	assert.equal(view.sort, 'create');
	assert.equal(location.search, '?sort=create');
	assert.equal(state.loading, false);
});

test('an older response arriving first leaves the latest request loading', async () => {
	const { view, requests, state } = createView();
	const older = view.setSort('name');
	const latest = view.setSort('create');
	respond(requests[0], 'Alphabetical first');
	await older;
	assert.equal(state.rendered.length, 0);
	assert.equal(state.loading, true);
	respond(requests[1], 'Newest publication');
	await latest;
	assert.equal(state.rendered[0].software_name, 'Newest publication');
	assert.equal(state.loading, false);
});

test('returning to an earlier sort still keeps only the latest response', async () => {
	const { view, requests, state } = createView();
	const first = view.setSort('name');
	const second = view.setSort('create');
	const latest = view.setSort('name');
	respond(requests[2], 'Latest name response');
	await latest;
	respond(requests[0], 'Stale name response');
	respond(requests[1], 'Stale create response');
	await Promise.all([first, second]);
	assert.equal(state.rendered[0].software_name, 'Latest name response');
});

test('a superseded page request cannot change history or scroll after a sort', async () => {
	const { view, requests, state, location } = createView();
	const olderPage = view.loadPage(25);
	const latestSort = view.setSort('name');
	respond(requests[1], 'Alphabetical first');
	await latestSort;
	respond(requests[0], 'Old second page');
	await olderPage;
	assert.equal(state.rendered[0].software_name, 'Alphabetical first');
	assert.equal(view.paginationOffset, 0);
	assert.equal(location.search, '?sort=name');
	assert.equal(state.historyWrites, 1);
	assert.equal(state.scrolls, 0);
});
