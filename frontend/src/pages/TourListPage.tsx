import React, { useEffect, useState } from 'react';
import {
  Container,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Chip,
  IconButton,
  Typography,
  Box,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  Visibility as ViewIcon,
  PlayArrow as OptimizeIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Tour, TourListResponse } from '../types';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

const activityTypeLabels: Record<string, string> = {
  snorkeling: 'シュノーケリング',
  diving: 'ダイビング',
  sightseeing: '観光',
  kayaking: 'カヤック',
  fishing: '釣り'
};

const statusLabels: Record<string, string> = {
  planning: '計画中',
  confirmed: '確定',
  in_progress: '実施中',
  completed: '完了',
  cancelled: 'キャンセル'
};

const statusColors: Record<string, 'default' | 'primary' | 'success' | 'warning' | 'error'> = {
  planning: 'default',
  confirmed: 'primary',
  in_progress: 'warning',
  completed: 'success',
  cancelled: 'error'
};

export const TourListPage: React.FC = () => {
  const [tours, setTours] = useState<Tour[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadTours();
  }, []);

  const loadTours = async () => {
    try {
      setLoading(true);
      const response = await api.get<TourListResponse>('/tours');
      setTours(response.data.tours);
      setError(null);
    } catch (err: any) {
      setError('ツアー一覧の取得に失敗しました');
      console.error('Error loading tours:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOptimize = (tourId: string) => {
    navigate(`/tours/${tourId}/optimize`);
  };

  const handleView = (tourId: string) => {
    navigate(`/tours/${tourId}`);
  };

  const handleCreate = () => {
    navigate('/tours/new');
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          ツアー一覧
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={handleCreate}
        >
          新規ツアー作成
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper elevation={2}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>日付</TableCell>
                <TableCell>アクティビティ</TableCell>
                <TableCell>目的地</TableCell>
                <TableCell align="center">参加者数</TableCell>
                <TableCell align="center">車両数</TableCell>
                <TableCell align="center">状態</TableCell>
                <TableCell align="center">アクション</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tours.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    ツアーがありません
                  </TableCell>
                </TableRow>
              ) : (
                tours.map((tour) => (
                  <TableRow key={tour.id} hover>
                    <TableCell>
                      {format(new Date(tour.tour_date), 'yyyy年MM月dd日', { locale: ja })}
                    </TableCell>
                    <TableCell>{activityTypeLabels[tour.activity_type] || tour.activity_type}</TableCell>
                    <TableCell>{tour.destination_name}</TableCell>
                    <TableCell align="center">{tour.total_participants}名</TableCell>
                    <TableCell align="center">
                      {tour.total_vehicles_used > 0 ? `${tour.total_vehicles_used}台` : '-'}
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={statusLabels[tour.status] || tour.status}
                        color={statusColors[tour.status] || 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="center">
                      <IconButton
                        size="small"
                        onClick={() => handleView(tour.id)}
                        title="詳細を見る"
                      >
                        <ViewIcon />
                      </IconButton>
                      {tour.status === 'planning' && (
                        <IconButton
                          size="small"
                          onClick={() => handleOptimize(tour.id)}
                          title="最適化を実行"
                          color="primary"
                        >
                          <OptimizeIcon />
                        </IconButton>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Container>
  );
};