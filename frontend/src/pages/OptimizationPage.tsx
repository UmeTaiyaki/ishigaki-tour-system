// frontend/src/pages/OptimizationPage.tsx
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
  Chip
} from '@mui/material';
import Grid from '@mui/material/Unstable_Grid2';
import {
  PlayArrow as StartIcon,
  CheckCircle as SuccessIcon,
  ArrowBack as BackIcon,
  DirectionsCar as VehicleIcon,
  Group as GroupIcon,
  Route as RouteIcon,
  Timer as TimerIcon
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
    total_duration_minutes: number;
    efficiency_score: number;
    assigned_guests: string[];
    route_segments?: Array<{
      from_location: {
        name: string;
        lat: number;
        lng: number;
      };
      to_location: {
        name: string;
        lat: number;
        lng: number;
      };
      guest_id: string | null;
      arrival_time: string;
      departure_time: string;
      distance_km: number;
      duration_minutes: number;
    }>;
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
      // 最適化ジョブを開始
      const response = await api.post<OptimizationJobStatus>(`/tours/${id}/optimize`);
      const jobId = response.data.job_id;
      setJobStatus(response.data);
      
      // ポーリングして結果を取得
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
            
            // ツアー情報をリロード
            await loadTour(id);
          } else if (statusResponse.data.status === 'failed') {
            clearInterval(pollInterval);
            setError('最適化に失敗しました: ' + (statusResponse.data.error_message || 'Unknown error'));
            setIsOptimizing(false);
          }
        } catch (err: any) {
          clearInterval(pollInterval);
          setError('結果の取得に失敗しました');
          setIsOptimizing(false);
        }
      }, 2000);
      
    } catch (err: any) {
      setError('最適化の開始に失敗しました');
      setIsOptimizing(false);
    }
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

      <Grid container spacing={3}>
        {/* ツアー情報 */}
        <Grid size={{ xs: 12, md: 4 }}>
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
        </Grid>

        {/* 最適化設定 */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              最適化設定
            </Typography>
            
            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>最適化戦略</InputLabel>
              <Select
                value={strategy}
                label="最適化戦略"
                onChange={(e) => setStrategy(e.target.value)}
                disabled={isOptimizing}
              >
                <MenuItem value="safety">安全重視（余裕時間確保）</MenuItem>
                <MenuItem value="efficiency">効率重視（最短距離・最小時間）</MenuItem>
                <MenuItem value="balanced">バランス（安全性と効率性の両立）</MenuItem>
              </Select>
            </FormControl>

            <Button
              variant="contained"
              color="primary"
              size="large"
              startIcon={<StartIcon />}
              onClick={handleOptimize}
              disabled={isOptimizing || tour.total_participants === 0}
              fullWidth
            >
              {isOptimizing ? '最適化中...' : '最適化を実行'}
            </Button>

            {jobStatus && isOptimizing && (
              <Box mt={2}>
                <Typography variant="body2" gutterBottom>
                  進捗: {jobStatus.progress_percentage}% - {jobStatus.current_step}
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={jobStatus.progress_percentage} 
                />
              </Box>
            )}
          </Paper>

          {/* 最適化結果 */}
          {result && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                最適化結果
              </Typography>
              
              {/* サマリー */}
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Box textAlign="center">
                    <VehicleIcon color="primary" sx={{ fontSize: 40 }} />
                    <Typography variant="h4">{result.total_vehicles_used}</Typography>
                    <Typography variant="body2" color="text.secondary">使用車両数</Typography>
                  </Box>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Box textAlign="center">
                    <RouteIcon color="primary" sx={{ fontSize: 40 }} />
                    <Typography variant="h4">{result.total_distance_km.toFixed(1)}</Typography>
                    <Typography variant="body2" color="text.secondary">総走行距離(km)</Typography>
                  </Box>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Box textAlign="center">
                    <TimerIcon color="primary" sx={{ fontSize: 40 }} />
                    <Typography variant="h4">{result.total_time_minutes}</Typography>
                    <Typography variant="body2" color="text.secondary">総所要時間(分)</Typography>
                  </Box>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Box textAlign="center">
                    <SuccessIcon color="success" sx={{ fontSize: 40 }} />
                    <Typography variant="h4">{(result.average_efficiency_score * 100).toFixed(0)}%</Typography>
                    <Typography variant="body2" color="text.secondary">効率スコア</Typography>
                  </Box>
                </Grid>
              </Grid>

              {/* 警告 */}
              {result.warnings.length > 0 && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  {result.warnings.join('、')}
                </Alert>
              )}

              {/* 車両別ルート */}
              <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
                車両別ルート詳細
              </Typography>
              <List>
                {result.routes.map((route, index) => (
                  <Card key={index} sx={{ mb: 2 }}>
                    <CardContent>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                        <Typography variant="h6">
                          {route.vehicle_name}
                        </Typography>
                        <Chip 
                          icon={<GroupIcon />}
                          label={`${route.assigned_guests.length}名`}
                          color="primary"
                          size="small"
                        />
                      </Box>
                      
                      <Grid container spacing={2}>
                        <Grid size={4}>
                          <Typography variant="body2" color="text.secondary">
                            走行距離: {route.total_distance_km.toFixed(1)} km
                          </Typography>
                        </Grid>
                        <Grid size={4}>
                          <Typography variant="body2" color="text.secondary">
                            所要時間: {route.total_duration_minutes} 分
                          </Typography>
                        </Grid>
                        <Grid size={4}>
                          <Typography variant="body2" color="text.secondary">
                            効率: {(route.efficiency_score * 100).toFixed(0)}%
                          </Typography>
                        </Grid>
                      </Grid>

                      {/* ルートセグメント */}
                      {route.route_segments && route.route_segments.length > 0 && (
                        <Box mt={2}>
                          <Typography variant="body2" fontWeight="bold" gutterBottom>
                            ピックアップ順序:
                          </Typography>
                          {route.route_segments
                            .filter(seg => seg.guest_id !== null)
                            .map((seg, segIndex) => (
                              <Box key={segIndex} sx={{ ml: 2, mb: 1 }}>
                                <Typography variant="body2">
                                  {segIndex + 1}. {seg.from_location.name} → {seg.to_location.name}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  到着: {seg.arrival_time} / 出発: {seg.departure_time}
                                </Typography>
                              </Box>
                            ))}
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </List>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};