import { jest } from '@jest/globals';

// Mock OpenAI API
export const mockOpenAI = {
  createCompletion: jest.fn(),
  createChatCompletion: jest.fn()
};

// Mock Ghost CMS API
export const mockGhostAPI = {
  posts: {
    add: jest.fn(),
    edit: jest.fn()
  }
};

// Mock Database
export const mockDB = {
  query: jest.fn(),
  connect: jest.fn(),
  disconnect: jest.fn()
};

// Reset all mocks
export const resetMocks = () => {
  mockOpenAI.createCompletion.mockReset();
  mockOpenAI.createChatCompletion.mockReset();
  mockGhostAPI.posts.add.mockReset();
  mockGhostAPI.posts.edit.mockReset();
  mockDB.query.mockReset();
  mockDB.connect.mockReset();
  mockDB.disconnect.mockReset();
};
