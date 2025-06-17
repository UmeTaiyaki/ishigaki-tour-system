// frontend/src/pages/VehicleManagementPage.tsx
import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Box,
  Typography,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  DirectionsCar as CarIcon,
  Person as DriverIcon,
  Phone as PhoneIcon,
  CheckCircle as ActiveIcon,
  Cancel as InactiveIcon
} from '@mui/icons-material';
import { api } from '../services/api';

interface Vehicle {
  id: string;
  name: string;
  capacity_adults: number;
  capacity_children: number;
  driver_name?: string;
  driver_phone?: string;
  vehicle_type?: 'sedan' | 'van' | 'minibus';
  status?: 'available' | 'in_use' | 'maintenance';
  equipment: string[];
  license_plate?: string;
  fuel_type?: string;
}

export const VehicleManagementPage: React.FC = () => {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState<Vehicle | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    capacity_adults: 8,
    capacity_children: 3,
    driver_name: '',
    driver_phone: '',
    vehicle_type: 'van' as 'sedan' | 'van' | 'minibus',
    status: 'available' as 'available' | 'in_use' | 'maintenance',
    equipment: [] as string[],
    license_plate: '',
    fuel_type: 'gasoline'
  });

  const vehicleTypes = [
    { value: 'sedan', label: 'セダン', defaultAdults: 4, defaultChildren: 2 },
    { value: 'van', label: 'バン', defaultAdults: 8, defaultChildren: 3 },
    { value: 'minibus', label: 'マイクロバス', defaultAdults: 20, defaultChildren: 5 }
  ];

  const statusOptions = [
    { value: 'available', label: '利用可能', color: 'success' as const },
    { value: 'in_use', label: '使用中', color: 'warning' as const },
    { value: 'maintenance', label: 'メンテナンス中', color: 'error' as const }
  ];

  const equipmentOptions = [
    'チャイルドシート',
    '車椅子対応',
    'Wi-Fi',
    'USB充電',
    '冷蔵庫',
    'カラオケ',
    '多言語ガイドシステム'
  ];

  useEffect(() => {
    loadVehicles();
  }, []);

  const loadVehicles = async () => {
    try {
      setLoading(true);
      const response = await api.get('/vehicles');
      setVehicles(response.data);
      setError(null);
    } catch (err: any) {
      setError('車両一覧の取得に失敗しました');
      console.error('Error loading vehicles:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      const payload = {
        ...formData,
        equipment: formData.equipment.filter(eq => eq.trim() !== '')
      };

      if (editingVehicle) {
        await api.put(`/vehicles/${editingVehicle.id}`, payload);
      } else {
        await api.post('/vehicles', payload);
      }

      setOpenDialog(false);
      resetForm();
      loadVehicles();
    } catch (err: any) {
      setError(err.response?.data?.message || '保存に失敗しました');
      console.error('Error saving vehicle:', err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('この車両を削除しますか？')) return;

    try {
      await api.delete(`/vehicles/${id}`);
      loadVehicles();
    } catch (err: any) {
      setError('削除に失敗しました');
      console.error('Error deleting vehicle:', err);
    }
  };

  const handleEdit = (vehicle: Vehicle) => {
    setEditingVehicle(vehicle);
    setFormData({
      name: vehicle.name,
      capacity_adults: vehicle.capacity_adults,
      capacity_children: vehicle.capacity_children,
      driver_name: vehicle.driver_name || '',
      driver_phone: vehicle.driver_phone || '',
      vehicle_type: vehicle.vehicle_type || 'van',
      status: vehicle.status || 'available',
      equipment: vehicle.equipment || [],
      license_plate: vehicle.license_plate || '',
      fuel_type: vehicle.fuel_type || 'gasoline'
    });
    setOpenDialog(true);
  };

  const handleVehicleTypeChange = (type: string) => {
    const vehicleType = vehicleTypes.find(vt => vt.value === type);
    if (vehicleType) {
      setFormData({
        ...formData,
        vehicle_type: type as 'sedan' | 'van' | 'minibus',
        capacity_adults: vehicleType.defaultAdults,
        capacity_children: vehicleType.defaultChildren
      });
    }
  };

  const resetForm = () => {
    setEditingVehicle(null);
    setFormData({
      name: '',
      capacity_adults: 8,
      capacity_children: 3,
      driver_name: '',
      driver_phone: '',
      vehicle_type: 'van',
      status: 'available',
      equipment: [],
      license_plate: '',
      fuel_type: 'gasoline'
    });
  };

  const getStatusChip = (status?: string) => {
    const option = statusOptions.find(opt => opt.value === status) || statusOptions[0];
    return <Chip label={option.label} color={option.color} size="small" />;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">車両管理</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            resetForm();
            setOpenDialog(true);
          }}
        >
          新規車両
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>車両名</TableCell>
              <TableCell>タイプ</TableCell>
              <TableCell align="center">定員（大人/子供）</TableCell>
              <TableCell>ドライバー</TableCell>
              <TableCell>装備</TableCell>
              <TableCell align="center">ステータス</TableCell>
              <TableCell align="center">操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {vehicles.map((vehicle) => (
              <TableRow key={vehicle.id}>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CarIcon fontSize="small" />
                    {vehicle.name}
                    {vehicle.license_plate && (
                      <Typography variant="caption" color="text.secondary">
                        ({vehicle.license_plate})
                      </Typography>
                    )}
                  </Box>
                </TableCell>
                <TableCell>
                  {vehicleTypes.find(vt => vt.value === vehicle.vehicle_type)?.label || '-'}
                </TableCell>
                <TableCell align="center">
                  {vehicle.capacity_adults}/{vehicle.capacity_children}
                </TableCell>
                <TableCell>
                  {vehicle.driver_name && (
                    <Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <DriverIcon fontSize="small" />
                        <Typography variant="body2">{vehicle.driver_name}</Typography>
                      </Box>
                      {vehicle.driver_phone && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <PhoneIcon fontSize="small" />
                          <Typography variant="caption">{vehicle.driver_phone}</Typography>
                        </Box>
                      )}
                    </Box>
                  )}
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {vehicle.equipment?.map((eq, index) => (
                      <Chip key={index} label={eq} size="small" variant="outlined" />
                    ))}
                  </Box>
                </TableCell>
                <TableCell align="center">
                  {getStatusChip(vehicle.status)}
                </TableCell>
                <TableCell align="center">
                  <IconButton onClick={() => handleEdit(vehicle)} size="small">
                    <EditIcon />
                  </IconButton>
                  <IconButton onClick={() => handleDelete(vehicle.id)} size="small" color="error">
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* 車両編集ダイアログ */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>{editingVehicle ? '車両編集' : '新規車両登録'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
              <TextField
                fullWidth
                label="車両名"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
              
              <TextField
                fullWidth
                label="ナンバープレート"
                value={formData.license_plate}
                onChange={(e) => setFormData({ ...formData, license_plate: e.target.value })}
              />
            </Box>
            
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2 }}>
              <FormControl fullWidth>
                <InputLabel>車両タイプ</InputLabel>
                <Select
                  value={formData.vehicle_type}
                  onChange={(e) => handleVehicleTypeChange(e.target.value)}
                  label="車両タイプ"
                >
                  {vehicleTypes.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              <TextField
                fullWidth
                type="number"
                label="大人定員"
                value={formData.capacity_adults}
                onChange={(e) => setFormData({ ...formData, capacity_adults: parseInt(e.target.value) || 0 })}
                inputProps={{ min: 0 }}
              />
              
              <TextField
                fullWidth
                type="number"
                label="子供定員"
                value={formData.capacity_children}
                onChange={(e) => setFormData({ ...formData, capacity_children: parseInt(e.target.value) || 0 })}
                inputProps={{ min: 0 }}
              />
            </Box>
            
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
              <TextField
                fullWidth
                label="ドライバー名"
                value={formData.driver_name}
                onChange={(e) => setFormData({ ...formData, driver_name: e.target.value })}
              />
              
              <TextField
                fullWidth
                label="ドライバー電話番号"
                value={formData.driver_phone}
                onChange={(e) => setFormData({ ...formData, driver_phone: e.target.value })}
              />
            </Box>
            
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
              <FormControl fullWidth>
                <InputLabel>ステータス</InputLabel>
                <Select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value as any })}
                  label="ステータス"
                >
                  {statusOptions.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              <FormControl fullWidth>
                <InputLabel>燃料タイプ</InputLabel>
                <Select
                  value={formData.fuel_type}
                  onChange={(e) => setFormData({ ...formData, fuel_type: e.target.value })}
                  label="燃料タイプ"
                >
                  <MenuItem value="gasoline">ガソリン</MenuItem>
                  <MenuItem value="diesel">ディーゼル</MenuItem>
                  <MenuItem value="hybrid">ハイブリッド</MenuItem>
                  <MenuItem value="electric">電気</MenuItem>
                </Select>
              </FormControl>
            </Box>
            
            <Box>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>装備</Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {equipmentOptions.map((eq) => (
                  <Chip
                    key={eq}
                    label={eq}
                    onClick={() => {
                      if (formData.equipment.includes(eq)) {
                        setFormData({
                          ...formData,
                          equipment: formData.equipment.filter(e => e !== eq)
                        });
                      } else {
                        setFormData({
                          ...formData,
                          equipment: [...formData.equipment, eq]
                        });
                      }
                    }}
                    color={formData.equipment.includes(eq) ? 'primary' : 'default'}
                    variant={formData.equipment.includes(eq) ? 'filled' : 'outlined'}
                  />
                ))}
              </Box>
            </Box>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>キャンセル</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingVehicle ? '更新' : '登録'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};