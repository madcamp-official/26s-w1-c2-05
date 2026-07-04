import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Auth/Login";
import Signup from "./pages/Auth/Signup";
import OnboardingPage from "./pages/Onboarding/OnboardingPage";
import AppLayout from "./pages/Layout/AppLayout";
import VocabPage from "./pages/Vocab/VocabPage";
import FlashcardPage from "./pages/Flashcard/FlashcardPage";

function App(){
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/onboarding" element={<OnboardingPage />} />

        <Route element={<AppLayout />}>
          <Route path="/vocab" element={<VocabPage />} />
          <Route path="/flashcard" element={<FlashcardPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
