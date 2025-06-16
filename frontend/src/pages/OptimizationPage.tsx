import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Card,
  CardContent,
  Button,
  CircularProgress,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Alert,
  LinearProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  Chip,
  Stack
} from '@mui/material';
import {
  PlayArrow as StartIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  ArrowBack as BackIcon
} from '@mui/icons-material';
import { api } from '../services/api';
import { Tour, OptimizationJobStatus } from '../types';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

interface OptimizationResult {
  tour_id: string;
  status: string;
  total_vehicles_used: number;
  routes: Array<{
    vehicle_id: string;
    vehicle_name: string;
    total_distance_km: number;
    total_time_minutes: number;
    efficiency_score: number;
    assigned_guests: string[];
  }>;
  total_distance_km: number;
  total_time_minutes: number;
  average_efficiency_score: number;
  warnings: string[];
}

export const OptimizationPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [tour, setTour] = useState<Tour | null>(null);
  const [strategy, setStrategy] = useState('balanced');
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [jobStatus, setJobStatus] = useState<OptimizationJobStatus | null>(null);
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      loadTour(id);
    }
  }, [id]);

  const loadTour = async (tourId: string) => {
    try {
      const response = await api.get<Tour>(`/tours/${tourId}`);
      setTour(response.data);
      setError(null);
    } catch (err: any) {
      setError('ツアー情報の取得に失敗しました');
      console.error('Error loading tour:', err);
    } finally {
      setLoading(false);
    }
  };

const handleOptimize = async () => {
  if (!id || !tour) return;

  setIsOptimizing(true);
  setError(null);
  setResult(null);

  try {
    // 最適化を開始 - リクエストボディを修正
    const response = await api.post(`/tours/${id}/optimize`);
    // または、バックエンドが期待する形式に合わせて：
    // const response = await api.post(`/tours/${id}/optimize`, {});

    const jobId = response.data.job_id;
    
    // ポーリングで結果を取得
    pollOptimizationStatus(jobId);
  } catch (err: any) {
    setError('最適化の開始に失敗しました');
    console.error('Error starting optimization:', err);
    setIsOptimizing(false);
  }
};

  const pollOptimizationStatus = async (jobId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const statusResponse = await api.get<OptimizationJobStatus>(`/optimize/status/${jobId}`);
        setJobStatus(statusResponse.data);

        if (statusResponse.data.status === 'completed') {
          clearInterval(pollInterval);
          
          // 結果を取得
          const resultResponse = await api.get<OptimizationResult>(`/optimize/result/${jobId}`);
          setResult(resultResponse.data);
          setIsOptimizing(false);
          
          // ツアー情報を再読み込み
          if (id) {
            await loadTour(id);
          }
        } else if (statusResponse.data.status === 'failed') {
          clearInterval(pollInterval);
          setError(statusResponse.data.error_message || '最適化に失敗しました');
          setIsOptimizing(false);
        }
      } catch (err) {
        clearInterval(pollInterval);
        setError('状態の確認に失敗しました');
        setIsOptimizing(false);
      }
    }, 1000);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (!tour) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">ツアーが見つかりません</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" alignItems="center" mb={3}>
        <Button
          startIcon={<BackIcon />}
          onClick={() => navigate('/tours')}
          sx={{ mr: 2 }}
        >
          戻る
        </Button>
        <Typography variant="h4" component="h1">
          ツアー最適化
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
        {/* ツアー情報 */}
        <Box sx={{ flex: { xs: '1 1 100%', md: '0 0 33%' } }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                ツアー情報
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Typography variant="body2" color="text.secondary" gutterBottom>
                日付: {format(new Date(tour.tour_date), 'yyyy年MM月dd日', { locale: ja })}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                アクティビティ: {tour.activity_type}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                目的地: {tour.destination_name}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                参加者数: {tour.total_participants}名
              </Typography>
              <Typography variant="body2" color="text.secondary">
                出発時刻: {tour.departure_time}
              </Typography>
            </CardContent>
          </Card>
        </Box>

        {/* 最適化設定 */}
        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 auto' } }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              最適化設定
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>最適化戦略</InputLabel>
              <Select
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                disabled={isOptimizing}
              >
                <MenuItem value="safety">安全重視（悪天候対応・余裕時間確保）</MenuItem>
                <MenuItem value="efficiency">効率重視（最短距離・最小時間）</MenuItem>
                <MenuItem value="balanced">バランス（安全性と効率の両立）</MenuItem>
              </Select>
            </FormControl>

            <Button
              variant="contained"
              color="primary"
              size="large"
              onClick={handleOptimize}
              disabled={isOptimizing || tour.status !== 'planning'}
              startIcon={isOptimizing ? <CircularProgress size={20} /> : <StartIcon />}
              fullWidth
            >
              {isOptimizing ? '最適化実行中...' : '最適化を実行'}
            </Button>

            {jobStatus && isOptimizing && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  進捗: {jobStatus.progress_percentage}%
                </Typography>
                <LinearProgress variant="determinate" value={jobStatus.progress_percentage} />
              </Box>
            )}
          </Paper>
        </Box>
      </Box>

      {/* 最適化結果 */}
      {result && (
        <Box sx={{ mt: 3 }}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" alignItems="center" mb={2}>
              <SuccessIcon color="success" sx={{ mr: 1 }} />
              <Typography variant="h6">
                最適化結果
              </Typography>
            </Box>
            <Divider sx={{ mb: 2 }} />

            <Box sx={{ 
              display: 'flex', 
              flexWrap: 'wrap', 
              gap: 2, 
              mb: 3 
            }}>
              <Box sx={{ flex: '1 1 200px' }}>
                <Typography variant="body2" color="text.secondary">
                  使用車両数
                </Typography>
                <Typography variant="h5">
                  {result.total_vehicles_used}台
                </Typography>
              </Box>
              <Box sx={{ flex: '1 1 200px' }}>
                <Typography variant="body2" color="text.secondary">
                  総走行距離
                </Typography>
                <Typography variant="h5">
                  {result.total_distance_km.toFixed(1)}km
                </Typography>
              </Box>
              <Box sx={{ flex: '1 1 200px' }}>
                <Typography variant="body2" color="text.secondary">
                  総所要時間
                </Typography>
                <Typography variant="h5">
                  {result.total_time_minutes}分
                </Typography>
              </Box>
              <Box sx={{ flex: '1 1 200px' }}>
                <Typography variant="body2" color="text.secondary">
                  効率スコア
                </Typography>
                <Typography variant="h5">
                  {(result.average_efficiency_score * 100).toFixed(0)}%
                </Typography>
              </Box>
            </Box>

            {result.warnings.length > 0 && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                {result.warnings.join(', ')}
              </Alert>
            )}

            <Typography variant="subtitle1" gutterBottom>
              車両別ルート
            </Typography>
            <List>
              {result.routes.map((route, index) => (
                <ListItem key={index} divider>
                  <ListItemText
                    primary={route.vehicle_name}
                    secondary={
                      <>
                        走行距離: {route.total_distance_km.toFixed(1)}km / 
                        所要時間: {route.total_time_minutes}分 / 
                        乗客数: {route.assigned_guests.length}名
                      </>
                    }
                  />
                  <Chip 
                    label={`効率 ${(route.efficiency_score * 100).toFixed(0)}%`}
                    color={route.efficiency_score > 0.8 ? 'success' : 'default'}
                    size="small"
                  />
                </ListItem>
              ))}
            </List>

            <Box display="flex" justifyContent="center" mt={3}>
              <Button
                variant="contained"
                color="primary"
                onClick={() => navigate(`/tours/${id}`)}
              >
                詳細を確認
              </Button>
            </Box>
          </Paper>
        </Box>
      )}
    </Container>
  );
};