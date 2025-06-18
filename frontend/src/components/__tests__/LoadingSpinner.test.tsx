import { render, screen } from '@testing-library/react';
import LoadingSpinner from '../Loading/LoadingSpinner';

describe('LoadingSpinner', () => {
  test('renders loading spinner', () => {
    render(<LoadingSpinner />);
    
    const progressElement = screen.getByRole('progressbar');
    expect(progressElement).toBeInTheDocument();
  });

  test('renders with message prop', () => {
    const message = 'Loading data...';
    render(<LoadingSpinner message={message} />);
    
    expect(screen.getByText(message)).toBeInTheDocument();
  });

  test('renders with size prop', () => {
    render(<LoadingSpinner size={60} />);
    
    const progressElement = screen.getByRole('progressbar');
    expect(progressElement).toBeInTheDocument();
  });

  test('renders default message when no message provided', () => {
    render(<LoadingSpinner />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });
});