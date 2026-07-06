import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Auth/Login";
import Signup from "./pages/Auth/Signup";
import OnboardingPage from "./pages/Onboarding/OnboardingPage";
import AppLayout from "./pages/Layout/AppLayout";
import VocabPage from "./pages/Vocab/VocabPage";
import FlashcardPage from "./pages/Flashcard/FlashcardPage";
import SpeakingPage from "./pages/Speaking/SpeakingPage";
import GrammarPage from "./pages/Grammar/GrammarPage";
import RequireOnboarding from "./routes/RequireOnboarding";

function App(){
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/onboarding" element={<OnboardingPage />} />

        <Route element={<RequireOnboarding />}>
          <Route element={<AppLayout />}>
            <Route path="/vocab" element={<VocabPage />} />
            <Route path="/flashcard" element={<FlashcardPage />} />
            <Route path="/speaking" element={<SpeakingPage />} />
            <Route path="/grammar" element={<GrammarPage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
