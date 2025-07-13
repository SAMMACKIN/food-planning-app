import React from 'react';
import { Box, IconButton } from '@mui/material';
import { Star, StarBorder } from '@mui/icons-material';

interface StarRatingProps {
  rating: number;
  onRatingChange?: (rating: number) => void;
  size?: 'small' | 'medium' | 'large';
  readOnly?: boolean;
  showZero?: boolean;
}

const StarRating: React.FC<StarRatingProps> = ({
  rating,
  onRatingChange,
  size = 'medium',
  readOnly = false,
  showZero = true
}) => {
  const handleStarClick = (starValue: number) => {
    if (!readOnly && onRatingChange) {
      // If clicking the same star that's already selected, toggle to 0 if showZero is true
      if (starValue === rating && showZero) {
        onRatingChange(0);
      } else {
        onRatingChange(starValue);
      }
    }
  };

  const getStarSize = () => {
    switch (size) {
      case 'small':
        return { fontSize: '1rem' };
      case 'large':
        return { fontSize: '2rem' };
      default:
        return { fontSize: '1.5rem' };
    }
  };

  const getIconButtonSize = () => {
    switch (size) {
      case 'small':
        return 'small' as const;
      case 'large':
        return 'large' as const;
      default:
        return 'medium' as const;
    }
  };

  return (
    <Box display="flex" alignItems="center">
      {[1, 2, 3, 4, 5].map((star) => {
        const isFilled = star <= rating;
        
        if (readOnly) {
          return (
            <Box key={star} sx={{ ...getStarSize(), color: isFilled ? '#ffd700' : '#e0e0e0' }}>
              {isFilled ? <Star sx={getStarSize()} /> : <StarBorder sx={getStarSize()} />}
            </Box>
          );
        }

        return (
          <IconButton
            key={star}
            size={getIconButtonSize()}
            onClick={() => handleStarClick(star)}
            sx={{
              color: isFilled ? '#ffd700' : '#e0e0e0',
              padding: size === 'small' ? '2px' : '4px',
              '&:hover': {
                color: '#ffd700',
                backgroundColor: 'rgba(255, 215, 0, 0.1)'
              }
            }}
          >
            {isFilled ? <Star sx={getStarSize()} /> : <StarBorder sx={getStarSize()} />}
          </IconButton>
        );
      })}
    </Box>
  );
};

export default StarRating;