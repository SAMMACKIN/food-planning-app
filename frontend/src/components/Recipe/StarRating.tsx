import React, { useState } from 'react';
import { Box, IconButton, Typography } from '@mui/material';
import { Star, StarBorder } from '@mui/icons-material';

interface StarRatingProps {
  rating: number;
  onChange?: (rating: number) => void;
  readOnly?: boolean;
  size?: 'small' | 'medium' | 'large';
  showValue?: boolean;
}

const StarRating: React.FC<StarRatingProps> = ({
  rating,
  onChange,
  readOnly = false,
  size = 'medium',
  showValue = false
}) => {
  const [hoverRating, setHoverRating] = useState(0);

  const handleClick = (newRating: number) => {
    if (!readOnly && onChange) {
      onChange(newRating);
    }
  };

  const handleMouseEnter = (newRating: number) => {
    if (!readOnly) {
      setHoverRating(newRating);
    }
  };

  const handleMouseLeave = () => {
    if (!readOnly) {
      setHoverRating(0);
    }
  };

  const getStarSize = () => {
    switch (size) {
      case 'small':
        return { fontSize: 16 };
      case 'large':
        return { fontSize: 32 };
      default:
        return { fontSize: 24 };
    }
  };

  const displayRating = hoverRating || rating;

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
      {[1, 2, 3, 4, 5].map((star) => (
        <IconButton
          key={star}
          size={size === 'small' ? 'small' : 'medium'}
          onClick={() => handleClick(star)}
          onMouseEnter={() => handleMouseEnter(star)}
          onMouseLeave={handleMouseLeave}
          disabled={readOnly}
          sx={{
            p: 0.25,
            color: star <= displayRating ? 'warning.main' : 'grey.300',
            cursor: readOnly ? 'default' : 'pointer',
            '&:hover': {
              backgroundColor: readOnly ? 'transparent' : 'action.hover',
            },
          }}
        >
          {star <= displayRating ? (
            <Star sx={getStarSize()} />
          ) : (
            <StarBorder sx={getStarSize()} />
          )}
        </IconButton>
      ))}
      {showValue && (
        <Typography variant="body2" sx={{ ml: 1 }}>
          {rating.toFixed(1)}
        </Typography>
      )}
    </Box>
  );
};

export default StarRating;