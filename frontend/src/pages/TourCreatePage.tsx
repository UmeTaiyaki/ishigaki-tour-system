// frontend/src/pages/TourCreatePage.tsx
import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Autocomplete,
  Chip,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Divider
} from '@mui/material';
import { Grid2 } from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { ja } from 'date-fns/locale';
import { useNavigate } from 'react-router-dom';
import {
  Event as EventIcon,
  Schedule as TimeIcon,
  Map as MapIcon,
  People as PeopleIcon,
  DirectionsCar as CarIcon,
  PlayArrow as OptimizeIcon
} from '@mui/icons-material';
import { api } from '../services/api';
import { Guest, Vehicle } from '../types';

interface Destination {
  name: string;
  lat: number;
  lng: number;
  activityTypes: string[];
}

export const TourCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tourDate, setTourDate] = useState<Date | null>(new Date());
  const [activityType, setActivityType] = useState('snorkeling');
  const [destinationName, setDestinationName] = useState('');
  const [destinationCoords, setDestinationCoords] = useState({ lat: 0, lng: 0 });
  const [departureTime, setDepartureTime] = useState<Date | null>(() => {
    const defaultTime = new Date();
    defaultTime.setHours(8, 0, 0, 0);
    return defaultTime;
  });
  const [guests, setGuests] = useState<Guest[]>([]);
  const [selectedGuests, setSelectedGuests] = useState<Guest[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [selectedVehicles, setSelectedVehicles] = useState<Vehicle[]>([]);
  const [autoSelectVehicles, setAutoSelectVehicles] = useState(true);

  // 石垣島の人気観光地
  const destinations: Destination[] = [
    { name: '川平湾', lat: 24.4526, lng: 124.1456, activityTypes: ['sightseeing', 'kayaking'] },
    { name: '青の洞窟', lat: 24.3967, lng: 124.1428, activityTypes: ['snorkeling', 'diving'] },
    { name: 'マンタスクランブル', lat: 24.4167, lng: 124.0833, activityTypes: ['diving'] },
    { name: '幻の島（浜島）', lat: 24.3000, lng: 124.0833, activityTypes: ['snorkeling', 'sightseeing'] },
    { name: '竹富島', lat: 24.3333, lng: 124.0833, activityTypes: ['sightseeing', 'snorkeling'] },
    { name: '西表島', lat: 24.3333, lng: 123.8167, activityTypes: ['kayaking', 'sightseeing'] },
    { name: '平久保崎', lat: 24.5917, lng: 124.2833, activityTypes: ['sightseeing'] },
    { name: '米原ビーチ', lat: 24.4444, lng: 124.1944, activityTypes: ['snorkeling'] }
  ];

  const activityTypes = [
    { value: 'snorkeling', label: 'シュノーケリング', icon: '🤿' },
    { value: 'diving', label: 'ダイビング', icon: '🤿' },
    { value: 'sightseeing', label: '観光', icon: '🏝️' },
    { value: 'kayaking', label: 'カヤック', icon: '🛶' },
    { value: 'fishing', label: '釣り', icon: '🎣' }
  ];

  useEffect(() => {
    loadGuestsAndVehicles();
  }, []);

  const loadGuestsAndVehicles = async () => {
    try {
      setLoading(true);
      const [guestsRes, vehiclesRes] = await Promise.all([
        api.get('/guests'),
        api.get('/vehicles')
      ]);
      setGuests(guestsRes.data);
      // 利用可能な車両のみフィルタ
      setVehicles(vehiclesRes.data.filter((v: Vehicle) => v.status === 'available'));
      setError(null);
    } catch (err: any) {
      setError('データの読み込みに失敗しました');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDestinationSelect = (destinationName: string) => {
    const destination = destinations.find(d => d.name === destinationName);
    if (destination) {
      setDestinationName(destination.name);
      setDestinationCoords({ lat: destination.lat, lng: destination.lng });
      
      // アクティビティタイプを自動設定（その目的地で可能な最初のもの）
      if (destination.activityTypes.includes(activityType) === false && destination.activityTypes.length > 0) {
        setActivityType(destination.activityTypes[0]);
      }
    }
  };

  const calculateTotalCapacity = () => {
    const vehiclesToUse = autoSelectVehicles ? vehicles : selectedVehicles;
    return vehiclesToUse.reduce((total, vehicle) => 
      total + vehicle.capacity_adults + vehicle.capacity_children, 0
    );
  };

  const calculateTotalGuests = () => {
    return selectedGuests.reduce((total, guest) => 
      total + guest.num_adults + guest.num_children, 0
    );
  };

  const validateForm = () => {
    if (!tourDate) {
      setError('ツアー日付を選択してください');
      return false;
    }
    if (!destinationName) {
      setError('目的地を選択してください');
      return false;
    }
    if (selectedGuests.length === 0) {
      setError('参加ゲストを選択してください');
      return false;
    }
    if (!autoSelectVehicles && selectedVehicles.length === 0) {
      setError('使用車両を選択してください');
      return false;
    }
    
    const totalCapacity = calculateTotalCapacity();
    const totalGuests = calculateTotalGuests();
    if (totalCapacity < totalGuests) {
      setError(`車両の総定員（${totalCapacity}名）が参加人数（${totalGuests}名）より少ないです`);
      return false;
    }
    
    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setLoading(true);
    setError(null);
    
    try {
      const payload = {
        tour_date: tourDate!.toISOString().split('T')[0],
        activity_type: activityType,
        destination_name: destinationName,
        destination_lat: destinationCoords.lat,
        destination_lng: destinationCoords.lng,
        departure_time: departureTime?.toTimeString().slice(0, 5) || '08:00',
        participant_ids: selectedGuests.map(g => g.id),
        vehicle_ids: autoSelectVehicles ? undefined : selectedVehicles.map(v => v.id),
        status: 'planning',
        optimization_strategy: 'balanced'
      };

      const response = await api.post('/tours', payload);
      
      // 作成成功後、最適化画面へ遷移
      navigate(`/tours/${response.data.id}/optimize`);
    } catch (err: any) {
      console.error('Failed to create tour:', err);
      setError('ツアーの作成に失敗しました: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  if (loading && guests.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ja}>
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Paper sx={{ p: 4 }}>
          <Typography variant="h5" gutterBottom>
            新規ツアー作成
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            ツアーの基本情報を入力して、ルート最適化を実行します
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <Grid2 container spacing={3} sx={{ mt: 2 }}>
            {/* 基本情報 */}
            <Grid2 size={12}>
              <Card variant="outlined">
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <EventIcon color="primary" />
                    <Typography variant="h6">基本情報</Typography>
                  </Box>
                  
                  <Grid2 container spacing={2}>
                    <Grid2 size={{ xs: 12, sm: 6 }}>
                      <DatePicker
                        label="ツアー日付"
                        value={tourDate}
                        onChange={setTourDate}
                        slotProps={{ 
                          textField: { 
                            fullWidth: true,
                            required: true
                          } 
                        }}
                        minDate={new Date()}
                      />
                    </Grid2>
                    
                    <Grid2 size={{ xs: 12, sm: 6 }}>
                      <TimePicker
                        label="出発時刻"
                        value={departureTime}
                        onChange={setDepartureTime}
                        slotProps={{ 
                          textField: { 
                            fullWidth: true,
                            helperText: "目的地への出発時刻"
                          } 
                        }}
                      />
                    </Grid2>
                    
                    <Grid2 size={{ xs: 12, sm: 6 }}>
                      <FormControl fullWidth required>
                        <InputLabel>アクティビティ</InputLabel>
                        <Select
                          value={activityType}
                          onChange={(e) => setActivityType(e.target.value)}
                          label="アクティビティ"
                        >
                          {activityTypes.map((type) => (
                            <MenuItem key={type.value} value={type.value}>
                              <Box display="flex" alignItems="center" gap={1}>
                                <span>{type.icon}</span>
                                {type.label}
                              </Box>
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid2>
                    
                    <Grid2 size={{ xs: 12, sm: 6 }}>
                      <FormControl fullWidth required>
                        <InputLabel>目的地</InputLabel>
                        <Select
                          value={destinationName}
                          onChange={(e) => handleDestinationSelect(e.target.value)}
                          label="目的地"
                        >
                          <MenuItem value="">
                            <em>目的地を選択</em>
                          </MenuItem>
                          {destinations
                            .filter(d => d.activityTypes.includes(activityType))
                            .map((dest) => (
                              <MenuItem key={dest.name} value={dest.name}>
                                {dest.name}
                              </MenuItem>
                            ))}
                        </Select>
                      </FormControl>
                    </Grid2>
                  </Grid2>
                </CardContent>
              </Card>
            </Grid2>

            {/* 参加ゲスト */}
            <Grid2 size={12}>
              <Card variant="outlined">
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <PeopleIcon color="primary" />
                    <Typography variant="h6">参加ゲスト</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
                      選択済み: {selectedGuests.length}名 / 合計: {calculateTotalGuests()}名
                    </Typography>
                  </Box>
                  
                  <Autocomplete
                    multiple
                    options={guests}
                    getOptionLabel={(option) => `${option.name} (${option.hotel_name || '未設定'})`}
                    value={selectedGuests}
                    onChange={(_, value) => setSelectedGuests(value)}
                    renderInput={(params) => (
                      <TextField 
                        {...params} 
                        label="ゲストを選択" 
                        required
                        helperText="参加するゲストを選択してください"
                      />
                    )}
                    renderTags={(value, getTagProps) =>
                      value.map((option, index) => (
                        <Chip
                          variant="outlined"
                          label={`${option.name} (${option.num_adults}大人${option.num_children > 0 ? `+${option.num_children}子供` : ''})`}
                          {...getTagProps({ index })}
                        />
                      ))
                    }
                    renderOption={(props, option) => (
                      <Box component="li" {...props}>
                        <Box>
                          <Typography variant="body2">{option.name}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {option.hotel_name || '宿泊先未設定'} - 大人{option.num_adults}名
                            {option.num_children > 0 && `、子供${option.num_children}名`}
                          </Typography>
                        </Box>
                      </Box>
                    )}
                  />
                </CardContent>
              </Card>
            </Grid2>

            {/* 使用車両 */}
            <Grid2 size={12}>
              <Card variant="outlined">
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <CarIcon color="primary" />
                    <Typography variant="h6">使用車両</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
                      総定員: {calculateTotalCapacity()}名
                    </Typography>
                  </Box>
                  
                  <FormControl component="fieldset" sx={{ mb: 2 }}>
                    <Box display="flex" gap={2}>
                      <Button
                        variant={autoSelectVehicles ? "contained" : "outlined"}
                        onClick={() => setAutoSelectVehicles(true)}
                        size="small"
                      >
                        自動選択
                      </Button>
                      <Button
                        variant={!autoSelectVehicles ? "contained" : "outlined"}
                        onClick={() => setAutoSelectVehicles(false)}
                        size="small"
                      >
                        手動選択
                      </Button>
                    </Box>
                  </FormControl>
                  
                  {autoSelectVehicles ? (
                    <Alert severity="info">
                      最適化時に、参加人数に応じて最適な車両が自動的に選択されます
                    </Alert>
                  ) : (
                    <Autocomplete
                      multiple
                      options={vehicles}
                      getOptionLabel={(option) => `${option.name} (定員: ${option.capacity_adults + option.capacity_children}名)`}
                      value={selectedVehicles}
                      onChange={(_, value) => setSelectedVehicles(value)}
                      renderInput={(params) => (
                        <TextField 
                          {...params} 
                          label="車両を選択"
                          helperText="使用する車両を選択してください"
                        />
                      )}
                      renderOption={(props, option) => (
                        <Box component="li" {...props}>
                          <Box>
                            <Typography variant="body2">{option.name}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {option.vehicle_type} - 定員: 大人{option.capacity_adults}名、子供{option.capacity_children}名
                              {option.driver_name && ` - ドライバー: ${option.driver_name}`}
                            </Typography>
                          </Box>
                        </Box>
                      )}
                    />
                  )}
                  
                  {calculateTotalCapacity() < calculateTotalGuests() && (
                    <Alert severity="warning" sx={{ mt: 2 }}>
                      車両の総定員が参加人数より少ないです。車両を追加してください。
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </Grid2>
          </Grid2>

          {/* アクションボタン */}
          <Box sx={{ mt: 4, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button
              onClick={() => navigate('/tours')}
              disabled={loading}
            >
              キャンセル
            </Button>
            <Button
              variant="contained"
              onClick={handleSubmit}
              disabled={loading || !tourDate || !destinationName || selectedGuests.length === 0}
              startIcon={loading ? <CircularProgress size={20} /> : <OptimizeIcon />}
            >
              {loading ? '作成中...' : 'ツアーを作成して最適化へ'}
            </Button>
          </Box>
        </Paper>
      </Container>
    </LocalizationProvider>
  );
};