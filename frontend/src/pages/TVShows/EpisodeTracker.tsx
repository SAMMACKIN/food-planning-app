import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Tabs,
  Tab,
  Checkbox,
  IconButton,
  LinearProgress,
  Alert,
  CircularProgress,
  Chip,
  Stack,
  Tooltip,
  FormControlLabel,
  Divider,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  CheckCircle as CheckCircleIcon,
  RadioButtonUnchecked as UncheckedIcon,
  DoneAll as DoneAllIcon,
  RemoveDone as RemoveDoneIcon,
  PlayArrow as PlayIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { TVShow, EpisodeWatch } from '../../types';
import { tvShowsApi, tvShowHelpers } from '../../services/tvShowsApi';

interface EpisodeTrackerProps {
  open: boolean;
  tvShow: TVShow;
  onClose: () => void;
}

interface SeasonEpisodes {
  [season: number]: {
    total: number;
    watched: Set<number>;
  };
}

const EpisodeTracker: React.FC<EpisodeTrackerProps> = ({ open, tvShow, onClose }) => {
  const [selectedSeason, setSelectedSeason] = useState(tvShow.current_season || 1);
  const [watchedEpisodes, setWatchedEpisodes] = useState<EpisodeWatch[]>([]);
  const [seasonData, setSeasonData] = useState<SeasonEpisodes>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load watched episodes
  const loadWatchedEpisodes = async () => {
    try {
      setLoading(true);
      setError(null);
      const episodes = await tvShowsApi.getWatchedEpisodes(tvShow.id);
      setWatchedEpisodes(episodes);
      
      // Build season data structure
      const data: SeasonEpisodes = {};
      const totalSeasons = tvShow.total_seasons || 5; // Default to 5 if not specified
      
      for (let s = 1; s <= totalSeasons; s++) {
        data[s] = {
          total: 20, // Default episodes per season
          watched: new Set(),
        };
      }
      
      // Mark watched episodes
      episodes.forEach((ep) => {
        if (ep.watched && data[ep.season_number]) {
          data[ep.season_number].watched.add(ep.episode_number);
        }
      });
      
      setSeasonData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load episodes');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open) {
      loadWatchedEpisodes();
    }
  }, [open]);

  const isEpisodeWatched = (season: number, episode: number): boolean => {
    return seasonData[season]?.watched.has(episode) || false;
  };

  const handleToggleEpisode = async (season: number, episode: number) => {
    try {
      setSaving(true);
      setError(null);
      
      const isWatched = isEpisodeWatched(season, episode);
      
      await tvShowsApi.markEpisodeWatched(tvShow.id, {
        season_number: season,
        episode_number: episode,
        watched: !isWatched,
      });
      
      // Update local state
      setSeasonData((prev) => {
        const newData = { ...prev };
        if (!newData[season]) {
          newData[season] = { total: 20, watched: new Set() };
        }
        
        if (isWatched) {
          newData[season].watched.delete(episode);
        } else {
          newData[season].watched.add(episode);
        }
        
        return newData;
      });
    } catch (err: any) {
      setError(err.message || 'Failed to update episode');
    } finally {
      setSaving(false);
    }
  };

  const handleMarkSeasonWatched = async (season: number, watched: boolean) => {
    try {
      setSaving(true);
      setError(null);
      
      const episodeCount = seasonData[season]?.total || 20;
      const episodes = Array.from({ length: episodeCount }, (_, i) => i + 1);
      
      await tvShowsApi.bulkMarkEpisodes(tvShow.id, season, episodes, watched);
      
      // Update local state
      setSeasonData((prev) => {
        const newData = { ...prev };
        if (!newData[season]) {
          newData[season] = { total: episodeCount, watched: new Set() };
        }
        
        if (watched) {
          newData[season].watched = new Set(episodes);
        } else {
          newData[season].watched = new Set();
        }
        
        return newData;
      });
    } catch (err: any) {
      setError(err.message || 'Failed to update season');
    } finally {
      setSaving(false);
    }
  };

  const getSeasonProgress = (season: number): number => {
    const data = seasonData[season];
    if (!data || data.total === 0) return 0;
    return (data.watched.size / data.total) * 100;
  };

  const getTotalProgress = (): number => {
    let totalEpisodes = 0;
    let watchedCount = 0;
    
    Object.values(seasonData).forEach((data) => {
      totalEpisodes += data.total;
      watchedCount += data.watched.size;
    });
    
    return totalEpisodes > 0 ? (watchedCount / totalEpisodes) * 100 : 0;
  };

  const renderSeasonTab = (season: number) => {
    const progress = getSeasonProgress(season);
    const data = seasonData[season];
    const episodeCount = data?.total || 20;
    
    return (
      <Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            Season {season} Progress
          </Typography>
          <Stack direction="row" spacing={1}>
            <Chip
              label={`${data?.watched.size || 0}/${episodeCount} episodes`}
              color={progress === 100 ? 'success' : 'default'}
            />
            {progress === 100 ? (
              <Button
                size="small"
                startIcon={<RemoveDoneIcon />}
                onClick={() => handleMarkSeasonWatched(season, false)}
                disabled={saving}
              >
                Unmark All
              </Button>
            ) : (
              <Button
                size="small"
                startIcon={<DoneAllIcon />}
                onClick={() => handleMarkSeasonWatched(season, true)}
                disabled={saving}
              >
                Mark All Watched
              </Button>
            )}
          </Stack>
        </Box>
        
        <LinearProgress
          variant="determinate"
          value={progress}
          sx={{ mb: 3, height: 8, borderRadius: 1 }}
        />
        
        <Grid container spacing={1}>
          {Array.from({ length: episodeCount }, (_, i) => i + 1).map((episode) => {
            const isWatched = isEpisodeWatched(season, episode);
            const isCurrentEpisode = season === tvShow.current_season && episode === tvShow.current_episode;
            
            return (
              <Grid item xs={4} sm={3} md={2} key={episode}>
                <Tooltip
                  title={
                    isCurrentEpisode
                      ? 'Current Episode'
                      : isWatched
                      ? 'Watched'
                      : 'Not Watched'
                  }
                >
                  <Box
                    sx={{
                      position: 'relative',
                      aspectRatio: '1',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      bgcolor: isWatched ? 'success.main' : 'action.hover',
                      borderRadius: 2,
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      border: isCurrentEpisode ? '3px solid' : 'none',
                      borderColor: 'primary.main',
                      '&:hover': {
                        transform: 'scale(1.05)',
                        boxShadow: 2,
                      },
                    }}
                    onClick={() => handleToggleEpisode(season, episode)}
                  >
                    <Typography
                      variant="h6"
                      color={isWatched ? 'success.contrastText' : 'text.primary'}
                    >
                      {episode}
                    </Typography>
                    {isCurrentEpisode && (
                      <PlayIcon
                        sx={{
                          position: 'absolute',
                          top: 4,
                          right: 4,
                          fontSize: 16,
                          color: 'primary.main',
                        }}
                      />
                    )}
                  </Box>
                </Tooltip>
              </Grid>
            );
          })}
        </Grid>
      </Box>
    );
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h5">
            Track Episodes - {tvShow.title}
          </Typography>
          <IconButton onClick={loadWatchedEpisodes} disabled={loading}>
            <RefreshIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            <Box sx={{ mb: 3 }}>
              <Typography variant="body1" gutterBottom>
                Overall Progress
              </Typography>
              <LinearProgress
                variant="determinate"
                value={getTotalProgress()}
                sx={{ height: 10, borderRadius: 1, mb: 1 }}
              />
              <Typography variant="body2" color="text.secondary">
                {tvShow.episodes_watched} of {tvShow.total_episodes || '?'} total episodes watched
                ({Math.round(getTotalProgress())}%)
              </Typography>
            </Box>
            
            <Divider sx={{ my: 2 }} />
            
            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
              <Tabs
                value={selectedSeason}
                onChange={(e, newValue) => setSelectedSeason(newValue)}
                variant="scrollable"
                scrollButtons="auto"
              >
                {Object.keys(seasonData).map((season) => (
                  <Tab
                    key={season}
                    label={
                      <Stack direction="row" spacing={1} alignItems="center">
                        <span>Season {season}</span>
                        {getSeasonProgress(Number(season)) === 100 && (
                          <CheckCircleIcon fontSize="small" color="success" />
                        )}
                      </Stack>
                    }
                    value={Number(season)}
                  />
                ))}
              </Tabs>
            </Box>
            
            {renderSeasonTab(selectedSeason)}
          </>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default EpisodeTracker;