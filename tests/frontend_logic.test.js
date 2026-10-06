const test = require('node:test');
const assert = require('node:assert');

const EDInsight = require('../web/app.js');

const severityLabels = ['Minor', 'Moderate', 'Serious', 'Critical'];
const esiLabels = ['Immediate (ESI-1)', 'High risk (ESI-2)', 'Urgent (ESI-3)', 'Less urgent (ESI-4)', 'Non-urgent (ESI-5)'];

test('toDisplayScore maps zero-based indices to one-based scale', () => {
    assert.strictEqual(EDInsight.toDisplayScore(0), 1);
    assert.strictEqual(EDInsight.toDisplayScore(4), 5);
    assert.strictEqual(EDInsight.toDisplayScore(1.8504), 2.8504);
});

test('labelForScore maps display scores to the nearest label', () => {
    assert.strictEqual(EDInsight.labelForScore(1.1, esiLabels, 'Unknown'), 'Immediate (ESI-1)');
    assert.strictEqual(EDInsight.labelForScore(2.8504, esiLabels, 'Unknown'), 'Urgent (ESI-3)');
    assert.strictEqual(EDInsight.labelForScore(5.0, esiLabels, 'Unknown'), 'Non-urgent (ESI-5)');
});

test('labelForScore returns fallback outside the scale', () => {
    assert.strictEqual(EDInsight.labelForScore(0.4, esiLabels, 'Unknown'), 'Unknown');
    assert.strictEqual(EDInsight.labelForScore(6.2, esiLabels, 'Unknown'), 'Unknown');
});

test('severity labels match the weighted-average score', () => {
    assert.strictEqual(EDInsight.labelForScore(EDInsight.toDisplayScore(2.5954), severityLabels, 'Unknown'), 'Critical');
    assert.strictEqual(EDInsight.labelForScore(EDInsight.toDisplayScore(0.1), severityLabels, 'Unknown'), 'Minor');
    assert.strictEqual(EDInsight.labelForScore(EDInsight.toDisplayScore(3.2), severityLabels, 'Unknown'), 'Critical');
});

test('verdictClassForPriority uses urgency thresholds', () => {
    assert.strictEqual(EDInsight.verdictClassForPriority(1.1), 'priority-high');
    assert.strictEqual(EDInsight.verdictClassForPriority(2.0), 'priority-high');
    assert.strictEqual(EDInsight.verdictClassForPriority(2.5), 'priority-medium');
    assert.strictEqual(EDInsight.verdictClassForPriority(3.0), 'priority-medium');
    assert.strictEqual(EDInsight.verdictClassForPriority(3.9), 'priority-low');
    assert.strictEqual(EDInsight.verdictClassForPriority(5.0), 'priority-low');
});

test('dischargeVerdict splits at the midpoint', () => {
    assert.strictEqual(EDInsight.dischargeVerdict(0.6), 'yes');
    assert.strictEqual(EDInsight.dischargeVerdict(0.5), 'no');
    assert.strictEqual(EDInsight.dischargeVerdict(0.0118), 'no');
});

test('noulConfidence is zero at the midpoint and one at the extremes', () => {
    assert.strictEqual(EDInsight.noulConfidence(0.5), 0);
    assert.strictEqual(EDInsight.noulConfidence(0), 1);
    assert.strictEqual(EDInsight.noulConfidence(1), 1);
    assert.ok(Math.abs(EDInsight.noulConfidence(0.0118) - 0.9764) < 0.001);
});
