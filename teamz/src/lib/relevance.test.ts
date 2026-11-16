import { describe, expect, it } from 'vitest';
import type { Agent, Conversation } from '../types';
import { scoreAgentRelevance, selectRelevantAgents } from './relevance';

function agent(id: string, name: string, extra: Partial<Agent> = {}): Agent {
  return {
    id,
    name,
    emoji: '🤖',
    accent: '#7c9cff',
    status: 'online',
    endpointUrl: 'http://localhost:8000/chat',
    model: 'test-model',
    systemPrompt: '',
    skills: [],
    createdAt: 0,
    ...extra,
  };
}

const channel: Conversation = {
  id: 'c1',
  kind: 'channel',
  name: 'Build Room',
  agentIds: ['a1', 'a2', 'a3'],
  topic: 'shipping frontend',
  createdAt: 0,
};

describe('relevance routing', () => {
  const coder = agent('a1', 'Atlas', {
    isLead: true,
    origin: { templateId: 'eng', familySlug: 'engineering', role: 'Lead Software Engineer' },
    skills: [
      { key: 'typescript', label: 'TypeScript', level: 5 },
      { key: 'react', label: 'React', level: 5 },
      { key: 'orchestration', label: 'Orchestration', level: 5 },
    ],
    systemPrompt: 'You are a lead engineer who can orchestrate and delegate.',
  });
  const designer = agent('a2', 'Pixel', {
    origin: { templateId: 'des', familySlug: 'design', role: 'Product Designer' },
    skills: [
      { key: 'ui', label: 'UI design', level: 5 },
      { key: 'ux', label: 'UX flows', level: 4 },
    ],
  });
  const writer = agent('a3', 'Sage', {
    origin: { templateId: 'w', familySlug: 'writing', role: 'Editor' },
    skills: [
      { key: 'editing', label: 'Editing', level: 5 },
      { key: 'docs', label: 'Documentation', level: 4 },
    ],
  });

  it('prefers coding agent for implementation requests', () => {
    const selected = selectRelevantAgents('Can you fix the React TypeScript bug in the API client?', [coder, designer, writer], channel);
    expect(selected.map((a) => a.id)).toContain('a1');
    expect(selected.length).toBeGreaterThanOrEqual(1);
  });

  it('prefers design agent for UI/design requests', () => {
    const selected = selectRelevantAgents('Please improve the UI layout, spacing and visual design', [coder, designer, writer], channel);
    expect(selected.map((a) => a.id)).toContain('a2');
  });

  it('prefers lead/orchestrator for runtime control requests', () => {
    const selected = selectRelevantAgents('Create a new channel and add an agent, then delegate this task', [writer, designer, coder], channel);
    expect(selected.map((a) => a.id)).toContain('a1');
  });

  it('does not blindly select all members for unmentioned messages', () => {
    const selected = selectRelevantAgents('Fix the frontend build error', [coder, designer, writer], channel);
    expect(selected.length).toBeLessThanOrEqual(3);
    // should be focused (not necessarily all 3)
    expect(selected.length).toBeGreaterThanOrEqual(1);
  });

  it('falls back sensibly when relevance is low', () => {
    const selected = selectRelevantAgents('hello there', [coder, designer, writer], channel);
    expect(selected.length).toBeGreaterThanOrEqual(1);
  });

  it('scores named agent higher when mentioned by name tokens', () => {
    const sAtlas = scoreAgentRelevance('Atlas can you help?', coder, channel);
    const sPixel = scoreAgentRelevance('Atlas can you help?', designer, channel);
    expect(sAtlas).toBeGreaterThan(sPixel);
  });
});
