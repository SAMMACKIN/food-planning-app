import React from 'react';
import { Box, Typography, Chip } from '@mui/material';

interface RecipeInstructionsProps {
  instructions: string[];
  prepTime?: number;
  compact?: boolean;
}

const RecipeInstructions: React.FC<RecipeInstructionsProps> = ({ 
  instructions, 
  prepTime,
  compact = false
}) => {
  return (
    <Box sx={{ p: compact ? 1 : 2 }}>
      {instructions.map((instruction, index) => (
        <Box key={index} sx={{ 
          display: 'flex', 
          alignItems: 'flex-start', 
          mb: index < instructions.length - 1 ? (compact ? 2 : 3) : 0,
          position: 'relative'
        }}>
          {/* Step Number Circle */}
          <Box sx={{
            minWidth: compact ? 32 : 40,
            height: compact ? 32 : 40,
            borderRadius: '50%',
            backgroundColor: 'primary.main',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 'bold',
            fontSize: compact ? '0.9rem' : '1.1rem',
            mr: compact ? 1.5 : 2,
            mt: 0.5
          }}>
            {index + 1}
          </Box>
          
          {/* Connecting Line (except for last step) */}
          {index < instructions.length - 1 && (
            <Box sx={{
              position: 'absolute',
              left: compact ? 15 : 19,
              top: compact ? 32 : 40,
              bottom: compact ? -8 : -12,
              width: 2,
              backgroundColor: 'divider',
              zIndex: 0
            }} />
          )}
          
          {/* Instruction Content */}
          <Box sx={{ flex: 1, position: 'relative', zIndex: 1 }}>
            <Typography variant={compact ? "body2" : "body1"} sx={{ 
              fontWeight: 500,
              lineHeight: 1.6,
              fontSize: compact ? '0.9rem' : '1rem'
            }}>
              {instruction}
            </Typography>
            
            {/* Estimated time indicator for first/last steps */}
            {!compact && (index === 0 || index === instructions.length - 1) && (
              <Chip
                size="small"
                label={index === 0 ? "Start here" : "Final step"}
                color={index === 0 ? "success" : "primary"}
                variant="outlined"
                sx={{ mt: 1, fontSize: '0.75rem' }}
              />
            )}
          </Box>
        </Box>
      ))}
      
      {/* Completion Badge */}
      {!compact && (
        <Box sx={{ 
          mt: 3, 
          p: 2, 
          backgroundColor: 'success.50', 
          borderRadius: 2,
          border: '1px solid',
          borderColor: 'success.200',
          textAlign: 'center'
        }}>
          <Typography variant="body2" color="success.main" sx={{ fontWeight: 600 }}>
            🎉 Your delicious meal is ready to enjoy!
          </Typography>
          {prepTime && (
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
              Estimated total time: {prepTime} minutes
            </Typography>
          )}
        </Box>
      )}
    </Box>
  );
};

export default RecipeInstructions;