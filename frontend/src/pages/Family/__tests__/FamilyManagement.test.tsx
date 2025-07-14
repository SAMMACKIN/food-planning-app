import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import FamilyManagement from '../FamilyManagement';
import { apiRequest } from '../../../services/api';

// Mock the API service
jest.mock('../../../services/api', () => ({
  apiRequest: jest.fn(),
}));

const mockApiRequest = apiRequest as jest.MockedFunction<typeof apiRequest>;

// Mock window.confirm
const mockConfirm = jest.fn();
window.confirm = mockConfirm;

// Mock console methods
const consoleMock = {
  log: jest.fn(),
  error: jest.fn(),
};
Object.defineProperty(console, 'log', { value: consoleMock.log });
Object.defineProperty(console, 'error', { value: consoleMock.error });

// Mock data
const mockFamilyMembers = [
  {
    id: '1',
    user_id: 'user1',
    name: 'John Doe',
    age: 35,
    dietary_restrictions: ['Vegetarian', 'Gluten-Free'],
    preferences: {
      likes: ['pasta', 'pizza'],
      dislikes: ['fish', 'eggs'],
      preferred_cuisines: ['Italian', 'Mexican'],
      spice_level: 2
    },
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z'
  },
  {
    id: '2',
    user_id: 'user1',
    name: 'Jane Doe',
    age: 32,
    dietary_restrictions: [],
    preferences: {
      likes: ['salad', 'chicken'],
      dislikes: ['beef'],
      preferred_cuisines: ['Mediterranean', 'Thai'],
      spice_level: 3
    },
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z'
  }
];

describe('FamilyManagement', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockConfirm.mockReturnValue(true);
  });

  const renderFamilyManagement = () => {
    return render(<FamilyManagement />);
  };

  describe('Component Rendering', () => {
    test('should render the family management header', async () => {
      mockApiRequest.mockResolvedValue([]);
      renderFamilyManagement();

      expect(screen.getByText('Family Management')).toBeInTheDocument();
      expect(screen.getByText('Add Family Member')).toBeInTheDocument();
    });

    test('should display loading state initially', () => {
      mockApiRequest.mockImplementation(() => new Promise(() => {})); // Never resolves
      renderFamilyManagement();

      expect(screen.getByRole('button', { name: /add family member/i })).toBeDisabled();
    });

    test('should display empty state when no family members', async () => {
      mockApiRequest.mockResolvedValue([]);
      renderFamilyManagement();

      await waitFor(() => {
        expect(screen.getByText('No family members yet')).toBeInTheDocument();
        expect(screen.getByText('Add family members to start planning meals for everyone')).toBeInTheDocument();
        expect(screen.getByText('Add Your First Family Member')).toBeInTheDocument();
      });
    });

    test('should display family members', async () => {
      mockApiRequest.mockResolvedValue(mockFamilyMembers);
      renderFamilyManagement();

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
        expect(screen.getByText('Jane Doe')).toBeInTheDocument();
        expect(screen.getByText('Age: 35')).toBeInTheDocument();
        expect(screen.getByText('Age: 32')).toBeInTheDocument();
      });
    });

    test('should display dietary restrictions as chips', async () => {
      mockApiRequest.mockResolvedValue(mockFamilyMembers);
      renderFamilyManagement();

      await waitFor(() => {
        expect(screen.getByText('Vegetarian')).toBeInTheDocument();
        expect(screen.getByText('Gluten-Free')).toBeInTheDocument();
      });
    });

    test('should display food preferences', async () => {
      mockApiRequest.mockResolvedValue(mockFamilyMembers);
      renderFamilyManagement();

      await waitFor(() => {
        expect(screen.getByText('pasta')).toBeInTheDocument();
        expect(screen.getByText('pizza')).toBeInTheDocument();
        expect(screen.getByText('fish')).toBeInTheDocument();
        expect(screen.getByText('eggs')).toBeInTheDocument();
      });
    });

    test('should display preferred cuisines', async () => {
      mockApiRequest.mockResolvedValue(mockFamilyMembers);
      renderFamilyManagement();

      await waitFor(() => {
        expect(screen.getByText('Italian')).toBeInTheDocument();
        expect(screen.getByText('Mexican')).toBeInTheDocument();
        expect(screen.getByText('Mediterranean')).toBeInTheDocument();
        expect(screen.getByText('Thai')).toBeInTheDocument();
      });
    });
  });

  describe('Adding Family Members', () => {
    test('should open add dialog when Add Family Member button is clicked', async () => {
      mockApiRequest.mockResolvedValue([]);
      renderFamilyManagement();

      await waitFor(() => {
        fireEvent.click(screen.getByText('Add Family Member'));
      });

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Add Family Member', { selector: 'h2' })).toBeInTheDocument();
    });

    test('should submit new family member', async () => {
      const user = userEvent.setup();
      mockApiRequest.mockResolvedValueOnce([]);
      mockApiRequest.mockResolvedValueOnce(undefined); // POST response
      mockApiRequest.mockResolvedValueOnce([...mockFamilyMembers]); // Refresh response

      renderFamilyManagement();

      await waitFor(() => {
        fireEvent.click(screen.getByText('Add Family Member'));
      });

      const dialog = screen.getByRole('dialog');
      
      // Fill form
      await user.type(within(dialog).getByLabelText('Name'), 'New Member');
      await user.type(within(dialog).getByLabelText('Age (optional)'), '25');
      await user.type(within(dialog).getByLabelText('Foods they like (comma-separated)'), 'burgers, fries');
      await user.type(within(dialog).getByLabelText('Foods they dislike (comma-separated)'), 'mushrooms');

      // Submit
      fireEvent.click(within(dialog).getByText('Save'));

      await waitFor(() => {
        expect(mockApiRequest).toHaveBeenCalledWith(
          'POST',
          '/family/members',
          expect.objectContaining({
            name: 'New Member',
            age: 25,
            preferences: expect.objectContaining({
              likes: ['burgers', 'fries'],
              dislikes: ['mushrooms']
            })
          })
        );
      });
    });

    test('should validate required fields', async () => {
      const user = userEvent.setup();
      mockApiRequest.mockResolvedValue([]);
      renderFamilyManagement();

      await waitFor(() => {
        fireEvent.click(screen.getByText('Add Family Member'));
      });

      const dialog = screen.getByRole('dialog');
      
      // Try to submit without filling required fields
      fireEvent.click(within(dialog).getByText('Save'));

      await waitFor(() => {
        expect(screen.getByText('Name must be at least 2 characters')).toBeInTheDocument();
      });
    });

    test('should handle dietary restrictions selection', async () => {
      const user = userEvent.setup();
      mockApiRequest.mockResolvedValue([]);
      renderFamilyManagement();

      await waitFor(() => {
        fireEvent.click(screen.getByText('Add Family Member'));
      });

      const dialog = screen.getByRole('dialog');
      
      // Open dietary restrictions dropdown
      const dietarySelect = within(dialog).getByLabelText('Dietary Restrictions');
      fireEvent.mouseDown(dietarySelect);

      // Select options
      const listbox = within(document.body).getByRole('listbox');
      fireEvent.click(within(listbox).getByText('Vegetarian'));
      fireEvent.click(within(listbox).getByText('Dairy-Free'));

      // Close dropdown by clicking away
      fireEvent.click(dialog);

      // Verify selections are displayed
      expect(within(dialog).getByText('Vegetarian')).toBeInTheDocument();
      expect(within(dialog).getByText('Dairy-Free')).toBeInTheDocument();
    });

    test('should close dialog on cancel', async () => {
      mockApiRequest.mockResolvedValue([]);
      renderFamilyManagement();

      await waitFor(() => {
        fireEvent.click(screen.getByText('Add Family Member'));
      });

      const dialog = screen.getByRole('dialog');
      fireEvent.click(within(dialog).getByText('Cancel'));

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });
  });

  describe('Editing Family Members', () => {
    test('should open edit dialog with member data', async () => {
      mockApiRequest.mockResolvedValue(mockFamilyMembers);
      renderFamilyManagement();

      await waitFor(() => {
        const johnCard = screen.getByText('John Doe').closest('.MuiCard-root');
        const editButton = within(johnCard!).getAllByRole('button')[0]; // First button is edit
        fireEvent.click(editButton);
      });

      const dialog = screen.getByRole('dialog');
      expect(screen.getByText('Edit Family Member')).toBeInTheDocument();
      expect(within(dialog).getByDisplayValue('John Doe')).toBeInTheDocument();
      expect(within(dialog).getByDisplayValue('35')).toBeInTheDocument();
      expect(within(dialog).getByDisplayValue('pasta, pizza')).toBeInTheDocument();
      expect(within(dialog).getByDisplayValue('fish, eggs')).toBeInTheDocument();
    });

    test('should update family member', async () => {
      const user = userEvent.setup();
      mockApiRequest.mockResolvedValueOnce(mockFamilyMembers);
      mockApiRequest.mockResolvedValueOnce(undefined); // PUT response
      mockApiRequest.mockResolvedValueOnce(mockFamilyMembers); // Refresh response

      renderFamilyManagement();

      await waitFor(() => {
        const johnCard = screen.getByText('John Doe').closest('.MuiCard-root');
        const editButton = within(johnCard!).getAllByRole('button')[0];
        fireEvent.click(editButton);
      });

      const dialog = screen.getByRole('dialog');
      
      // Update age
      const ageInput = within(dialog).getByLabelText('Age (optional)');
      await user.clear(ageInput);
      await user.type(ageInput, '36');

      // Submit
      fireEvent.click(within(dialog).getByText('Save'));

      await waitFor(() => {
        expect(mockApiRequest).toHaveBeenCalledWith(
          'PUT',
          '/family/members/1',
          expect.objectContaining({
            name: 'John Doe',
            age: 36
          })
        );
      });
    });
  });

  describe('Deleting Family Members', () => {
    test('should show confirmation dialog before deleting', async () => {
      mockApiRequest.mockResolvedValue(mockFamilyMembers);
      renderFamilyManagement();

      await waitFor(() => {
        const johnCard = screen.getByText('John Doe').closest('.MuiCard-root');
        const deleteButton = within(johnCard!).getAllByRole('button')[1]; // Second button is delete
        fireEvent.click(deleteButton);
      });

      expect(mockConfirm).toHaveBeenCalledWith('Are you sure you want to delete this family member?');
    });

    test('should delete family member when confirmed', async () => {
      mockConfirm.mockReturnValue(true);
      mockApiRequest.mockResolvedValueOnce(mockFamilyMembers);
      mockApiRequest.mockResolvedValueOnce(undefined); // DELETE response
      mockApiRequest.mockResolvedValueOnce([mockFamilyMembers[1]]); // Refresh without John

      renderFamilyManagement();

      await waitFor(() => {
        const johnCard = screen.getByText('John Doe').closest('.MuiCard-root');
        const deleteButton = within(johnCard!).getAllByRole('button')[1];
        fireEvent.click(deleteButton);
      });

      await waitFor(() => {
        expect(mockApiRequest).toHaveBeenCalledWith('DELETE', '/family/members/1');
      });
    });

    test('should not delete when cancelled', async () => {
      mockConfirm.mockReturnValue(false);
      mockApiRequest.mockResolvedValue(mockFamilyMembers);
      renderFamilyManagement();

      await waitFor(() => {
        const johnCard = screen.getByText('John Doe').closest('.MuiCard-root');
        const deleteButton = within(johnCard!).getAllByRole('button')[1];
        fireEvent.click(deleteButton);
      });

      expect(mockApiRequest).not.toHaveBeenCalledWith('DELETE', expect.any(String));
    });
  });

  describe('Error Handling', () => {
    test('should display error when fetch fails', async () => {
      mockApiRequest.mockRejectedValue(new Error('Network error'));
      renderFamilyManagement();

      await waitFor(() => {
        expect(screen.getByText('Failed to fetch family members')).toBeInTheDocument();
      });
    });

    test('should display error when adding member fails', async () => {
      const user = userEvent.setup();
      mockApiRequest.mockResolvedValueOnce([]);
      mockApiRequest.mockRejectedValueOnce({
        response: { data: { detail: 'Name already exists' } }
      });

      renderFamilyManagement();

      await waitFor(() => {
        fireEvent.click(screen.getByText('Add Family Member'));
      });

      const dialog = screen.getByRole('dialog');
      await user.type(within(dialog).getByLabelText('Name'), 'John Doe');
      fireEvent.click(within(dialog).getByText('Save'));

      await waitFor(() => {
        expect(screen.getByText('Failed to add family member: Name already exists')).toBeInTheDocument();
      });
    });

    test('should display error when update fails', async () => {
      mockApiRequest.mockResolvedValueOnce(mockFamilyMembers);
      mockApiRequest.mockRejectedValueOnce(new Error('Update failed'));

      renderFamilyManagement();

      await waitFor(() => {
        const johnCard = screen.getByText('John Doe').closest('.MuiCard-root');
        const editButton = within(johnCard!).getAllByRole('button')[0];
        fireEvent.click(editButton);
      });

      const dialog = screen.getByRole('dialog');
      fireEvent.click(within(dialog).getByText('Save'));

      await waitFor(() => {
        expect(screen.getByText(/Failed to update family member/)).toBeInTheDocument();
      });
    });

    test('should display error when delete fails', async () => {
      mockApiRequest.mockResolvedValueOnce(mockFamilyMembers);
      mockApiRequest.mockRejectedValueOnce(new Error('Delete failed'));

      renderFamilyManagement();

      await waitFor(() => {
        const johnCard = screen.getByText('John Doe').closest('.MuiCard-root');
        const deleteButton = within(johnCard!).getAllByRole('button')[1];
        fireEvent.click(deleteButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Failed to delete family member')).toBeInTheDocument();
      });
    });
  });

  describe('Form Validation', () => {
    test('should validate age range', async () => {
      const user = userEvent.setup();
      mockApiRequest.mockResolvedValue([]);
      renderFamilyManagement();

      await waitFor(() => {
        fireEvent.click(screen.getByText('Add Family Member'));
      });

      const dialog = screen.getByRole('dialog');
      
      // Try negative age
      await user.type(within(dialog).getByLabelText('Name'), 'Test');
      await user.type(within(dialog).getByLabelText('Age (optional)'), '-5');
      fireEvent.click(within(dialog).getByText('Save'));

      await waitFor(() => {
        expect(screen.getByText('Age must be 0 or greater')).toBeInTheDocument();
      });

      // Clear and try too high age
      await user.clear(within(dialog).getByLabelText('Age (optional)'));
      await user.type(within(dialog).getByLabelText('Age (optional)'), '150');
      fireEvent.click(within(dialog).getByText('Save'));

      await waitFor(() => {
        expect(screen.getByText('Age must be 120 or less')).toBeInTheDocument();
      });
    });

    test('should validate name length', async () => {
      const user = userEvent.setup();
      mockApiRequest.mockResolvedValue([]);
      renderFamilyManagement();

      await waitFor(() => {
        fireEvent.click(screen.getByText('Add Family Member'));
      });

      const dialog = screen.getByRole('dialog');
      
      await user.type(within(dialog).getByLabelText('Name'), 'A');
      fireEvent.click(within(dialog).getByText('Save'));

      await waitFor(() => {
        expect(screen.getByText('Name must be at least 2 characters')).toBeInTheDocument();
      });
    });

    test('should allow optional age to be empty', async () => {
      const user = userEvent.setup();
      mockApiRequest.mockResolvedValueOnce([]);
      mockApiRequest.mockResolvedValueOnce(undefined);
      mockApiRequest.mockResolvedValueOnce([]);

      renderFamilyManagement();

      await waitFor(() => {
        fireEvent.click(screen.getByText('Add Family Member'));
      });

      const dialog = screen.getByRole('dialog');
      
      await user.type(within(dialog).getByLabelText('Name'), 'Test User');
      // Leave age empty
      fireEvent.click(within(dialog).getByText('Save'));

      await waitFor(() => {
        expect(mockApiRequest).toHaveBeenCalledWith(
          'POST',
          '/family/members',
          expect.objectContaining({
            name: 'Test User',
            age: undefined
          })
        );
      });
    });
  });

  describe('Loading States', () => {
    test('should disable buttons while loading', async () => {
      let resolveApiRequest: (value: any) => void;
      const apiPromise = new Promise(resolve => {
        resolveApiRequest = resolve;
      });
      mockApiRequest.mockReturnValue(apiPromise);

      renderFamilyManagement();

      expect(screen.getByRole('button', { name: /add family member/i })).toBeDisabled();

      // Resolve the promise
      resolveApiRequest!(mockFamilyMembers);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add family member/i })).toBeEnabled();
      });
    });

    test('should disable action buttons during operations', async () => {
      mockApiRequest.mockResolvedValueOnce(mockFamilyMembers);
      
      let resolveDelete: (value: any) => void;
      const deletePromise = new Promise(resolve => {
        resolveDelete = resolve;
      });
      mockApiRequest.mockReturnValueOnce(deletePromise);

      renderFamilyManagement();

      await waitFor(() => {
        const editButtons = screen.getAllByRole('button', { name: '' });
        const deleteButton = editButtons[3]; // Second member's delete button
        fireEvent.click(deleteButton);
      });

      // Check that buttons are disabled during operation
      const allButtons = screen.getAllByRole('button');
      allButtons.forEach(button => {
        if (button.textContent !== 'Cancel') {
          expect(button).toBeDisabled();
        }
      });

      // Resolve delete
      resolveDelete!(undefined);
    });
  });
});