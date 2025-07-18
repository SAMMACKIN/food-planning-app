import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Alert,
  CircularProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  FormControlLabel,
  Checkbox,
  Link,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Movie as MovieIcon,
  Tv as TvIcon,
  GetApp as DownloadIcon,
  OpenInNew as OpenInNewIcon,
} from '@mui/icons-material';

interface NetflixImportDialogProps {
  open: boolean;
  onClose: () => void;
  onImportComplete: () => void;
}

const NetflixImportDialog: React.FC<NetflixImportDialogProps> = ({
  open,
  onClose,
  onImportComplete,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const [file, setFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);
  const [importMovies, setImportMovies] = useState(true);
  const [importTvShows, setImportTvShows] = useState(true);
  const [activeStep, setActiveStep] = useState(0);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        setError('Please select a CSV file');
        return;
      }
      setFile(selectedFile);
      setError(null);
      setActiveStep(1);
    }
  };

  const handleImport = async () => {
    if (!file) return;

    setImporting(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const queryParams = new URLSearchParams({
        import_movies: importMovies.toString(),
        import_tv_shows: importTvShows.toString(),
      });

      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/api/v1/movies/import/netflix?${queryParams}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
          body: formData,
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Import failed');
      }

      const result = await response.json();
      setImportResult(result);
      setSuccess(true);
      setActiveStep(2);
      
      if (result.success) {
        setTimeout(() => {
          onImportComplete();
          handleClose();
        }, 3000);
      }
    } catch (err: any) {
      console.error('Import error:', err);
      setError(err.message || 'Failed to import Netflix history');
    } finally {
      setImporting(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setError(null);
    setSuccess(false);
    setImportResult(null);
    setActiveStep(0);
    onClose();
  };

  const steps = [
    {
      label: 'Get your Netflix data',
      content: (
        <Box>
          <Typography variant="body2" paragraph>
            Follow these steps to download your Netflix viewing history:
          </Typography>
          <List dense>
            <ListItem>
              <ListItemText 
                primary="1. Go to Netflix.com and sign in"
                secondary={
                  <Link href="https://www.netflix.com" target="_blank" rel="noopener">
                    Open Netflix <OpenInNewIcon sx={{ fontSize: 14, ml: 0.5 }} />
                  </Link>
                }
              />
            </ListItem>
            <ListItem>
              <ListItemText primary="2. Click on your profile icon → Account" />
            </ListItem>
            <ListItem>
              <ListItemText primary="3. Under 'Profile & Parental Controls', select your profile" />
            </ListItem>
            <ListItem>
              <ListItemText primary="4. Click 'Viewing activity'" />
            </ListItem>
            <ListItem>
              <ListItemText primary="5. Scroll to the bottom and click 'Download all'" />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <DownloadIcon color="primary" />
              </ListItemIcon>
              <ListItemText 
                primary="6. Save the CSV file to your computer"
                secondary="The file will be named something like 'ViewingActivity.csv'"
              />
            </ListItem>
          </List>
        </Box>
      ),
    },
    {
      label: 'Upload and configure',
      content: (
        <Box>
          <Box sx={{ mb: 3 }}>
            <input
              accept=".csv"
              style={{ display: 'none' }}
              id="netflix-csv-upload"
              type="file"
              onChange={handleFileChange}
            />
            <label htmlFor="netflix-csv-upload">
              <Button
                variant="contained"
                component="span"
                startIcon={<UploadIcon />}
                fullWidth
              >
                {file ? 'Change File' : 'Select Netflix CSV File'}
              </Button>
            </label>
            
            {file && (
              <Typography variant="body2" sx={{ mt: 1, color: 'success.main' }}>
                ✅ Selected: {file.name}
              </Typography>
            )}
          </Box>

          <Typography variant="body2" color="text.secondary" paragraph>
            Choose what to import:
          </Typography>
          
          <Box sx={{ mb: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={importMovies}
                  onChange={(e) => setImportMovies(e.target.checked)}
                  disabled={importing}
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <MovieIcon />
                  <span>Import Movies</span>
                </Box>
              }
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={importTvShows}
                  onChange={(e) => setImportTvShows(e.target.checked)}
                  disabled={importing}
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TvIcon />
                  <span>Import TV Shows</span>
                </Box>
              }
            />
          </Box>
          
          <Alert severity="info" sx={{ mt: 2 }}>
            For TV shows, we'll create one entry per show (not per episode) to avoid clutter.
          </Alert>
        </Box>
      ),
    },
    {
      label: 'Import complete',
      content: (
        <Box sx={{ textAlign: 'center', py: 2 }}>
          {success && importResult ? (
            <>
              <CheckIcon sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Import Successful!
              </Typography>
              <Box sx={{ mt: 2, textAlign: 'left' }}>
                <Typography variant="body2">
                  • Movies imported: {importResult.movies_imported}
                </Typography>
                <Typography variant="body2">
                  • Movies skipped (duplicates): {importResult.movies_skipped}
                </Typography>
                <Typography variant="body2">
                  • TV shows imported: {importResult.tv_shows_imported}
                </Typography>
                <Typography variant="body2">
                  • TV shows skipped (duplicates): {importResult.tv_shows_skipped}
                </Typography>
                {importResult.errors > 0 && (
                  <Typography variant="body2" color="error">
                    • Errors: {importResult.errors}
                  </Typography>
                )}
              </Box>
            </>
          ) : (
            <>
              <ErrorIcon sx={{ fontSize: 64, color: 'error.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Import Failed
              </Typography>
              <Typography variant="body2" color="error">
                {error || 'An error occurred during import'}
              </Typography>
            </>
          )}
        </Box>
      ),
    },
  ];

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      fullScreen={isMobile}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <img 
            src="https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg" 
            alt="Netflix" 
            style={{ height: 24 }}
          />
          Import Netflix Viewing History
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {error && activeStep !== 2 && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Stepper activeStep={activeStep} orientation="vertical">
          {steps.map((step, index) => (
            <Step key={step.label}>
              <StepLabel
                optional={
                  index === 2 ? (
                    <Typography variant="caption">Last step</Typography>
                  ) : null
                }
              >
                {step.label}
              </StepLabel>
              <StepContent>
                {step.content}
                <Box sx={{ mb: 2, mt: 2 }}>
                  {index === 0 && (
                    <Button
                      variant="contained"
                      onClick={() => setActiveStep(1)}
                      sx={{ mt: 1, mr: 1 }}
                    >
                      I have my CSV file
                    </Button>
                  )}
                  {index === 1 && (
                    <>
                      <Button
                        variant="contained"
                        onClick={handleImport}
                        disabled={!file || importing || (!importMovies && !importTvShows)}
                        sx={{ mt: 1, mr: 1 }}
                        startIcon={importing ? <CircularProgress size={20} /> : null}
                      >
                        {importing ? 'Importing...' : 'Import'}
                      </Button>
                      <Button
                        disabled={importing}
                        onClick={() => setActiveStep(0)}
                        sx={{ mt: 1, mr: 1 }}
                      >
                        Back
                      </Button>
                    </>
                  )}
                </Box>
              </StepContent>
            </Step>
          ))}
        </Stepper>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose} disabled={importing}>
          {success ? 'Close' : 'Cancel'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default NetflixImportDialog;