// src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainPage from './pages/MainPage';
import WorkshopPage from './pages/WorkshopPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* The "index" or home route */}
        <Route path="/" element={<MainPage />} />
        
        {/* The route for your 3D editor */}
        <Route path="/workshop" element={<WorkshopPage />} />
      </Routes>
    </BrowserRouter>
  );
}