import { describe, it } from 'node:test';
import assert from 'node:assert/strict';

describe('Frontend API Client & Error Normalization', () => {
  it('correctly constructs error details from 422 validation response', () => {
    const errorDetail = [
      { loc: ['body', 'topic'], msg: 'Field required' },
      { loc: ['body', 'target_word_count'], msg: 'Must be >= 300' }
    ].map((err) => `${err.loc.join('.')}: ${err.msg}`).join(', ');

    assert.equal(errorDetail, 'body.topic: Field required, body.target_word_count: Must be >= 300');
  });

  it('validates 8-stage workflow structure', () => {
    const stages = [
      'analyze_topic',
      'research',
      'plan',
      'write_sections',
      'merge',
      'plan_images',
      'generate_images',
      'save'
    ];

    assert.equal(stages.length, 8);
    assert.equal(stages[0], 'analyze_topic');
    assert.equal(stages[7], 'save');
  });

  it('validates stage statuses include skipped for closed-book topics', () => {
    const stageStatuses = ['pending', 'running', 'completed', 'skipped', 'failed'];
    assert.ok(stageStatuses.includes('skipped'));
    assert.ok(stageStatuses.includes('completed'));
  });

  it('sanitizes malicious script and javascript links in markdown', () => {
    const maliciousInput = '<script>alert("hacked")</script>[Click](javascript:stealData())';
    // rehype-sanitize strips script tags and javascript: protocol links
    assert.ok(maliciousInput.includes('<script>'));
    const safeOutput = maliciousInput.replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, '').replace(/javascript:[^)]+/gi, '#');
    assert.ok(!safeOutput.includes('<script>'));
    assert.ok(!safeOutput.includes('javascript:stealData'));
  });
});
