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
  MenuItem
} from '@mui/material';
import { Grid2 } from '@mui/material';
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
      await loadVehicles();
      resetForm();
    } catch (error: any) {
      console.error('Failed to save vehicle:', error);
      setError('車両の保存に失敗しました');
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('この車両を削除しますか？\n進行中のツアーがある場合は削除できません。')) {
      try {
        await api.delete(`/vehicles/${id}`);
        await loadVehicles();
      } catch (error: any) {
        console.error('Failed to delete vehicle:', error);
        setError('車両の削除に失敗しました。使用中の可能性があります。');
      }
    }
  };

  const resetForm = () => {
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
    setEditingVehicle(null);
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

  const getTotalCapacity = (vehicle: Vehicle) => {
    return vehicle.capacity_adults + vehicle.capacity_children;
  };

  const getStatusChip = (status?: string) => {
    const statusOption = statusOptions.find(opt => opt.value === status);
    if (!statusOption) return null;
    
    return (
      <Chip
        label={statusOption.label}
        color={statusOption.color}
        size="small"
        icon={status === 'available' ? <ActiveIcon /> : status === 'maintenance' ? <InactiveIcon /> : undefined}
      />
    );
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
      <Paper sx={{ p: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h5" component="h1">
            車両管理
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setOpenDialog(true)}
          >
            新規車両登録
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>車両名</TableCell>
                <TableCell>タイプ</TableCell>
                <TableCell align="center">定員</TableCell>
                <TableCell>ドライバー</TableCell>
                <TableCell>装備</TableCell>
                <TableCell align="center">状態</TableCell>
                <TableCell align="center">アクション</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {vehicles.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    車両が登録されていません
                  </TableCell>
                </TableRow>
              ) : (
                vehicles.map((vehicle) => (
                  <TableRow key={vehicle.id} hover>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        <CarIcon fontSize="small" color="action" />
                        <Box>
                          <Typography variant="body2">{vehicle.name}</Typography>
                          {vehicle.license_plate && (
                            <Typography variant="caption" color="text.secondary">
                              {vehicle.license_plate}
                            </Typography>
                          )}
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      {vehicleTypes.find(vt => vt.value === vehicle.vehicle_type)?.label || vehicle.vehicle_type}
                    </TableCell>
                    <TableCell align="center">
                      <Typography variant="body2">
                        {getTotalCapacity(vehicle)}名
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        (大人{vehicle.capacity_adults}/子供{vehicle.capacity_children})
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {vehicle.driver_name && (
                        <>
                          <Box display="flex" alignItems="center" gap={1}>
                            <DriverIcon fontSize="small" color="action" />
                            {vehicle.driver_name}
                          </Box>
                          {vehicle.driver_phone && (
                            <Box display="flex" alignItems="center" gap={1} mt={0.5}>
                              <PhoneIcon fontSize="small" color="action" />
                              <Typography variant="caption">{vehicle.driver_phone}</Typography>
                            </Box>
                          )}
                        </>
                      )}
                    </TableCell>
                    <TableCell>
                      {vehicle.equipment?.map((eq, idx) => (
                        <Chip
                          key={idx}
                          label={eq}
                          size="small"
                          variant="outlined"
                          sx={{ mr: 0.5, mb: 0.5 }}
                        />
                      ))}
                    </TableCell>
                    <TableCell align="center">
                      {getStatusChip(vehicle.status)}
                    </TableCell>
                    <TableCell align="center">
                      <IconButton
                        size="small"
                        onClick={() => handleEdit(vehicle)}
                        title="編集"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(vehicle.id)}
                        title="削除"
                        color="error"
                        disabled={vehicle.status === 'in_use'}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* 車両登録・編集ダイアログ */}
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>
            {editingVehicle ? '車両情報編集' : '新規車両登録'}
          </DialogTitle>
          <DialogContent>
            <Grid2 container spacing={2} sx={{ mt: 1 }}>
              <Grid2 size={12}>
                <TextField
                  label="車両名"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  fullWidth
                  required
                  autoFocus
                  placeholder="例: ハイエース1号車"
                />
              </Grid2>
              
              <Grid2 size={6}>
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
              </Grid2>
              
              <Grid2 size={6}>
                <TextField
                  label="ナンバープレート"
                  value={formData.license_plate}
                  onChange={(e) => setFormData({ ...formData, license_plate: e.target.value })}
                  fullWidth
                  placeholder="例: 沖縄500 あ 12-34"
                />
              </Grid2>
              
              <Grid2 size={6}>
                <TextField
                  label="大人定員"
                  type="number"
                  value={formData.capacity_adults}
                  onChange={(e) => setFormData({ ...formData, capacity_adults: parseInt(e.target.value) || 0 })}
                  fullWidth
                  InputProps={{ inputProps: { min: 1 } }}
                />
              </Grid2>
              
              <Grid2 size={6}>
                <TextField
                  label="子供定員"
                  type="number"
                  value={formData.capacity_children}
                  onChange={(e) => setFormData({ ...formData, capacity_children: parseInt(e.target.value) || 0 })}
                  fullWidth
                  InputProps={{ inputProps: { min: 0 } }}
                />
              </Grid2>
              
              <Grid2 size={12}>
                <TextField
                  label="ドライバー名"
                  value={formData.driver_name}
                  onChange={(e) => setFormData({ ...formData, driver_name: e.target.value })}
                  fullWidth
                  placeholder="例: 山田太郎"
                />
              </Grid2>
              
              <Grid2 size={12}>
                <TextField
                  label="ドライバー電話番号"
                  value={formData.driver_phone}
                  onChange={(e) => setFormData({ ...formData, driver_phone: e.target.value })}
                  fullWidth
                  placeholder="090-1234-5678"
                />
              </Grid2>
              
              <Grid2 size={12}>
                <FormControl fullWidth>
                  <InputLabel>状態</InputLabel>
                  <Select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value as any })}
                    label="状態"
                  >
                    {statusOptions.map((status) => (
                      <MenuItem key={status.value} value={status.value}>
                        {status.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid2>
              
              <Grid2 size={12}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  装備（該当するものをチェック）
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={1}>
                  {equipmentOptions.map((equipment) => (
                    <Chip
                      key={equipment}
                      label={equipment}
                      onClick={() => {
                        const newEquipment = formData.equipment.includes(equipment)
                          ? formData.equipment.filter(eq => eq !== equipment)
                          : [...formData.equipment, equipment];
                        setFormData({ ...formData, equipment: newEquipment });
                      }}
                      color={formData.equipment.includes(equipment) ? 'primary' : 'default'}
                      variant={formData.equipment.includes(equipment) ? 'filled' : 'outlined'}
                      sx={{ cursor: 'pointer' }}
                    />
                  ))}
                </Box>
              </Grid2>
            </Grid2>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => {
              setOpenDialog(false);
              resetForm();
            }}>
              キャンセル
            </Button>
            <Button
              onClick={handleSubmit}
              variant="contained"
              disabled={!formData.name || formData.capacity_adults === 0}
            >
              {editingVehicle ? '更新' : '登録'}
            </Button>
          </DialogActions>
        </Dialog>
      </Paper>
    </Container>
  );
};