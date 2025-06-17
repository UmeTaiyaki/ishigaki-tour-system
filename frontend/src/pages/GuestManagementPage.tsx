// frontend/src/pages/GuestManagementPage.tsx
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
  Stack
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Person as PersonIcon,
  Hotel as HotelIcon,
  Phone as PhoneIcon,
  Email as EmailIcon
} from '@mui/icons-material';
import { api } from '../services/api';

interface Guest {
  id: string;
  name: string;
  hotel_name?: string;
  num_adults: number;
  num_children: number;
  phone?: string;
  email?: string;
  special_requirements: string[];
  pickup_lat?: number;
  pickup_lng?: number;
}

export const GuestManagementPage: React.FC = () => {
  const [guests, setGuests] = useState<Guest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingGuest, setEditingGuest] = useState<Guest | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    hotel_name: '',
    num_adults: 1,
    num_children: 0,
    phone: '',
    email: '',
    special_requirements: [] as string[],
    pickup_lat: 24.3448,
    pickup_lng: 124.1572
  });

  // ホテルのプリセットリスト（石垣島の主要ホテル）
  const hotelPresets = [
    { name: 'ANAインターコンチネンタル石垣リゾート', lat: 24.3969, lng: 124.1531 },
    { name: 'フサキビーチリゾート', lat: 24.3667, lng: 124.1389 },
    { name: 'グランヴィリオリゾート石垣島', lat: 24.4086, lng: 124.1639 },
    { name: 'アートホテル石垣島', lat: 24.3378, lng: 124.1561 },
    { name: '石垣島ビーチホテルサンシャイン', lat: 24.3722, lng: 124.1411 }
  ];

  useEffect(() => {
    loadGuests();
  }, []);

  const loadGuests = async () => {
    try {
      setLoading(true);
      const response = await api.get('/guests');
      setGuests(response.data);
      setError(null);
    } catch (err: any) {
      setError('ゲスト一覧の取得に失敗しました');
      console.error('Error loading guests:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      const payload = {
        ...formData,
        special_requirements: formData.special_requirements.filter(req => req.trim() !== '')
      };

      if (editingGuest) {
        await api.put(`/guests/${editingGuest.id}`, payload);
      } else {
        await api.post('/guests', payload);
      }

      setOpenDialog(false);
      resetForm();
      loadGuests();
    } catch (err: any) {
      setError(err.response?.data?.message || '保存に失敗しました');
      console.error('Error saving guest:', err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('このゲストを削除しますか？')) return;

    try {
      await api.delete(`/guests/${id}`);
      loadGuests();
    } catch (err: any) {
      setError('削除に失敗しました');
      console.error('Error deleting guest:', err);
    }
  };

  const handleEdit = (guest: Guest) => {
    setEditingGuest(guest);
    setFormData({
      name: guest.name,
      hotel_name: guest.hotel_name || '',
      num_adults: guest.num_adults,
      num_children: guest.num_children,
      phone: guest.phone || '',
      email: guest.email || '',
      special_requirements: guest.special_requirements || [],
      pickup_lat: guest.pickup_lat || 24.3448,
      pickup_lng: guest.pickup_lng || 124.1572
    });
    setOpenDialog(true);
  };

  const handleHotelSelect = (hotelName: string) => {
    const hotel = hotelPresets.find(h => h.name === hotelName);
    if (hotel) {
      setFormData({
        ...formData,
        hotel_name: hotel.name,
        pickup_lat: hotel.lat,
        pickup_lng: hotel.lng
      });
    }
  };

  const resetForm = () => {
    setEditingGuest(null);
    setFormData({
      name: '',
      hotel_name: '',
      num_adults: 1,
      num_children: 0,
      phone: '',
      email: '',
      special_requirements: [],
      pickup_lat: 24.3448,
      pickup_lng: 124.1572
    });
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
        <Typography variant="h4">ゲスト管理</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            resetForm();
            setOpenDialog(true);
          }}
        >
          新規ゲスト
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
              <TableCell>名前</TableCell>
              <TableCell>ホテル</TableCell>
              <TableCell align="center">大人</TableCell>
              <TableCell align="center">子供</TableCell>
              <TableCell>連絡先</TableCell>
              <TableCell>特記事項</TableCell>
              <TableCell align="center">操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {guests.map((guest) => (
              <TableRow key={guest.id}>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <PersonIcon fontSize="small" />
                    {guest.name}
                  </Box>
                </TableCell>
                <TableCell>
                  {guest.hotel_name && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <HotelIcon fontSize="small" />
                      {guest.hotel_name}
                    </Box>
                  )}
                </TableCell>
                <TableCell align="center">{guest.num_adults}</TableCell>
                <TableCell align="center">{guest.num_children}</TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                    {guest.phone && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <PhoneIcon fontSize="small" />
                        <Typography variant="body2">{guest.phone}</Typography>
                      </Box>
                    )}
                    {guest.email && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <EmailIcon fontSize="small" />
                        <Typography variant="body2">{guest.email}</Typography>
                      </Box>
                    )}
                  </Box>
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {guest.special_requirements?.map((req, index) => (
                      <Chip key={index} label={req} size="small" />
                    ))}
                  </Box>
                </TableCell>
                <TableCell align="center">
                  <IconButton onClick={() => handleEdit(guest)} size="small">
                    <EditIcon />
                  </IconButton>
                  <IconButton onClick={() => handleDelete(guest.id)} size="small" color="error">
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* ゲスト編集ダイアログ */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingGuest ? 'ゲスト編集' : '新規ゲスト登録'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              fullWidth
              label="名前"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
            
            <TextField
              fullWidth
              label="ホテル名"
              value={formData.hotel_name}
              onChange={(e) => {
                setFormData({ ...formData, hotel_name: e.target.value });
                handleHotelSelect(e.target.value);
              }}
              placeholder="ホテル名を入力"
            />
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                fullWidth
                type="number"
                label="大人の人数"
                value={formData.num_adults}
                onChange={(e) => setFormData({ ...formData, num_adults: parseInt(e.target.value) || 0 })}
                inputProps={{ min: 0 }}
              />
              
              <TextField
                fullWidth
                type="number"
                label="子供の人数"
                value={formData.num_children}
                onChange={(e) => setFormData({ ...formData, num_children: parseInt(e.target.value) || 0 })}
                inputProps={{ min: 0 }}
              />
            </Box>
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                fullWidth
                label="電話番号"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
              
              <TextField
                fullWidth
                label="メールアドレス"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                type="email"
              />
            </Box>
            
            <TextField
              fullWidth
              label="特記事項"
              value={formData.special_requirements.join(', ')}
              onChange={(e) => setFormData({ 
                ...formData, 
                special_requirements: e.target.value.split(',').map(s => s.trim()).filter(s => s)
              })}
              helperText="複数の場合はカンマで区切って入力"
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>キャンセル</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingGuest ? '更新' : '登録'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};