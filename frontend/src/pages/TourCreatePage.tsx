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
  Divider,
  Stack
} from '@mui/material';
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
    if (!vehiclesToUse || vehiclesToUse.length === 0) return 0;
    
    return vehiclesToUse.reduce((total, vehicle) => 
      total + (vehicle.capacity_adults || 0) + (vehicle.capacity_children || 0), 0
    );
  };

  const calculateTotalGuests = () => {
    if (!selectedGuests || selectedGuests.length === 0) return 0;
    
    return selectedGuests.reduce((total, guest) => 
      total + (guest.num_adults || 0) + (guest.num_children || 0), 0
    );
  };

  const isFormValid = () => {
    if (!tourDate) return false;
    if (!destinationName) return false;
    if (selectedGuests.length === 0) return false;
    if (!autoSelectVehicles && selectedVehicles.length === 0) return false;
    
    const totalCapacity = calculateTotalCapacity();
    const totalGuests = calculateTotalGuests();
    if (totalCapacity < totalGuests) return false;
    
    return true;
  };

  const getValidationError = () => {
    if (!tourDate) {
      return 'ツアー日付を選択してください';
    }
    if (!destinationName) {
      return '目的地を選択してください';
    }
    if (selectedGuests.length === 0) {
      return '参加ゲストを選択してください';
    }
    if (!autoSelectVehicles && selectedVehicles.length === 0) {
      return '使用車両を選択してください';
    }
    
    const totalCapacity = calculateTotalCapacity();
    const totalGuests = calculateTotalGuests();
    if (totalCapacity < totalGuests) {
      return `車両の総定員（${totalCapacity}名）が参加人数（${totalGuests}名）より少ないです`;
    }
    
    return null;
  };

  const handleSubmit = async () => {
    const validationError = getValidationError();
    if (validationError) {
      setError(validationError);
      return;
    }

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
        vehicle_ids: autoSelectVehicles ? 
          vehicles.slice(0, Math.ceil(calculateTotalGuests() / 8)).map(v => v.id) :
          selectedVehicles.map(v => v.id)
      };

      const response = await api.post('/tours', payload);
      
      // 作成成功後、最適化ページへ遷移
      navigate(`/tours/${response.data.id}/optimize`);
    } catch (err: any) {
      setError(err.response?.data?.message || 'ツアーの作成に失敗しました');
      console.error('Error creating tour:', err);
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
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 4 }}>
        新規ツアー作成
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ja}>
        <Stack spacing={3}>
          {/* 基本情報 */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <EventIcon /> 基本情報
              </Typography>
              <Divider sx={{ my: 2 }} />
              
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 3 }}>
                <DatePicker
                  label="ツアー日"
                  value={tourDate}
                  onChange={(newValue) => setTourDate(newValue)}
                  sx={{ width: '100%' }}
                />
                
                <TimePicker
                  label="出発時刻"
                  value={departureTime}
                  onChange={(newValue) => setDepartureTime(newValue)}
                  sx={{ width: '100%' }}
                  ampm={false}
                />
                
                <FormControl fullWidth>
                  <InputLabel>アクティビティ</InputLabel>
                  <Select
                    value={activityType}
                    onChange={(e) => setActivityType(e.target.value)}
                    label="アクティビティ"
                  >
                    {activityTypes.map((type) => (
                      <MenuItem key={type.value} value={type.value}>
                        {type.icon} {type.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
            </CardContent>
          </Card>

          {/* 目的地情報 */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <MapIcon /> 目的地
              </Typography>
              <Divider sx={{ my: 2 }} />
              
              <Autocomplete
                value={destinationName}
                onChange={(_, newValue) => {
                  if (newValue) handleDestinationSelect(newValue);
                }}
                options={destinations
                  .filter(d => d.activityTypes.includes(activityType))
                  .map(d => d.name)}
                renderInput={(params) => (
                  <TextField {...params} label="目的地を選択" />
                )}
                sx={{ mb: 2 }}
              />
              
              {destinationCoords.lat !== 0 && (
                <Typography variant="body2" color="text.secondary">
                  座標: {destinationCoords.lat.toFixed(4)}, {destinationCoords.lng.toFixed(4)}
                </Typography>
              )}
            </CardContent>
          </Card>

          {/* ゲスト選択 */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <PeopleIcon /> 参加ゲスト
              </Typography>
              <Divider sx={{ my: 2 }} />
              
              <Autocomplete
                multiple
                value={selectedGuests}
                onChange={(_, newValue) => setSelectedGuests(newValue)}
                options={guests}
                getOptionLabel={(option) => 
                  `${option.name} (大人${option.num_adults}名・子供${option.num_children}名)`
                }
                renderInput={(params) => (
                  <TextField {...params} label="ゲストを選択" />
                )}
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => (
                    <Chip
                      variant="outlined"
                      label={`${option.name} (${option.num_adults + option.num_children}名)`}
                      {...getTagProps({ index })}
                    />
                  ))
                }
              />
              
              {selectedGuests.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    合計: 大人{selectedGuests.reduce((sum, g) => sum + g.num_adults, 0)}名・
                    子供{selectedGuests.reduce((sum, g) => sum + g.num_children, 0)}名
                    （計{calculateTotalGuests()}名）
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>

          {/* 車両選択 */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CarIcon /> 使用車両
              </Typography>
              <Divider sx={{ my: 2 }} />
              
              <FormControl sx={{ mb: 2 }}>
                <Select
                  value={autoSelectVehicles ? 'auto' : 'manual'}
                  onChange={(e) => setAutoSelectVehicles(e.target.value === 'auto')}
                >
                  <MenuItem value="auto">自動選択</MenuItem>
                  <MenuItem value="manual">手動選択</MenuItem>
                </Select>
              </FormControl>
              
              {!autoSelectVehicles && (
                <Autocomplete
                  multiple
                  value={selectedVehicles}
                  onChange={(_, newValue) => setSelectedVehicles(newValue)}
                  options={vehicles}
                  getOptionLabel={(option) => 
                    `${option.name} (定員: 大人${option.capacity_adults}名・子供${option.capacity_children}名)`
                  }
                  renderInput={(params) => (
                    <TextField {...params} label="車両を選択" />
                  )}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <Chip
                        variant="outlined"
                        label={`${option.name} (${option.capacity_adults + option.capacity_children}名)`}
                        {...getTagProps({ index })}
                      />
                    ))
                  }
                />
              )}
              
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  車両総定員: {calculateTotalCapacity()}名
                  {calculateTotalCapacity() < calculateTotalGuests() && (
                    <Typography component="span" color="error">
                      {' '}（定員不足！）
                    </Typography>
                  )}
                </Typography>
              </Box>
            </CardContent>
          </Card>

          {/* アクションボタン */}
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              onClick={() => navigate('/tours')}
              disabled={loading}
            >
              キャンセル
            </Button>
            <Button
              variant="contained"
              onClick={handleSubmit}
              disabled={loading || !isFormValid()}
              startIcon={loading ? <CircularProgress size={20} /> : <OptimizeIcon />}
            >
              {loading ? '作成中...' : 'ツアーを作成して最適化へ'}
            </Button>
          </Box>
        </Stack>
      </LocalizationProvider>
    </Container>
  );
};