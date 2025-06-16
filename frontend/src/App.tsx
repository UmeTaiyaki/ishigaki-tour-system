import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { TourListPage } from './pages/TourListPage';
import { OptimizationPage } from './pages/OptimizationPage';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
      '"Apple Color Emoji"',
      '"Segoe UI Emoji"',
      '"Segoe UI Symbol"',
      '"Noto Sans JP"',
    ].join(','),
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<Navigate to="/tours" replace />} />
          <Route path="/tours" element={<TourListPage />} />
          <Route path="/tours/:id/optimize" element={<OptimizationPage />} />
          {/* 今後追加するルート */}
          {/* <Route path="/tours/new" element={<TourCreatePage />} /> */}
          {/* <Route path="/tours/:id" element={<TourDetailPage />} /> */}
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;