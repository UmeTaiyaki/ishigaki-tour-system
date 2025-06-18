// frontend/src/components/OptimizationMap.tsx
import React, { useEffect, useState } from 'react';
import { GoogleMap, LoadScript, Marker, Polyline, DirectionsRenderer } from '@react-google-maps/api';
import { Box, Paper, Typography, Chip } from '@mui/material';

interface Location {
  name: string;
  lat: number;
  lng: number;
}

interface RouteSegment {
  from_location: Location;
  to_location: Location;
  guest_id: string | null;
  arrival_time: string;
}

interface VehicleRoute {
  vehicle_id: string;
  vehicle_name: string;
  route_segments: RouteSegment[];
  total_distance_km: number;
  efficiency_score: number;
}

interface OptimizationMapProps {
  routes: VehicleRoute[];
  destination: Location;
  googleMapsApiKey?: string;
}

const containerStyle = {
  width: '100%',
  height: '600px'
};

const center = {
  lat: 24.3448,  // 石垣島の中心
  lng: 124.1572
};

// 車両ごとの色
const vehicleColors = [
  '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#DDA0DD',
  '#F4A460', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2'
];

export const OptimizationMap: React.FC<OptimizationMapProps> = ({ 
  routes, 
  destination,
  googleMapsApiKey 
}) => {
  const [map, setMap] = useState<google.maps.Map | null>(null);
  const [selectedRoute, setSelectedRoute] = useState<number | null>(null);
  const [directions, setDirections] = useState<google.maps.DirectionsResult[]>([]);

  useEffect(() => {
    if (map && routes.length > 0 && googleMapsApiKey) {
      // 各ルートのDirections APIを呼び出し
      const directionsService = new google.maps.DirectionsService();
      
      routes.forEach((route, index) => {
        const waypoints = route.route_segments
          .filter(seg => seg.guest_id !== null)
          .map(seg => ({
            location: new google.maps.LatLng(
              seg.from_location.lat, 
              seg.from_location.lng
            ),
            stopover: true
          }));

        const request: google.maps.DirectionsRequest = {
          origin: new google.maps.LatLng(
            route.route_segments[0].from_location.lat,
            route.route_segments[0].from_location.lng
          ),
          destination: new google.maps.LatLng(destination.lat, destination.lng),
          waypoints: waypoints,
          optimizeWaypoints: false,
          travelMode: google.maps.TravelMode.DRIVING
        };

        directionsService.route(request, (result, status) => {
          if (status === 'OK' && result) {
            setDirections(prev => {
              const newDirections = [...prev];
              newDirections[index] = result;
              return newDirections;
            });
          }
        });
      });

      // 地図の範囲を調整
      const bounds = new google.maps.LatLngBounds();
      routes.forEach(route => {
        route.route_segments.forEach(segment => {
          bounds.extend(new google.maps.LatLng(
            segment.from_location.lat,
            segment.from_location.lng
          ));
        });
      });
      bounds.extend(new google.maps.LatLng(destination.lat, destination.lng));
      map.fitBounds(bounds);
    }
  }, [map, routes, destination, googleMapsApiKey]);

  const onLoad = React.useCallback((map: google.maps.Map) => {
    setMap(map);
  }, []);

  const onUnmount = React.useCallback(() => {
    setMap(null);
  }, []);

  // Google Maps APIキーがない場合のフォールバック
  if (!googleMapsApiKey || googleMapsApiKey === 'your-google-maps-api-key') {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" gutterBottom>
          地図表示にはGoogle Maps APIキーが必要です
        </Typography>
        <Typography variant="body2" color="text.secondary">
          環境変数 REACT_APP_GOOGLE_MAPS_API_KEY を設定してください
        </Typography>
      </Paper>
    );
  }

  return (
    <Box>
      <LoadScript googleMapsApiKey={googleMapsApiKey}>
        <GoogleMap
          mapContainerStyle={containerStyle}
          center={center}
          zoom={11}
          onLoad={onLoad}
          onUnmount={onUnmount}
          options={{
            fullscreenControl: true,
            mapTypeControl: true,
            streetViewControl: false
          }}
        >
          {/* 目的地マーカー */}
          <Marker
            position={{ lat: destination.lat, lng: destination.lng }}
            icon={{
              url: 'http://maps.google.com/mapfiles/ms/icons/green-dot.png',
              scaledSize: new google.maps.Size(40, 40)
            }}
            title={destination.name}
          />

          {/* 各ルートの表示 */}
          {directions.map((direction, index) => (
            <DirectionsRenderer
              key={index}
              directions={direction}
              options={{
                polylineOptions: {
                  strokeColor: vehicleColors[index % vehicleColors.length],
                  strokeOpacity: selectedRoute === null || selectedRoute === index ? 1 : 0.3,
                  strokeWeight: selectedRoute === index ? 6 : 4
                },
                suppressMarkers: false,
                preserveViewport: true
              }}
            />
          ))}

          {/* ピックアップ地点のマーカー */}
          {routes.flatMap((route, routeIndex) => 
            route.route_segments
              .filter(seg => seg.guest_id !== null)
              .map((seg, segIndex) => (
                <Marker
                  key={`${routeIndex}-${segIndex}`}
                  position={{ lat: seg.from_location.lat, lng: seg.from_location.lng }}
                  icon={{
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 8,
                    fillColor: vehicleColors[routeIndex % vehicleColors.length],
                    fillOpacity: 0.8,
                    strokeColor: 'white',
                    strokeWeight: 2
                  }}
                  title={`${seg.from_location.name} - ${seg.arrival_time}`}
                />
              ))
          )}
        </GoogleMap>
      </LoadScript>

      {/* 凡例 */}
      <Paper sx={{ p: 2, mt: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          車両別ルート
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {routes.map((route, index) => (
            <Chip
              key={index}
              label={`${route.vehicle_name} (${route.total_distance_km.toFixed(1)}km)`}
              onClick={() => setSelectedRoute(selectedRoute === index ? null : index)}
              sx={{
                backgroundColor: vehicleColors[index % vehicleColors.length],
                color: 'white',
                opacity: selectedRoute === null || selectedRoute === index ? 1 : 0.5,
                '&:hover': {
                  opacity: 1
                }
              }}
            />
          ))}
        </Box>
      </Paper>
    </Box>
  );
};