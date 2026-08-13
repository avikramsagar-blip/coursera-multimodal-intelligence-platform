import { BrowserRouter, Routes, Route } from "react-router-dom";
import Profile from "./pages/Profile";
import ProtectedRoute from "./components/ProtectedRoute";

import Login from "./pages/login";
import Register from "./pages/register";
import Dashboard from "./pages/dashboard";
import NotFound from "./pages/notfound";
import CourseDetails from "./pages/CourseDetails";
import AITutor from "./pages/AITutor";
import CreateCourse from "./pages/CreateCourse";

function App() {
  return (
    <BrowserRouter>
      <Routes>

        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
  path="/ai-tutor"
  element={
    <ProtectedRoute>
      <AITutor />
    </ProtectedRoute>
  }
/>

        <Route
          path="/course/:id"
          element={
            <ProtectedRoute>
              <CourseDetails />
            </ProtectedRoute>
          }
        />

        <Route
          path="/course/:id/ai"
          element={
            <ProtectedRoute>
              <AITutor />
            </ProtectedRoute>
          }
        />

        <Route
          path="/courses/new"
          element={
            <ProtectedRoute>
              <CreateCourse />
            </ProtectedRoute>
          }
        />
        <Route
  path="/profile"
  element={
    <ProtectedRoute>
      <Profile />
    </ProtectedRoute>
  }
/>

        <Route path="*" element={<NotFound />} />

      </Routes>
    </BrowserRouter>
  );
}

export default App;