import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Link,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  FilePresent as FileIcon,
  LibraryBooks as BooksIcon,
} from '@mui/icons-material';
import { booksApi } from '../../services/booksApi';

interface GoodreadsImportDialogProps {
  open: boolean;
  onClose: () => void;
  onImportComplete: () => void;
}

interface ImportResult {
  success: boolean;
  message: string;
  imported: number;
  skipped: number;
  errors: number;
  total: number;
}

const GoodreadsImportDialog: React.FC<GoodreadsImportDialogProps> = ({
  open,
  onClose,
  onImportComplete,
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);

  const steps = ['Instructions', 'Upload File', 'Import Complete'];

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.csv')) {
        setError('Please select a CSV file');
        return;
      }
      setSelectedFile(file);
      setError(null);
      setActiveStep(1);
    }
  };

  const handleImport = async () => {
    if (!selectedFile) return;

    setImporting(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('csv_file', selectedFile);

      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/v1/books/import/goodreads`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Import failed');
      }

      const data: ImportResult = await response.json();
      setResult(data);
      setActiveStep(2);
      
      if (data.imported > 0) {
        onImportComplete();
      }
    } catch (err: any) {
      setError(err.message || 'Failed to import books');
    } finally {
      setImporting(false);
    }
  };

  const handleClose = () => {
    setActiveStep(0);
    setSelectedFile(null);
    setError(null);
    setResult(null);
    onClose();
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <>
            <Typography variant="body1" paragraph>
              Follow these steps to export your Goodreads library:
            </Typography>
            
            <List>
              <ListItem>
                <ListItemIcon>
                  <InfoIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="1. Go to My Books on Goodreads"
                  secondary={
                    <Link href="https://www.goodreads.com/review/list" target="_blank" rel="noopener">
                      www.goodreads.com/review/list
                    </Link>
                  }
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <InfoIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="2. Click on Tools"
                  secondary="Find the Tools link at the top of your books list"
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <InfoIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="3. Click 'Import and Export'"
                  secondary="From the dropdown menu"
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <InfoIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="4. Click 'Export Library'"
                  secondary="This will download a CSV file to your computer"
                />
              </ListItem>
            </List>

            <Alert severity="info" sx={{ mt: 2 }}>
              The export includes all your books with reading status, ratings, and shelves.
              Duplicate books will be automatically skipped during import.
            </Alert>

            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <input
                accept=".csv"
                style={{ display: 'none' }}
                id="csv-file-input"
                type="file"
                onChange={handleFileSelect}
              />
              <label htmlFor="csv-file-input">
                <Button
                  variant="contained"
                  component="span"
                  startIcon={<UploadIcon />}
                  size="large"
                >
                  Select CSV File
                </Button>
              </label>
            </Box>
          </>
        );

      case 1:
        return (
          <Box sx={{ textAlign: 'center', py: 3 }}>
            {importing ? (
              <>
                <CircularProgress size={60} sx={{ mb: 3 }} />
                <Typography variant="h6" gutterBottom>
                  Importing your books...
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  This may take a moment depending on your library size
                </Typography>
              </>
            ) : (
              <>
                <Paper
                  variant="outlined"
                  sx={{
                    p: 3,
                    mb: 3,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 2,
                  }}
                >
                  <FileIcon color="primary" fontSize="large" />
                  <Box sx={{ textAlign: 'left', flex: 1 }}>
                    <Typography variant="subtitle1">
                      {selectedFile?.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {selectedFile && `${(selectedFile.size / 1024).toFixed(1)} KB`}
                    </Typography>
                  </Box>
                  <CheckIcon color="success" />
                </Paper>

                {error && (
                  <Alert severity="error" sx={{ mb: 3 }}>
                    {error}
                  </Alert>
                )}

                <Button
                  variant="contained"
                  size="large"
                  onClick={handleImport}
                  startIcon={<BooksIcon />}
                  disabled={importing}
                >
                  Import Books
                </Button>
              </>
            )}
          </Box>
        );

      case 2:
        return (
          <Box sx={{ textAlign: 'center', py: 3 }}>
            {result?.success ? (
              <>
                <CheckIcon sx={{ fontSize: 60, color: 'success.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom color="success.main">
                  Import Complete!
                </Typography>
              </>
            ) : (
              <>
                <ErrorIcon sx={{ fontSize: 60, color: 'error.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom color="error.main">
                  Import Failed
                </Typography>
              </>
            )}

            {result && (
              <Box sx={{ mt: 3, mb: 3 }}>
                <Typography variant="body1" paragraph>
                  {result.message}
                </Typography>
                
                <Box sx={{ display: 'flex', justifyContent: 'center', gap: 3, flexWrap: 'wrap' }}>
                  <Box>
                    <Typography variant="h4" color="primary">
                      {result.imported}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Books Imported
                    </Typography>
                  </Box>
                  
                  {result.skipped > 0 && (
                    <Box>
                      <Typography variant="h4" color="warning.main">
                        {result.skipped}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Duplicates Skipped
                      </Typography>
                    </Box>
                  )}
                  
                  {result.errors > 0 && (
                    <Box>
                      <Typography variant="h4" color="error.main">
                        {result.errors}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Errors
                      </Typography>
                    </Box>
                  )}
                </Box>
              </Box>
            )}
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      disableEscapeKeyDown={importing}
    >
      <DialogTitle>
        Import from Goodreads
      </DialogTitle>
      
      <Box sx={{ px: 3, pt: 2 }}>
        <Stepper activeStep={activeStep}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </Box>

      <DialogContent>
        {renderStepContent()}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={importing}>
          {activeStep === 2 ? 'Close' : 'Cancel'}
        </Button>
        
        {activeStep === 0 && selectedFile && (
          <Button
            variant="contained"
            onClick={() => setActiveStep(1)}
          >
            Next
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default GoodreadsImportDialog;