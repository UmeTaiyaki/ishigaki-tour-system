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
  CircularProgress
} from '@mui/material';
import { Grid2 } from '@mui/material';
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
      await loadGuests();
      resetForm();
    } catch (error: any) {
      console.error('Failed to save guest:', error);
      setError('ゲストの保存に失敗しました');
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('このゲストを削除しますか？\n関連するツアー予約も影響を受ける可能性があります。')) {
      try {
        await api.delete(`/guests/${id}`);
        await loadGuests();
      } catch (error: any) {
        console.error('Failed to delete guest:', error);
        setError('ゲストの削除に失敗しました');
      }
    }
  };

  const resetForm = () => {
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
    setEditingGuest(null);
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
            ゲスト管理
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setOpenDialog(true)}
          >
            新規ゲスト登録
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
                <TableCell>名前</TableCell>
                <TableCell>ホテル</TableCell>
                <TableCell align="center">大人/子供</TableCell>
                <TableCell>連絡先</TableCell>
                <TableCell>特記事項</TableCell>
                <TableCell align="center">アクション</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {guests.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    ゲストが登録されていません
                  </TableCell>
                </TableRow>
              ) : (
                guests.map((guest) => (
                  <TableRow key={guest.id} hover>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        <PersonIcon fontSize="small" color="action" />
                        {guest.name}
                      </Box>
                    </TableCell>
                    <TableCell>
                      {guest.hotel_name && (
                        <Box display="flex" alignItems="center" gap={1}>
                          <HotelIcon fontSize="small" color="action" />
                          {guest.hotel_name}
                        </Box>
                      )}
                    </TableCell>
                    <TableCell align="center">
                      {guest.num_adults}名 / {guest.num_children}名
                    </TableCell>
                    <TableCell>
                      {guest.phone && (
                        <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                          <PhoneIcon fontSize="small" color="action" />
                          {guest.phone}
                        </Box>
                      )}
                      {guest.email && (
                        <Box display="flex" alignItems="center" gap={1}>
                          <EmailIcon fontSize="small" color="action" />
                          {guest.email}
                        </Box>
                      )}
                    </TableCell>
                    <TableCell>
                      {guest.special_requirements?.map((req, idx) => (
                        <Chip
                          key={idx}
                          label={req}
                          size="small"
                          sx={{ mr: 0.5, mb: 0.5 }}
                        />
                      ))}
                    </TableCell>
                    <TableCell align="center">
                      <IconButton
                        size="small"
                        onClick={() => handleEdit(guest)}
                        title="編集"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(guest.id)}
                        title="削除"
                        color="error"
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

        {/* ゲスト登録・編集ダイアログ */}
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>
            {editingGuest ? 'ゲスト情報編集' : '新規ゲスト登録'}
          </DialogTitle>
          <DialogContent>
            <Grid2 container spacing={2} sx={{ mt: 1 }}>
              <Grid2 size={12}>
                <TextField
                  label="名前"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  fullWidth
                  required
                  autoFocus
                />
              </Grid2>
              
              <Grid2 size={12}>
                <TextField
                  label="ホテル名"
                  value={formData.hotel_name}
                  onChange={(e) => handleHotelSelect(e.target.value)}
                  fullWidth
                  select
                  SelectProps={{
                    native: true,
                  }}
                >
                  <option value="">ホテルを選択</option>
                  {hotelPresets.map((hotel) => (
                    <option key={hotel.name} value={hotel.name}>
                      {hotel.name}
                    </option>
                  ))}
                </TextField>
              </Grid2>
              
              <Grid2 size={6}>
                <TextField
                  label="大人"
                  type="number"
                  value={formData.num_adults}
                  onChange={(e) => setFormData({ ...formData, num_adults: parseInt(e.target.value) || 0 })}
                  fullWidth
                  InputProps={{ inputProps: { min: 0 } }}
                />
              </Grid2>
              
              <Grid2 size={6}>
                <TextField
                  label="子供"
                  type="number"
                  value={formData.num_children}
                  onChange={(e) => setFormData({ ...formData, num_children: parseInt(e.target.value) || 0 })}
                  fullWidth
                  InputProps={{ inputProps: { min: 0 } }}
                />
              </Grid2>
              
              <Grid2 size={12}>
                <TextField
                  label="電話番号"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  fullWidth
                  placeholder="090-1234-5678"
                />
              </Grid2>
              
              <Grid2 size={12}>
                <TextField
                  label="メールアドレス"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  fullWidth
                  placeholder="example@email.com"
                />
              </Grid2>
              
              <Grid2 size={12}>
                <TextField
                  label="特記事項"
                  value={formData.special_requirements.join(', ')}
                  onChange={(e) => setFormData({
                    ...formData,
                    special_requirements: e.target.value.split(',').map(req => req.trim())
                  })}
                  fullWidth
                  multiline
                  rows={2}
                  placeholder="車椅子利用, アレルギー等（カンマ区切り）"
                  helperText="複数の項目はカンマで区切って入力してください"
                />
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
              disabled={!formData.name || formData.num_adults + formData.num_children === 0}
            >
              {editingGuest ? '更新' : '登録'}
            </Button>
          </DialogActions>
        </Dialog>
      </Paper>
    </Container>
  );
};